"""Configuração central. Valores registrados para a reprodução dos experimentos."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")  # .env fica fora do git (ver .gitignore)

DADOS = RAIZ / "dados"
CONTEUDO = DADOS / "conteudo"
FRONTEND = RAIZ / "frontend"
LOGS = RAIZ / "logs"
PROMPTS = Path(__file__).resolve().parent / "prompts"

MODELO = os.getenv("QUAESTOR_MODELO", "claude-haiku-5-5")
# Só necessário se a chave NÃO pertencer a um workspace (o ideal é criar a chave dentro do workspace).
WORKSPACE_ID = os.getenv("ANTHROPIC_WORKSPACE_ID", "").strip()
ESFORCO_EXTRACAO = os.getenv("QUAESTOR_ESFORCO_EXTRACAO", "low")
ESFORCO_RESPOSTA = os.getenv("QUAESTOR_ESFORCO_RESPOSTA", "low")
MAX_TOKENS_EXTRACAO = 4000
MAX_TOKENS_RESPOSTA = 4000

RAG_K = int(os.getenv("QUAESTOR_RAG_K", "6"))
MAX_MENSAGEM = 1200          # caracteres por mensagem do usuário
MAX_HISTORICO = 20           # mensagens mantidas por sessão
SESSAO_TTL_MIN = 60          # sessões em memória expiram após inatividade

# Preço do Claude Haiku 5.5 (US$ por 1M tokens, prompts até 100K) — usado só para estimar custo nos logs.
PRECO_ENTRADA = 0.10
PRECO_SAIDA = 0.50
