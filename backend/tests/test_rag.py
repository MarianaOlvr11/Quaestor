import rag

# pergunta → trecho que deve aparecer entre os 3 primeiros (amostra; o conjunto completo fica nos experimentos)
CASOS = {
    "posso tirar meu dinheiro do tesouro selic antes?": "tesouro-selic#liquidez-e-resgate",
    "o que é liquidez": "liquidez#o-que-e-liquidez",
    "qual a diferença entre renda fixa e renda variável": "renda-fixa-x-renda-variavel#diferencas-entre-renda-fixa-e-renda-variavel",
    "quanto de imposto paga a LCI": "lci#tributacao",
    "quero comprar bitcoin": "fora-do-escopo#criptoativos-e-criptomoedas-no-quaestor",
    "cdb tem garantia do fgc?": "cdb#cobertura-do-fgc",
    "quanto guardar de reserva de emergencia": "reserva-emergencia#quanto-guardar",
}


def test_todos_os_documentos_indexados():
    docs = {t.doc for t in rag.indice().trechos}
    assert "metodologia-quaestor" in docs and len(docs) >= 30


def test_trechos_tem_titulo_e_url():
    for t in rag.indice().trechos:
        assert t.texto.startswith(t.titulo) and t.url.startswith("http")


def test_recall_amostra():
    acertos = sum(esperado in [t.id for t in rag.buscar(q, 3)] for q, esperado in CASOS.items())
    assert acertos == len(CASOS)


def test_filtro_por_documento():
    assert all(t.doc == "metodologia-quaestor" for t in rag.buscar("faixas de pontuação", 3, docs={"metodologia-quaestor"}))
