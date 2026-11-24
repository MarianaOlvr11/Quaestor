"""Fluxo de cada mensagem: extração (LLM) → regras (código) → busca (RAG) → resposta (LLM).

O LLM nunca decide perfil, carteira ou bloqueio: ele extrai os campos e explica o
resultado que o mecanismo de regras calculou.
"""
from __future__ import annotations

import time
import unicodedata
from dataclasses import dataclass, field

import config
import llm
import rag
import regras as R


@dataclass
class Sessao:
    id: str
    historico: list[dict] = field(default_factory=list)
    respostas: dict = field(default_factory=dict)
    atualizada: float = field(default_factory=time.time)


_SESSOES: dict[str, Sessao] = {}


def obter_sessao(sessao_id: str) -> Sessao:
    agora = time.time()
    for sid in [s for s, v in _SESSOES.items() if agora - v.atualizada > config.SESSAO_TTL_MIN * 60]:
        del _SESSOES[sid]
    s = _SESSOES.setdefault(sessao_id, Sessao(sessao_id))
    s.atualizada = agora
    return s


def _norm(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c)).strip()


def identificar_produto(pedido: str) -> str | None:
    """Associa o que o usuário escreveu a um produto do catálogo (ou None se estiver fora)."""
    p = _norm(pedido)
    for pid, prod in R.CATALOGO.items():
        if p == pid or p == _norm(prod["nome"]):
            return pid
    for pid, prod in R.CATALOGO.items():
        nome = _norm(prod["nome"])
        if p in nome or nome in p or pid.replace("-", " ") in p:
            return pid
    return None


def avaliar_pedidos(pedidos: list[str], perfil: str | None, respostas: dict) -> list[dict]:
    saida = []
    for pedido in pedidos:
        pid = identificar_produto(pedido)
        if pid is None:
            motivos = [R.MOTIVOS["fora_do_catalogo"]["mensagem"]]
        elif perfil is None:
            motivos = [R.MOTIVOS["informacoes_incompletas"]["mensagem"]]
        else:
            motivos = [m["mensagem"] for m in R.avaliar_produto(pid, perfil, respostas)]
        saida.append({
            "pedido": pedido,
            "produto": R.CATALOGO[pid]["nome"] if pid else pedido,
            "no_catalogo": pid is not None,
            "permitido": not motivos,
            "motivos": motivos,
        })
    return saida


def montar_estado(respostas: dict, ext, pedidos: list[dict]) -> tuple[dict, dict]:
    """Estado calculado pelas regras: vai para o LLM (explicar) e para a interface (mostrar)."""
    resultado = R.montar_carteira(respostas)
    cls = resultado["classificacao"]
    estado = {
        "campos_coletados": {R.CRITERIOS[c]["nome"]: R._opcao(c, v)["rotulo"] for c, v in respostas.items()},
        "campos_faltando": [R.CRITERIOS[c]["nome"] for c in cls.get("faltando", [])],
        "contradicao_a_esclarecer": ext.contradicao,
        "perfil": cls["perfil"],
    }
    if cls["perfil"]:
        estado.update({
            "pontos": cls["pontos"],
            "perfil_pela_soma_de_pontos": cls["perfil_pelos_pontos"],
            "travas_aplicadas": [f"{t['id']}: {t['motivo']}" for t in cls["travas_aplicadas"]],
            "carteira_simulada": [f"{i['produto']}: {i['pct']}%" for i in resultado["itens"]],
            "bloqueados_na_carteira": [f"{b['produto']}: {' '.join(b['motivos'])}" for b in resultado["bloqueados"]],
            "limite_renda_variavel": f"{resultado['renda_variavel_pct']}% de {resultado['limite_renda_variavel_pct']}% permitidos",
        })
    if pedidos:
        estado["pedidos_de_produto"] = pedidos
    if ext.pede_ignorar_regras:
        estado["pedido_para_ignorar_regras"] = R.MOTIVOS["pedido_ignorar_regras"]["mensagem"]
    return estado, resultado


def selecionar_trechos(consulta: str, ext, perfil: str | None, pedidos: list[dict]) -> list:
    trechos = rag.buscar(consulta, config.RAG_K)
    if perfil or ext.intencao in ("explicar_classificacao", "pedir_carteira") or pedidos or ext.pede_ignorar_regras:
        trechos += rag.buscar(f"{consulta} pontuação faixas travas bloqueio carteira", 2, docs={"metodologia-quaestor"})
    if any(not p["no_catalogo"] for p in pedidos):
        nomes = " ".join(p["pedido"] for p in pedidos if not p["no_catalogo"])
        trechos += rag.buscar(f"{nomes} fora do escopo catálogo", 2, docs={"fora-do-escopo"})
    unicos = {}
    for t in trechos:
        unicos.setdefault(t.id, t)
    return list(unicos.values())[:8]


def para_interface(texto: str, citados: list[str], respostas: dict, resultado: dict, pedidos: list[dict]) -> dict:
    """Formato que o frontend espera (ver contrato no início de frontend/app.js)."""
    citacoes, vistos = [], set()
    for tid in citados:
        t = rag.por_id(tid)
        if t and t.doc not in vistos:
            vistos.add(t.doc)
            citacoes.append({"titulo": t.titulo, "url": t.url})

    cls = resultado["classificacao"]
    carteira = None
    if cls["perfil"]:
        bloqueados = [{"produto": b["produto"], "motivo": " ".join(b["motivos"])} for b in resultado["bloqueados"]]
        bloqueados += [{"produto": p["produto"], "motivo": " ".join(p["motivos"])} for p in pedidos if not p["permitido"]]
        carteira = {
            "itens": [{
                "produto": i["produto"], "pct": i["pct"],
                "justificativa": f"Risco {i['risco']} de 5 · {R.CATALOGO[i['id']]['resgate']}.",
            } for i in resultado["itens"]],
            "bloqueados": bloqueados,
        }
    return {
        "reply": texto,
        "citations": citacoes,
        "perfil": {
            "campos": {c: (R._opcao(c, respostas[c])["rotulo"] if c in respostas else None) for c in R.CRITERIOS},
            "classificacao": cls["perfil"],
            "pontos": cls.get("pontos"),
        },
        "carteira": carteira,
    }


def processar(sessao: Sessao, mensagem: str) -> dict:
    sessao.historico.append({"role": "user", "content": mensagem})
    sessao.historico = sessao.historico[-config.MAX_HISTORICO:]
    if sessao.historico[0]["role"] != "user":   # a conversa enviada ao modelo deve começar pelo usuário
        sessao.historico = sessao.historico[1:]

    ext, uso_ext = llm.extrair(sessao.historico, sessao.respostas, sessao.id)
    for c in R.CRITERIOS:
        valor = getattr(ext, c)
        if valor is not None:
            sessao.respostas[c] = valor

    perfil = R.classificar(sessao.respostas)["perfil"]
    pedidos = avaliar_pedidos(ext.produtos_pedidos, perfil, sessao.respostas)
    estado, resultado = montar_estado(sessao.respostas, ext, pedidos)
    trechos = selecionar_trechos(f"{ext.consulta_busca} {mensagem}", ext, perfil, pedidos)

    texto, citados, uso_resp = llm.responder(sessao.historico, estado, trechos, sessao.id)
    sessao.historico.append({"role": "assistant", "content": texto})

    saida = para_interface(texto, citados, sessao.respostas, resultado, pedidos)
    saida["_debug"] = {  # usado pelos experimentos; a interface ignora
        "extracao": ext.model_dump(),
        "trechos": [t.id for t in trechos],
        "citados": citados,
        "uso": [uso_ext, uso_resp],
    }
    return saida
