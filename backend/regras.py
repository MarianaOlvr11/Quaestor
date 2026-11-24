"""Mecanismo de regras do Quaestor.

Tudo o que decide perfil, bloqueio e carteira vem de dados/regras.json e
dados/catalogo.json. O LLM só coleta as respostas e explica o resultado;
quem classifica e bloqueia é este módulo (código determinístico, testável).
"""
from __future__ import annotations

import json
from pathlib import Path

DADOS = Path(__file__).resolve().parent.parent / "dados"


def carregar(dados: Path = DADOS) -> tuple[dict, dict]:
    regras = json.loads((dados / "regras.json").read_text(encoding="utf-8"))
    catalogo = json.loads((dados / "catalogo.json").read_text(encoding="utf-8"))
    return regras, {p["id"]: p for p in catalogo["produtos"]}


REGRAS, CATALOGO = carregar()
ORDEM = REGRAS["ordem_perfis"]
CRITERIOS = {c["id"]: c for c in REGRAS["criterios"]}
MOTIVOS = {m["id"]: m for m in REGRAS["motivos_bloqueio"]}


def _opcao(criterio: str, valor: str) -> dict:
    for op in CRITERIOS[criterio]["opcoes"]:
        if op["valor"] == valor:
            return op
    raise ValueError(f"valor inválido para {criterio}: {valor!r}")


def campos_faltando(respostas: dict) -> list[str]:
    return [c for c in CRITERIOS if not respostas.get(c)]


def classificar(respostas: dict) -> dict:
    """Soma os pontos, aplica as travas e devolve o perfil com a explicação."""
    faltando = campos_faltando(respostas)
    if faltando:
        return {"perfil": None, "faltando": faltando, "motivo": MOTIVOS["informacoes_incompletas"]}

    detalhes = []
    for cid in CRITERIOS:
        op = _opcao(cid, respostas[cid])
        detalhes.append({"criterio": cid, "valor": op["valor"], "rotulo": op["rotulo"], "pontos": op["pontos"]})
    total = sum(d["pontos"] for d in detalhes)

    perfil_pontos = next(f["perfil"] for f in REGRAS["faixas"] if f["min"] <= total <= f["max"])
    perfil = perfil_pontos
    travas = []
    for t in REGRAS["travas"]:
        if respostas[t["campo"]] in t["valores"]:
            travas.append(t)
            if ORDEM.index(perfil) > ORDEM.index(t["perfil_maximo"]):
                perfil = t["perfil_maximo"]

    return {
        "perfil": perfil,
        "pontos": total,
        "perfil_pelos_pontos": perfil_pontos,
        "detalhes": detalhes,
        "travas_aplicadas": [{"id": t["id"], "perfil_maximo": t["perfil_maximo"], "motivo": t["motivo"]} for t in travas],
        "faltando": [],
    }


def avaliar_produto(produto_id: str, perfil: str, respostas: dict) -> list[dict]:
    """Lista os motivos de bloqueio do produto (lista vazia = permitido)."""
    prod = CATALOGO.get(produto_id)
    if prod is None:
        return [MOTIVOS["fora_do_catalogo"]]
    motivos = []
    if prod["risco"] > REGRAS["limites_perfil"][perfil]["risco_maximo"]:
        motivos.append(MOTIVOS["risco_acima_do_perfil"])
    horizonte_max = _opcao("horizonte", respostas["horizonte"])["meses_max"]
    if max(prod["carencia_meses"], prod["horizonte_recomendado_meses"]) > horizonte_max:
        motivos.append(MOTIVOS["horizonte_insuficiente"])
    if respostas["liquidez"] == "alta" and not prod["apto_reserva"]:
        motivos.append(MOTIVOS["liquidez_incompativel"])
    if respostas["objetivo"] == "reserva" and not prod["apto_reserva"]:
        motivos.append(MOTIVOS["nao_apto_reserva"])
    return motivos


def montar_carteira(respostas: dict) -> dict:
    """Parte da carteira modelo do perfil, bloqueia o que não serve e redistribui."""
    cls = classificar(respostas)
    if cls["perfil"] is None:
        return {"classificacao": cls, "itens": [], "bloqueados": []}

    perfil = cls["perfil"]
    chave = "reserva" if respostas["objetivo"] == "reserva" else perfil
    destino = REGRAS["destino_redistribuicao"]
    pesos: dict[str, int] = {}
    bloqueados = []
    for pid, pct in REGRAS["carteiras_modelo"][chave].items():
        motivos = avaliar_produto(pid, perfil, respostas)
        if motivos:
            bloqueados.append({"produto": CATALOGO[pid]["nome"], "id": pid, "pct_original": pct,
                               "motivos": [m["mensagem"] for m in motivos]})
            pesos[destino] = pesos.get(destino, 0) + pct
        else:
            pesos[pid] = pesos.get(pid, 0) + pct

    total = sum(pesos.values())
    rv = sum(p for pid, p in pesos.items() if CATALOGO[pid]["classe"] == "renda_variavel")
    limite_rv = REGRAS["limites_perfil"][perfil]["renda_variavel_max_pct"]
    assert total == 100, f"carteira soma {total}%"
    assert rv <= limite_rv, f"renda variável {rv}% acima do limite {limite_rv}%"

    itens = [{"id": pid, "produto": CATALOGO[pid]["nome"], "pct": pct, "risco": CATALOGO[pid]["risco"],
              "doc": CATALOGO[pid]["doc"]} for pid, pct in sorted(pesos.items(), key=lambda x: -x[1])]
    return {"classificacao": cls, "carteira_base": chave, "itens": itens, "bloqueados": bloqueados,
            "renda_variavel_pct": rv, "limite_renda_variavel_pct": limite_rv}


def validar_configuracao() -> list[str]:
    """Checa se regras.json e catalogo.json são coerentes entre si."""
    erros = []
    faixas = sorted(REGRAS["faixas"], key=lambda f: f["min"])
    minimo = sum(min(o["pontos"] for o in c["opcoes"]) for c in CRITERIOS.values())
    maximo = sum(max(o["pontos"] for o in c["opcoes"]) for c in CRITERIOS.values())
    if faixas[0]["min"] != minimo or faixas[-1]["max"] != maximo:
        erros.append(f"faixas não cobrem {minimo}..{maximo}")
    for a, b in zip(faixas, faixas[1:]):
        if b["min"] != a["max"] + 1:
            erros.append(f"faixas com buraco ou sobreposição entre {a['perfil']} e {b['perfil']}")
    for nome, cart in REGRAS["carteiras_modelo"].items():
        if sum(cart.values()) != 100:
            erros.append(f"carteira {nome} soma {sum(cart.values())}%")
        for pid in cart:
            if pid not in CATALOGO:
                erros.append(f"carteira {nome}: {pid} não está no catálogo")
        if nome in REGRAS["limites_perfil"]:
            lim = REGRAS["limites_perfil"][nome]
            for pid in cart:
                if pid in CATALOGO and CATALOGO[pid]["risco"] > lim["risco_maximo"]:
                    erros.append(f"carteira {nome}: {pid} tem risco acima do limite do perfil")
            rv = sum(p for pid, p in cart.items() if CATALOGO.get(pid, {}).get("classe") == "renda_variavel")
            if rv > lim["renda_variavel_max_pct"]:
                erros.append(f"carteira {nome}: renda variável {rv}% acima de {lim['renda_variavel_max_pct']}%")
    if REGRAS["destino_redistribuicao"] not in CATALOGO:
        erros.append("destino_redistribuicao fora do catálogo")
    return erros
