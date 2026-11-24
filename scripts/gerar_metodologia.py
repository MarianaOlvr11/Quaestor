"""Gera dados/conteudo/metodologia-quaestor.md a partir de dados/regras.json e dados/catalogo.json.

Rodar sempre que as regras mudarem:  python scripts/gerar_metodologia.py
Assim o texto que o RAG usa para explicar a classificação nunca diverge do código.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
import regras as R  # noqa: E402

SAIDA = RAIZ / "dados" / "conteudo" / "metodologia-quaestor.md"
PERFIL = {"conservador": "Conservador", "moderado": "Moderado", "arrojado": "Arrojado", "reserva": "Reserva de emergência"}
CLASSE = {"renda_fixa": "Renda fixa", "multimercado": "Multimercado", "renda_variavel": "Renda variável"}


def secao(titulo: str, *linhas: str) -> str:
    return f"## {titulo}\n\n" + "\n".join(linhas).strip() + "\n"


def exemplo(titulo: str, respostas: dict) -> str:
    m = R.montar_carteira(respostas)
    c = m["classificacao"]
    linhas = [f"Respostas de um investidor fictício e o resultado calculado pelo Quaestor:", ""]
    for d in c["detalhes"]:
        linhas.append(f"- {R.CRITERIOS[d['criterio']]['nome']}: {d['rotulo']} ({d['pontos']} ponto{'s' if d['pontos'] > 1 else ''}).")
    linhas += ["", f"A soma foi {c['pontos']} pontos, o que corresponde à faixa do perfil {c['perfil_pelos_pontos']}."]
    if c["travas_aplicadas"]:
        for t in c["travas_aplicadas"]:
            linhas.append(f"A trava \"{t['id']}\" limita o perfil a no máximo {t['perfil_maximo']}: {t['motivo']}")
    linhas.append(f"Perfil final: {c['perfil']}.")
    linhas += ["", "Carteira simulada resultante:", ""]
    linhas += [f"- {i['produto']}: {i['pct']}%." for i in m["itens"]]
    if m["bloqueados"]:
        linhas += ["", "Produtos da carteira modelo que foram bloqueados (o percentual foi para o Tesouro Selic):", ""]
        linhas += [f"- {b['produto']} ({b['pct_original']}%): {' '.join(b['motivos'])}" for b in m["bloqueados"]]
    return secao(titulo, *linhas)


def revisores_atuais() -> str:
    """Mantém o revisado_por já preenchido pelo grupo ao regenerar o arquivo."""
    if SAIDA.exists():
        for linha in SAIDA.read_text(encoding="utf-8").splitlines():
            if linha.startswith("revisado_por:"):
                return linha.split(":", 1)[1].strip()
    return "[]"


def gerar() -> str:
    erros = R.validar_configuracao()
    if erros:
        raise SystemExit("Configuração inconsistente:\n- " + "\n- ".join(erros))
    reg, base = R.REGRAS, R.REGRAS["base_normativa"]

    partes = [f"""---
id: metodologia-quaestor
titulo: Metodologia do Quaestor
fonte: [Projeto Quaestor, CVM]
url:
  - {base['url']}
acesso: '{base['acesso']}'
categoria: perfil
tags:
  - metodologia
  - classificacao
  - pontuacao
  - suitability
  - perfil
  - carteira
  - bloqueio
  - regras
revisado_por: {revisores_atuais()}
gerado_automaticamente: true
versao_regras: '{reg['versao']}'
---

<!-- Arquivo gerado por scripts/gerar_metodologia.py a partir de dados/regras.json e dados/catalogo.json. Não edite à mão. -->

# Metodologia do Quaestor
"""]

    partes.append(secao(
        "O que é a metodologia do Quaestor",
        "A metodologia do Quaestor é o conjunto de regras programadas que define o perfil de investidor, bloqueia produtos incompatíveis e monta a carteira simulada.",
        "",
        "No Quaestor, o modelo de linguagem conversa com o usuário e explica os resultados, mas quem calcula o perfil, decide os bloqueios e distribui os percentuais é o código, seguindo as regras descritas neste documento. Um pedido na conversa não altera essas regras.",
        "",
        "O Quaestor é uma ferramenta educacional: a classificação e a carteira são simulações e não constituem recomendação de investimento.",
    ))

    partes.append(secao(
        "Base normativa da metodologia do Quaestor",
        f"A metodologia do Quaestor se inspira na {base['norma']}, que trata da adequação dos investimentos ao perfil do cliente (suitability).",
        "",
        "- O art. 3º manda verificar os objetivos de investimento, a situação financeira e o conhecimento do cliente.",
        "- O art. 4º manda classificar o cliente em categorias de perfil de risco previamente estabelecidas.",
        "- O art. 5º manda classificar os produtos considerando riscos, perfil do emissor, garantias e prazos de carência.",
        "- O art. 6º proíbe recomendar produto inadequado ao perfil ou quando faltam informações para identificar o perfil.",
        "",
        "A resolução não define pontuações nem limites numéricos. As pontuações, faixas e limites do Quaestor são uma rubrica própria e simplificada do projeto, no formato de soma de pontos usado em questionários de perfil de investidor.",
    ))

    linhas = ["| Critério | O que o Quaestor pergunta | Base |", "|---|---|---|"]
    for c in reg["criterios"]:
        linhas.append(f"| {c['nome']} | {' / '.join(o['rotulo'] for o in c['opcoes'])} | {c['base']} |")
    partes.append(secao("Critérios avaliados pelo Quaestor",
                        "O Quaestor avalia seis critérios antes de classificar o perfil:", "", *linhas))

    linhas = ["Cada critério vale de 1 a 3 pontos no Quaestor. Quanto maior a pontuação, maior a disposição e a capacidade de assumir riscos.", ""]
    for c in reg["criterios"]:
        ops = "; ".join(f"{o['rotulo']} = {o['pontos']}" for o in c["opcoes"])
        linhas.append(f"- {c['nome']}: {ops}.")
    partes.append(secao("Pontuação de cada critério no Quaestor", *linhas))

    linhas = ["O Quaestor soma os pontos dos seis critérios e classifica o perfil pela faixa:", ""]
    linhas += [f"- {PERFIL[f['perfil']]}: de {f['min']} a {f['max']} pontos." for f in reg["faixas"]]
    linhas += ["", "Depois da soma, o Quaestor aplica as travas de segurança, que podem reduzir o perfil, mas nunca aumentá-lo."]
    partes.append(secao("Faixas de pontuação dos perfis no Quaestor", *linhas))

    linhas = ["As travas de segurança do Quaestor prevalecem sobre a soma de pontos:", ""]
    for t in reg["travas"]:
        rot = " ou ".join(R._opcao(t["campo"], v)["rotulo"] for v in t["valores"])
        linhas.append(f"- {R.CRITERIOS[t['campo']]['nome']} = {rot}: perfil no máximo {t['perfil_maximo']}. {t['motivo']}")
    linhas += ["", "Por isso, um investidor pode somar pontos de perfil moderado ou arrojado e mesmo assim ser classificado em um perfil mais conservador."]
    partes.append(secao("Travas de segurança do Quaestor", *linhas))

    linhas = ["O Quaestor classifica cada produto do catálogo em uma escala de risco de 1 a 5:", ""]
    linhas += [f"- Risco {k}: {v}." for k, v in reg["escala_risco"].items()]
    linhas += ["", "| Produto | Classe | Risco | Carência | Prazo recomendado | Garantia |", "|---|---|---|---|---|---|"]
    for p in R.CATALOGO.values():
        linhas.append(f"| {p['nome']} | {CLASSE[p['classe']]} | {p['risco']} | {p['carencia_meses']} meses | "
                      f"{p['horizonte_recomendado_meses']} meses | {p['garantia']} |")
    partes.append(secao("Classificação de risco dos produtos no Quaestor", *linhas))

    linhas = ["| Perfil | Risco máximo por produto | Renda variável na carteira |", "|---|---|---|"]
    for perf, lim in reg["limites_perfil"].items():
        linhas.append(f"| {PERFIL[perf]} | {lim['risco_maximo']} | até {lim['renda_variavel_max_pct']}% |")
    partes.append(secao("Limites da carteira por perfil no Quaestor",
                        "Cada perfil do Quaestor tem um risco máximo por produto e um limite de renda variável na carteira:", "", *linhas))

    linhas = ["O Quaestor parte de uma carteira modelo para cada perfil:", ""]
    for nome, cart in reg["carteiras_modelo"].items():
        itens = ", ".join(f"{R.CATALOGO[p]['nome']} {pct}%" for p, pct in cart.items())
        linhas.append(f"- {PERFIL[nome]}: {itens}.")
    linhas += ["", "Quando o objetivo informado é reserva de emergência, o Quaestor usa a carteira de reserva, só com produtos de liquidez diária e baixo risco."]
    partes.append(secao("Carteiras modelo do Quaestor", *linhas))

    linhas = ["O Quaestor bloqueia um produto e explica o motivo nas seguintes situações:", ""]
    linhas += [f"- {m['mensagem']} ({m['base']})" for m in reg["motivos_bloqueio"]]
    partes.append(secao("Por que o Quaestor bloqueia um produto", *linhas))

    partes.append(secao(
        "Como o Quaestor monta a carteira simulada",
        "1. Confere se os seis critérios foram respondidos. Se faltar algum, o Quaestor faz perguntas de esclarecimento e não monta carteira.",
        "2. Calcula o perfil pela soma de pontos e aplica as travas de segurança.",
        "3. Escolhe a carteira modelo do perfil, ou a carteira de reserva quando o objetivo é reserva de emergência.",
        "4. Verifica cada produto: risco, carência e prazo recomendado em relação ao horizonte, e necessidade de liquidez.",
        f"5. Bloqueia os produtos incompatíveis e transfere o percentual deles para o {R.CATALOGO[reg['destino_redistribuicao']]['nome']}.",
        "6. Confere se a carteira soma 100% e se a renda variável respeita o limite do perfil antes de exibir o resultado.",
    ))

    partes.append(exemplo("Exemplo de classificação moderada no Quaestor", dict(
        objetivo="objetivo_definido", horizonte="1_a_5_anos", experiencia="renda_fixa",
        liquidez="media", perdas="media", tolerancia="esperaria")))
    partes.append(exemplo("Exemplo de bloqueio por necessidade de liquidez no Quaestor", dict(
        objetivo="crescimento", horizonte="mais_de_5_anos", experiencia="renda_fixa",
        liquidez="alta", perdas="media", tolerancia="esperaria")))

    partes.append(secao(
        "Limitações da metodologia do Quaestor",
        "- A rubrica é uma simplificação em três perfis, feita para fins educacionais, e não reproduz o questionário de nenhuma instituição.",
        "- O catálogo usa tipos genéricos de produto, sem taxas, emissores ou rentabilidades reais.",
        "- A classificação de risco dos produtos é uma escolha do projeto, baseada nos fatores do art. 5º da Resolução CVM 30.",
        "- Os custos de cada produto (art. 3º, § 5º da Resolução CVM 30) não entram no cálculo da carteira.",
        "- As respostas são declaradas pelo usuário na conversa e podem estar incompletas ou imprecisas.",
    ))

    partes.append(secao(
        "Pontos de atenção",
        "- O perfil calculado pelo Quaestor pode ser diferente do perfil calculado por um banco ou corretora.",
        "- O usuário pode revisar suas respostas, e o perfil é recalculado.",
        "- Um pedido para ignorar as regras não libera produtos bloqueados.",
        "- A carteira simulada não é recomendação de investimento.",
    ))
    return "\n".join(partes)


if __name__ == "__main__":
    SAIDA.write_text(gerar(), encoding="utf-8")
    print(f"gerado: {SAIDA.relative_to(RAIZ)}")
