import regras as R

COMPLETO = dict(objetivo="objetivo_definido", horizonte="1_a_5_anos", experiencia="renda_fixa",
                liquidez="media", perdas="media", tolerancia="esperaria")


def test_configuracao_coerente():
    assert R.validar_configuracao() == []


def test_incompleto_nao_classifica():
    cls = R.classificar({"objetivo": "reserva"})
    assert cls["perfil"] is None
    assert set(cls["faltando"]) == {"horizonte", "experiencia", "liquidez", "perdas", "tolerancia"}


def test_soma_moderada():
    cls = R.classificar(COMPLETO)
    assert cls["pontos"] == 12 and cls["perfil"] == "moderado" and cls["travas_aplicadas"] == []


def test_trava_nunca_aumenta_o_perfil():
    resp = dict(COMPLETO, horizonte="ate_1_ano")
    cls = R.classificar(resp)
    assert cls["perfil_pelos_pontos"] == "moderado" and cls["perfil"] == "conservador"


def test_extremos():
    arrojado = dict(objetivo="crescimento", horizonte="mais_de_5_anos", experiencia="renda_variavel",
                    liquidez="baixa", perdas="alta", tolerancia="investiria_mais")
    assert R.classificar(arrojado)["perfil"] == "arrojado"
    assert R.classificar({k: c["opcoes"][0]["valor"] for k, c in R.CRITERIOS.items()})["perfil"] == "conservador"


def test_todas_as_combinacoes_geram_carteira_valida():
    """729 combinações: toda carteira soma 100% e respeita o limite de renda variável."""
    import itertools
    ids = list(R.CRITERIOS)
    for combo in itertools.product(*[[o["valor"] for o in R.CRITERIOS[c]["opcoes"]] for c in ids]):
        m = R.montar_carteira(dict(zip(ids, combo)))
        assert sum(i["pct"] for i in m["itens"]) == 100
        assert m["renda_variavel_pct"] <= m["limite_renda_variavel_pct"]
        perfil = m["classificacao"]["perfil"]
        assert all(R.CATALOGO[i["id"]]["risco"] <= R.REGRAS["limites_perfil"][perfil]["risco_maximo"] for i in m["itens"])


def test_bloqueios():
    assert R.avaliar_produto("bitcoin", "arrojado", COMPLETO)[0]["id"] == "fora_do_catalogo"
    assert any(m["id"] == "risco_acima_do_perfil" for m in R.avaliar_produto("acoes", "moderado", COMPLETO))
    curto = dict(COMPLETO, horizonte="ate_1_ano")
    assert any(m["id"] == "horizonte_insuficiente" for m in R.avaliar_produto("tesouro-ipca", "conservador", curto))
    assert R.avaliar_produto("tesouro-selic", "conservador", curto) == []
