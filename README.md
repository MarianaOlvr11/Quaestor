# Quaestor

Assistente educacional para identificar o perfil de investidor (conservador, moderado ou arrojado) e montar carteiras simuladas, usando o **Claude Haiku 5.5** (`claude-haiku-5-5`) com regras programadas e uma base de conteúdo revisada (RAG).

> Projeto acadêmico — IFSP Pirituba, TADS 6º semestre. Não é recomendação de investimento e não movimenta dinheiro real.

## Como funciona

Cada mensagem passa por quatro etapas (`backend/pipeline.py`):

1. **Extração (LLM)** — o Haiku lê a conversa e devolve, em JSON validado, os seis campos do perfil, os produtos pedidos, se o usuário pediu para ignorar as regras e uma consulta de busca.
2. **Regras (código)** — `backend/regras.py` soma os pontos, aplica as travas, monta a carteira e bloqueia produtos. Tudo vem de `dados/regras.json` e `dados/catalogo.json`. **O LLM não decide perfil, carteira nem bloqueio.**
3. **Busca (RAG)** — `backend/rag.py` divide os `.md` de `dados/conteudo/` por seção e busca com BM25 (determinístico, sem serviço externo).
4. **Resposta (LLM)** — o Haiku recebe os trechos como resultados de busca com citação e o estado calculado pelas regras, e explica o resultado. As fontes citadas aparecem na interface.

Se a API falhar, a interface mostra um aviso de erro — nunca uma resposta inventada.

## Estrutura

```
Quaestor/
├── frontend/              # interface web (HTML, CSS e JS puros)
├── backend/
│   ├── app.py             # FastAPI: POST /api/chat, GET /api/health e a interface
│   ├── pipeline.py        # extração → regras → busca → resposta
│   ├── llm.py             # chamadas ao Claude (extração estruturada e resposta com citações)
│   ├── rag.py             # índice BM25 da base de conteúdo
│   ├── regras.py          # mecanismo de regras (perfil, bloqueios, carteira)
│   ├── config.py          # modelo, esforço, limites (registrados para reprodução)
│   ├── prompts/           # prompt do sistema e de extração
│   └── tests/             # testes (rodam sem chave e sem custo)
├── dados/
│   ├── conteudo/          # base revisada (.md com fonte, URL e revisores)
│   ├── regras.json        # rubrica de perfil, travas, limites e carteiras modelo
│   └── catalogo.json      # produtos do simulador
├── scripts/
│   └── gerar_metodologia.py   # gera dados/conteudo/metodologia-quaestor.md a partir das regras
└── logs/                  # uso de tokens e custo por chamada (fora do git)
```

## Instalação

Requer Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r backend/requirements.txt
```

## Chave da API

1. No Console da Anthropic, use um workspace do projeto **com limite de gastos** e crie uma chave.
2. Copie `.env.example` para `.env` e preencha `ANTHROPIC_API_KEY`. O `.env` está no `.gitignore` e **nunca** deve ir para o GitHub.

A chave fica só no servidor; o navegador nunca a recebe.

## Rodar

```bash
cd backend
uvicorn app:app --reload --port 8000
```

Abra http://localhost:8000. Sem chave configurada, a interface abre normalmente e cada mensagem mostra o aviso "credencial da API não configurada".

Sem backend (só `python -m http.server 5173 --directory frontend`), a interface entra no **modo demonstração**, com respostas roteirizadas.

## Testes

```bash
cd backend
pytest -q
```

Os testes usam um LLM simulado: não precisam de chave e não geram custo. Cobrem as regras (incluindo as 729 combinações de respostas), a busca e o fluxo da API.

## Alterar as regras ou o catálogo

1. Edite `dados/regras.json` e/ou `dados/catalogo.json`.
2. Rode `python scripts/gerar_metodologia.py` (a partir da pasta `Quaestor`). O script para com erro se as regras ficarem inconsistentes e mantém os revisores do `.md`.
3. Rode os testes.

## Custos e registros

Cada chamada ao modelo é registrada em `logs/uso.jsonl` (tokens, latência, custo estimado, sem texto da conversa e com o id da sessão anonimizado). Preço usado na estimativa: US$ 0,10 / US$ 0,50 por 1M tokens de entrada/saída (Haiku 5.5, prompts até 100K).
