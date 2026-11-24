"""API do Quaestor (FastAPI). Serve a rota /api/chat e a interface em frontend/.

Rodar (dentro de backend/):  uvicorn app:app --reload
"""
from __future__ import annotations

import logging
import threading
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
import llm
import pipeline
import rag
import regras as R

log = logging.getLogger("quaestor")


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    erros = R.validar_configuracao()
    if erros:
        raise RuntimeError("regras.json/catalogo.json inconsistentes: " + "; ".join(erros))
    log.info("Quaestor: %d trechos indexados, modelo %s", len(rag.indice().trechos), config.MODELO)
    yield


app = FastAPI(title="Quaestor", version="0.1", lifespan=ciclo_de_vida)
_trava = threading.Lock()  # sessões ficam em memória; uma mensagem por vez por processo


class Pedido(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex, max_length=64)
    message: str = Field(min_length=1, max_length=config.MAX_MENSAGEM)


@app.get("/api/health")
def saude() -> dict:
    return {"ok": True, "modelo": config.MODELO, "trechos": len(rag.indice().trechos), "versao_regras": R.REGRAS["versao"]}


@app.post("/api/chat")
def chat(p: Pedido):
    with _trava:
        sessao = pipeline.obter_sessao(p.session_id)
        try:
            saida = pipeline.processar(sessao, p.message.strip())
        except llm.FalhaLLM as e:
            # desfaz a mensagem para o usuário poder tentar de novo, sem resposta inventada
            if sessao.historico and sessao.historico[-1]["role"] == "user":
                sessao.historico.pop()
            log.warning("falha no LLM: %s", e)
            return JSONResponse(status_code=503, content={"erro": str(e)})
    saida.pop("_debug", None)
    return saida


# A interface fica por último para não sobrepor as rotas /api.
app.mount("/", StaticFiles(directory=config.FRONTEND, html=True), name="frontend")
