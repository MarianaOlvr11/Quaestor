---
id: metodologia-quaestor
titulo: Metodologia do Quaestor
fonte: [Projeto Quaestor, CVM]
url:
  - https://conteudo.cvm.gov.br/legislacao/resolucoes/resol030.html
acesso: '2026-11-24'
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
revisado_por: [Mariana, Gustavo]
gerado_automaticamente: true
versao_regras: '0.1'
---

<!-- Arquivo gerado por scripts/gerar_metodologia.py a partir de dados/regras.json e dados/catalogo.json. Não edite à mão. -->

# Metodologia do Quaestor

## O que é a metodologia do Quaestor

A metodologia do Quaestor é o conjunto de regras programadas que define o perfil de investidor, bloqueia produtos incompatíveis e monta a carteira simulada.

No Quaestor, o modelo de linguagem conversa com o usuário e explica os resultados, mas quem calcula o perfil, decide os bloqueios e distribui os percentuais é o código, seguindo as regras descritas neste documento. Um pedido na conversa não altera essas regras.

O Quaestor é uma ferramenta educacional: a classificação e a carteira são simulações e não constituem recomendação de investimento.

## Base normativa da metodologia do Quaestor

A metodologia do Quaestor se inspira na Resolução CVM nº 30/2021 (texto consolidado), que trata da adequação dos investimentos ao perfil do cliente (suitability).

- O art. 3º manda verificar os objetivos de investimento, a situação financeira e o conhecimento do cliente.
- O art. 4º manda classificar o cliente em categorias de perfil de risco previamente estabelecidas.
- O art. 5º manda classificar os produtos considerando riscos, perfil do emissor, garantias e prazos de carência.
- O art. 6º proíbe recomendar produto inadequado ao perfil ou quando faltam informações para identificar o perfil.

A resolução não define pontuações nem limites numéricos. As pontuações, faixas e limites do Quaestor são uma rubrica própria e simplificada do projeto, no formato de soma de pontos usado em questionários de perfil de investidor.

## Critérios avaliados pelo Quaestor

O Quaestor avalia seis critérios antes de classificar o perfil:

| Critério | O que o Quaestor pergunta | Base |
|---|---|---|
| Objetivo do investimento | reserva de emergência ou uso no curto prazo / objetivo definido (imóvel, estudo, viagem, carro) / crescimento do patrimônio ou aposentadoria | Res. CVM 30, art. 3º, § 1º, III (finalidades do investimento) |
| Horizonte de investimento | até 1 ano / de 1 a 5 anos / mais de 5 anos | Res. CVM 30, art. 3º, § 1º, I (período em que deseja manter o investimento) |
| Experiência com investimentos | nunca investiu ou só poupança / já investiu em renda fixa / já investiu em renda variável | Res. CVM 30, art. 3º, § 3º, I e II (produtos com que tem familiaridade e operações já realizadas) |
| Necessidade de liquidez | pode precisar do dinheiro a qualquer momento / pode precisar de parte do dinheiro / não deve precisar do dinheiro no período | Res. CVM 30, art. 3º, § 2º, III (necessidade futura de recursos) |
| Capacidade de suportar perdas | uma perda afetaria despesas essenciais / uma perda incomodaria, mas não afetaria o essencial / uma perda temporária não afetaria a vida financeira | Res. CVM 30, art. 3º, § 2º, I e II (receitas regulares e patrimônio) |
| Tolerância ao risco | diante de uma queda de 15%, resgataria tudo / diante de uma queda de 15%, esperaria a recuperação / diante de uma queda de 15%, investiria mais | Res. CVM 30, art. 3º, § 1º, II (preferências declaradas quanto à assunção de riscos) |

## Pontuação de cada critério no Quaestor

Cada critério vale de 1 a 3 pontos no Quaestor. Quanto maior a pontuação, maior a disposição e a capacidade de assumir riscos.

- Objetivo do investimento: reserva de emergência ou uso no curto prazo = 1; objetivo definido (imóvel, estudo, viagem, carro) = 2; crescimento do patrimônio ou aposentadoria = 3.
- Horizonte de investimento: até 1 ano = 1; de 1 a 5 anos = 2; mais de 5 anos = 3.
- Experiência com investimentos: nunca investiu ou só poupança = 1; já investiu em renda fixa = 2; já investiu em renda variável = 3.
- Necessidade de liquidez: pode precisar do dinheiro a qualquer momento = 1; pode precisar de parte do dinheiro = 2; não deve precisar do dinheiro no período = 3.
- Capacidade de suportar perdas: uma perda afetaria despesas essenciais = 1; uma perda incomodaria, mas não afetaria o essencial = 2; uma perda temporária não afetaria a vida financeira = 3.
- Tolerância ao risco: diante de uma queda de 15%, resgataria tudo = 1; diante de uma queda de 15%, esperaria a recuperação = 2; diante de uma queda de 15%, investiria mais = 3.

## Faixas de pontuação dos perfis no Quaestor

O Quaestor soma os pontos dos seis critérios e classifica o perfil pela faixa:

- Conservador: de 6 a 10 pontos.
- Moderado: de 11 a 14 pontos.
- Arrojado: de 15 a 18 pontos.

Depois da soma, o Quaestor aplica as travas de segurança, que podem reduzir o perfil, mas nunca aumentá-lo.

## Travas de segurança do Quaestor

As travas de segurança do Quaestor prevalecem sobre a soma de pontos:

- Horizonte de investimento = até 1 ano: perfil no máximo conservador. Com horizonte de até 1 ano, não há tempo para recuperar eventuais quedas de investimentos mais arriscados.
- Necessidade de liquidez = pode precisar do dinheiro a qualquer momento: perfil no máximo conservador. Quem pode precisar do dinheiro a qualquer momento não deve depender de investimentos que oscilam ou têm carência.
- Objetivo do investimento = reserva de emergência ou uso no curto prazo: perfil no máximo conservador. A reserva de emergência deve priorizar baixo risco e alta liquidez, não rentabilidade.
- Capacidade de suportar perdas = uma perda afetaria despesas essenciais: perfil no máximo moderado. Quando uma perda afetaria despesas essenciais, o perfil arrojado não é adequado, mesmo com alta tolerância ao risco.
- Experiência com investimentos = nunca investiu ou só poupança: perfil no máximo moderado. Sem experiência prévia, o perfil arrojado exigiria conhecimento que o investidor ainda não declarou ter (art. 3º, III).

Por isso, um investidor pode somar pontos de perfil moderado ou arrojado e mesmo assim ser classificado em um perfil mais conservador.

## Classificação de risco dos produtos no Quaestor

O Quaestor classifica cada produto do catálogo em uma escala de risco de 1 a 5:

- Risco 1: muito baixo: liquidez diária, baixa oscilação e garantia do Tesouro Nacional ou do FGC.
- Risco 2: baixo: renda fixa com carência, pequena oscilação ou sem cobertura do FGC.
- Risco 3: médio: oscilação relevante de preço (marcação a mercado) ou estratégias mistas.
- Risco 4: alto: renda variável diversificada ou crédito privado sem garantia.
- Risco 5: muito alto: renda variável concentrada em empresas individuais.

| Produto | Classe | Risco | Carência | Prazo recomendado | Garantia |
|---|---|---|---|---|---|
| Tesouro Selic | Renda fixa | 1 | 0 meses | 0 meses | Tesouro Nacional |
| Poupança | Renda fixa | 1 | 0 meses | 0 meses | FGC |
| CDB com liquidez diária | Renda fixa | 1 | 0 meses | 0 meses | FGC |
| LCI | Renda fixa | 2 | 6 meses | 6 meses | FGC |
| LCA | Renda fixa | 2 | 6 meses | 6 meses | FGC |
| Fundo de renda fixa simples | Renda fixa | 2 | 0 meses | 6 meses | nenhuma |
| Tesouro Prefixado | Renda fixa | 2 | 0 meses | 12 meses | Tesouro Nacional |
| Tesouro IPCA+ | Renda fixa | 3 | 0 meses | 36 meses | Tesouro Nacional |
| Debêntures | Renda fixa | 4 | 0 meses | 36 meses | nenhuma |
| Fundo multimercado | Multimercado | 3 | 0 meses | 24 meses | nenhuma |
| ETF de ações (índice amplo) | Renda variável | 4 | 0 meses | 60 meses | nenhuma |
| Fundo imobiliário (FII) | Renda variável | 4 | 0 meses | 36 meses | nenhuma |
| Ações individuais | Renda variável | 5 | 0 meses | 60 meses | nenhuma |

## Limites da carteira por perfil no Quaestor

Cada perfil do Quaestor tem um risco máximo por produto e um limite de renda variável na carteira:

| Perfil | Risco máximo por produto | Renda variável na carteira |
|---|---|---|
| Conservador | 2 | até 0% |
| Moderado | 4 | até 30% |
| Arrojado | 5 | até 70% |

## Carteiras modelo do Quaestor

O Quaestor parte de uma carteira modelo para cada perfil:

- Reserva de emergência: Tesouro Selic 60%, CDB com liquidez diária 40%.
- Conservador: Tesouro Selic 40%, CDB com liquidez diária 25%, LCI 15%, LCA 10%, Tesouro Prefixado 10%.
- Moderado: Tesouro Selic 25%, CDB com liquidez diária 10%, Tesouro IPCA+ 25%, LCA 10%, Fundo multimercado 15%, ETF de ações (índice amplo) 15%.
- Arrojado: Tesouro Selic 10%, Tesouro IPCA+ 20%, Fundo multimercado 15%, ETF de ações (índice amplo) 25%, Fundo imobiliário (FII) 15%, Ações individuais 15%.

Quando o objetivo informado é reserva de emergência, o Quaestor usa a carteira de reserva, só com produtos de liquidez diária e baixo risco.

## Por que o Quaestor bloqueia um produto

O Quaestor bloqueia um produto e explica o motivo nas seguintes situações:

- Ainda faltam informações para identificar seu perfil. Sem elas, o Quaestor não monta carteira nem indica produtos (Res. CVM 30, art. 6º, II). (Res. CVM 30, art. 6º, II)
- O risco deste produto é maior que o permitido para o seu perfil. (Res. CVM 30, art. 6º, I)
- O prazo de carência ou o horizonte recomendado deste produto é maior que o seu horizonte de investimento. (Res. CVM 30, art. 5º, IV (prazos de carência))
- Você indicou que pode precisar do dinheiro a qualquer momento, e este produto tem carência ou oscila de preço. (Res. CVM 30, art. 3º, § 2º, III (necessidade futura de recursos))
- Para reserva de emergência, o Quaestor só usa produtos de liquidez diária e baixo risco. (Base de conteúdo: reserva-emergencia)
- A carteira já atingiu o limite de renda variável do seu perfil. (Regra própria do Quaestor)
- Este produto não faz parte do catálogo revisado do simulador. (Regra própria do Quaestor)
- As regras de adequação não podem ser desativadas pela conversa. Se suas informações mudaram, você pode revisar suas respostas e o perfil será recalculado. (Regra própria do Quaestor)

## Como o Quaestor monta a carteira simulada

1. Confere se os seis critérios foram respondidos. Se faltar algum, o Quaestor faz perguntas de esclarecimento e não monta carteira.
2. Calcula o perfil pela soma de pontos e aplica as travas de segurança.
3. Escolhe a carteira modelo do perfil, ou a carteira de reserva quando o objetivo é reserva de emergência.
4. Verifica cada produto: risco, carência e prazo recomendado em relação ao horizonte, e necessidade de liquidez.
5. Bloqueia os produtos incompatíveis e transfere o percentual deles para o Tesouro Selic.
6. Confere se a carteira soma 100% e se a renda variável respeita o limite do perfil antes de exibir o resultado.

## Exemplo de classificação moderada no Quaestor

Respostas de um investidor fictício e o resultado calculado pelo Quaestor:

- Objetivo do investimento: objetivo definido (imóvel, estudo, viagem, carro) (2 pontos).
- Horizonte de investimento: de 1 a 5 anos (2 pontos).
- Experiência com investimentos: já investiu em renda fixa (2 pontos).
- Necessidade de liquidez: pode precisar de parte do dinheiro (2 pontos).
- Capacidade de suportar perdas: uma perda incomodaria, mas não afetaria o essencial (2 pontos).
- Tolerância ao risco: diante de uma queda de 15%, esperaria a recuperação (2 pontos).

A soma foi 12 pontos, o que corresponde à faixa do perfil moderado.
Perfil final: moderado.

Carteira simulada resultante:

- Tesouro Selic: 25%.
- Tesouro IPCA+: 25%.
- Fundo multimercado: 15%.
- ETF de ações (índice amplo): 15%.
- CDB com liquidez diária: 10%.
- LCA: 10%.

## Exemplo de bloqueio por necessidade de liquidez no Quaestor

Respostas de um investidor fictício e o resultado calculado pelo Quaestor:

- Objetivo do investimento: crescimento do patrimônio ou aposentadoria (3 pontos).
- Horizonte de investimento: mais de 5 anos (3 pontos).
- Experiência com investimentos: já investiu em renda fixa (2 pontos).
- Necessidade de liquidez: pode precisar do dinheiro a qualquer momento (1 ponto).
- Capacidade de suportar perdas: uma perda incomodaria, mas não afetaria o essencial (2 pontos).
- Tolerância ao risco: diante de uma queda de 15%, esperaria a recuperação (2 pontos).

A soma foi 13 pontos, o que corresponde à faixa do perfil moderado.
A trava "liquidez_alta" limita o perfil a no máximo conservador: Quem pode precisar do dinheiro a qualquer momento não deve depender de investimentos que oscilam ou têm carência.
Perfil final: conservador.

Carteira simulada resultante:

- Tesouro Selic: 75%.
- CDB com liquidez diária: 25%.

Produtos da carteira modelo que foram bloqueados (o percentual foi para o Tesouro Selic):

- LCI (15%): Você indicou que pode precisar do dinheiro a qualquer momento, e este produto tem carência ou oscila de preço.
- LCA (10%): Você indicou que pode precisar do dinheiro a qualquer momento, e este produto tem carência ou oscila de preço.
- Tesouro Prefixado (10%): Você indicou que pode precisar do dinheiro a qualquer momento, e este produto tem carência ou oscila de preço.

## Limitações da metodologia do Quaestor

- A rubrica é uma simplificação em três perfis, feita para fins educacionais, e não reproduz o questionário de nenhuma instituição.
- O catálogo usa tipos genéricos de produto, sem taxas, emissores ou rentabilidades reais.
- A classificação de risco dos produtos é uma escolha do projeto, baseada nos fatores do art. 5º da Resolução CVM 30.
- Os custos de cada produto (art. 3º, § 5º da Resolução CVM 30) não entram no cálculo da carteira.
- As respostas são declaradas pelo usuário na conversa e podem estar incompletas ou imprecisas.

## Pontos de atenção

- O perfil calculado pelo Quaestor pode ser diferente do perfil calculado por um banco ou corretora.
- O usuário pode revisar suas respostas, e o perfil é recalculado.
- Um pedido para ignorar as regras não libera produtos bloqueados.
- A carteira simulada não é recomendação de investimento.
