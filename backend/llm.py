"""Chamadas ao Claude Haiku 5.5: extração estruturada e resposta com citações."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Literal, Optional

import anthropic
from pydantic import BaseModel, Field, create_model

import config
import regras as R

log = logging.getLogger("quaestor")
_cliente: anthropic.Anthropic | None = None


def cliente() -> anthropic.Anthropic:
    """Usa ANTHROPIC_API_KEY (ou outra credencial do ambiente). A chave nunca vai para o frontend."""
    global _cliente
    if _cliente is None:
        cabecalhos = {}
        # chaves que não pertencem a um workspace exigem o id do workspace em cada pedido
        if config.WORKSPACE_ID:
            cabecalhos["anthropic-workspace-id"] = config.WORKSPACE_ID
        _cliente = anthropic.Anthropic(max_retries=2, timeout=60.0, default_headers=cabecalhos or None)
    return _cliente


class FalhaLLM(Exception):
    """Erro ao falar com o modelo. A interface mostra uma mensagem de falha, nunca uma resposta inventada."""


# ---------- extração estruturada ----------

def _modelo_extracao() -> type[BaseModel]:
    campos = {}
    for c in R.REGRAS["criterios"]:
        valores = tuple(o["valor"] for o in c["opcoes"])
        campos[c["id"]] = (Optional[Literal[valores]], Field(default=None, description=c["nome"]))  # type: ignore[valid-type]
    campos["intencao"] = (
        Literal["responder_perfil", "duvida_conceito", "pedir_carteira", "pedir_produto", "explicar_classificacao", "outro"],
        Field(description="O que o usuário quer com a última mensagem"),
    )
    campos["produtos_pedidos"] = (list[str], Field(default_factory=list))
    campos["pede_ignorar_regras"] = (bool, False)
    campos["contradicao"] = (Optional[str], None)
    campos["consulta_busca"] = (str, Field(description="Busca curta com termos da área financeira"))
    return create_model("Extracao", **campos)


Extracao = _modelo_extracao()


def _prompt_extracao() -> str:
    linhas = []
    for c in R.REGRAS["criterios"]:
        ops = "; ".join(f'"{o["valor"]}" = {o["rotulo"]}' for o in c["opcoes"])
        linhas.append(f'- {c["id"]} ({c["nome"]}): {ops}')
    catalogo = "\n".join(f"- {p['id']}: {p['nome']}" for p in R.CATALOGO.values())
    modelo = (config.PROMPTS / "extracao.md").read_text(encoding="utf-8")
    return modelo.replace("{criterios}", "\n".join(linhas)).replace("{catalogo}", catalogo)


PROMPT_EXTRACAO = _prompt_extracao()
PROMPT_SISTEMA = (config.PROMPTS / "sistema.md").read_text(encoding="utf-8")


def _registrar(etapa: str, sessao: str, resp, inicio: float, extra: dict | None = None) -> dict:
    u = resp.usage
    uso = {
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sessao": hashlib.sha256(sessao.encode()).hexdigest()[:12],  # sem dados pessoais
        "etapa": etapa,
        "modelo": resp.model,
        "stop_reason": resp.stop_reason,
        "tokens_entrada": u.input_tokens,
        "tokens_saida": u.output_tokens,
        "latencia_s": round(time.perf_counter() - inicio, 2),
        "custo_usd": round((u.input_tokens * config.PRECO_ENTRADA + u.output_tokens * config.PRECO_SAIDA) / 1e6, 6),
        **(extra or {}),
    }
    config.LOGS.mkdir(exist_ok=True)
    with open(config.LOGS / "uso.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(uso, ensure_ascii=False) + "\n")
    return uso


def _chamar(fn, **kwargs):
    try:
        return fn(**kwargs)
    except anthropic.AuthenticationError as e:
        raise FalhaLLM("credencial da API ausente ou inválida") from e
    except anthropic.RateLimitError as e:
        raise FalhaLLM("limite de requisições atingido") from e
    except anthropic.APIConnectionError as e:
        raise FalhaLLM("sem conexão com a API") from e
    except anthropic.APIStatusError as e:
        log.warning("API %s: %s (request_id=%s)", e.status_code, e.message, getattr(e, "request_id", None))
        raise FalhaLLM(f"erro da API ({e.status_code})") from e
    except TypeError as e:
        # o SDK lança TypeError quando não encontra nenhuma credencial no ambiente
        if "authentication" in str(e).lower():
            raise FalhaLLM("credencial da API não configurada no servidor") from e
        raise


def extrair(historico: list[dict], respostas: dict, sessao: str) -> tuple[BaseModel, dict]:
    conversa = "\n".join(f"{'Usuário' if m['role'] == 'user' else 'Quaestor'}: {m['content']}" for m in historico)
    conteudo = (
        f"<valores_registrados>\n{json.dumps(respostas, ensure_ascii=False)}\n</valores_registrados>\n\n"
        f"<conversa>\n{conversa}\n</conversa>"
    )
    inicio = time.perf_counter()
    resp = _chamar(
        cliente().messages.parse,
        model=config.MODELO,
        max_tokens=config.MAX_TOKENS_EXTRACAO,
        system=PROMPT_EXTRACAO,
        messages=[{"role": "user", "content": conteudo}],
        output_format=Extracao,
        output_config={"effort": config.ESFORCO_EXTRACAO},
    )
    uso = _registrar("extracao", sessao, resp, inicio)
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise FalhaLLM(f"extração não concluída ({resp.stop_reason})")
    return resp.parsed_output, uso


# ---------- resposta com citações ----------

def responder(historico: list[dict], estado: dict, trechos: list, sessao: str) -> tuple[str, list[str], dict]:
    """Gera a resposta final. Devolve (texto, ids dos trechos citados, uso)."""
    resultados = [
        {
            "type": "search_result",
            "source": t.id,
            "title": f"{t.titulo} — {t.secao}",
            "content": [{"type": "text", "text": t.texto}],
            "citations": {"enabled": True},
        }
        for t in trechos
    ]
    ultima = historico[-1]["content"]
    mensagens = [{"role": m["role"], "content": m["content"]} for m in historico[:-1]]
    mensagens.append({
        "role": "user",
        "content": resultados + [{
            "type": "text",
            "text": (
                f"<estado_do_sistema>\n{json.dumps(estado, ensure_ascii=False, indent=1)}\n</estado_do_sistema>\n\n"
                f"<mensagem_do_usuario>\n{ultima}\n</mensagem_do_usuario>"
            ),
        }],
    })
    inicio = time.perf_counter()
    resp = _chamar(
        cliente().messages.create,
        model=config.MODELO,
        max_tokens=config.MAX_TOKENS_RESPOSTA,
        system=PROMPT_SISTEMA,
        messages=mensagens,
        output_config={"effort": config.ESFORCO_RESPOSTA},
    )
    if resp.stop_reason == "refusal":
        _registrar("resposta", sessao, resp, inicio)
        raise FalhaLLM("o modelo recusou a resposta")

    partes, citados = [], []
    for bloco in resp.content:
        if bloco.type != "text":
            continue
        partes.append(bloco.text)
        for c in getattr(bloco, "citations", None) or []:
            src = getattr(c, "source", None)
            if src and src not in citados:
                citados.append(src)
    uso = _registrar("resposta", sessao, resp, inicio, {"trechos_enviados": len(trechos), "trechos_citados": len(citados)})
    return "".join(partes).strip(), citados, uso
