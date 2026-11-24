"""Busca na base de conteúdo revisada (RAG) com BM25.

Cada arquivo .md de dados/conteudo é dividido pelas seções "## ". Cada trecho recebe o
título do documento junto ("Tesouro IPCA+ — Tributação"), para que seções com o mesmo
nome em documentos diferentes não fiquem ambíguas. BM25 é determinístico e não depende
de serviço externo, o que facilita reproduzir os experimentos.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from config import CONTEUDO

STOPWORDS = set("""
a o as os um uma uns umas de do da dos das no na nos nas em por para pra com sem sob sobre
e ou mas que se ao aos à às é ser são foi era como mais menos muito muita muitos muitas
eu tu ele ela nos vos eles elas meu minha meus minhas seu sua seus suas esse essa isso
este esta isto aquele aquela aquilo qual quais quando onde porque pois já não sim também
ter tem têm tinha há quero queria posso pode podem devo deve the of
""".split())


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


# palavras que um iniciante usa → termo que aparece na base (já como radical)
SINONIMOS = {
    "tirar": "resgat", "sacar": "resgat", "retirar": "resgat", "resgatar": "resgat",
    "imposto": "tribut", "impostos": "tribut", "ir": "tribut",
    "bitcoin": "cripto", "btc": "cripto", "ethereum": "cripto",
    "rende": "rentab", "rendimento": "rentab", "lucro": "rentab",
    "perder": "perda", "prejuizo": "perda",
}


def _radical(tk: str) -> str:
    # radical bem simples: tira plural e terminações comuns e corta em 6 letras
    for suf in ("mente", "coes", "cao", "oes", "ais", "eis", "es", "s"):
        if len(tk) > len(suf) + 3 and tk.endswith(suf):
            tk = tk[: -len(suf)]
            break
    return tk[:6]


def tokenizar(texto: str, consulta: bool = False) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", _sem_acento(texto.lower()))
    out = []
    for tk in tokens:
        if consulta and tk in SINONIMOS:
            out.append(SINONIMOS[tk])
        if tk in STOPWORDS or len(tk) < 2:
            continue
        out.append(_radical(tk))
    return out


@dataclass
class Trecho:
    id: str            # "tesouro-selic#liquidez-e-resgate"
    doc: str           # "tesouro-selic"
    titulo: str        # título do documento
    secao: str         # título da seção
    url: str           # primeira URL do cabeçalho
    fonte: str
    texto: str         # texto que vai para o modelo
    tokens: list[str] = field(repr=False, default_factory=list)


def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _sem_acento(t.lower())).strip("-")


def carregar_trechos(pasta: Path = CONTEUDO) -> list[Trecho]:
    trechos = []
    for arq in sorted(pasta.glob("*.md")):
        bruto = arq.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", bruto, re.S)
        if not m:
            continue
        meta = yaml.safe_load(m.group(1)) or {}
        corpo = re.sub(r"<!--.*?-->", "", m.group(2), flags=re.S)
        urls = meta.get("url") or []
        url = urls[0] if isinstance(urls, list) and urls else (urls if isinstance(urls, str) else "")
        fonte = meta.get("fonte")
        fonte = ", ".join(fonte) if isinstance(fonte, list) else str(fonte or "")
        doc, titulo = meta.get("id", arq.stem), meta.get("titulo", arq.stem)

        partes = re.split(r"^## +(.+)$", corpo, flags=re.M)
        # partes = [antes_da_primeira_secao, titulo1, corpo1, titulo2, corpo2, ...]
        for i in range(1, len(partes), 2):
            secao, texto = partes[i].strip(), partes[i + 1].strip()
            if not texto:
                continue
            cabeca = f"{titulo} — {secao}"
            trechos.append(Trecho(
                id=f"{doc}#{_slug(secao)}", doc=doc, titulo=titulo, secao=secao, url=url, fonte=fonte,
                texto=f"{cabeca}\n\n{texto}",
                # título e seção contam em dobro: ajudam a achar o trecho certo
                tokens=tokenizar(cabeca) * 2 + tokenizar(texto),
            ))
    return trechos


class BM25:
    def __init__(self, trechos: list[Trecho], k1: float = 1.5, b: float = 0.75):
        self.trechos, self.k1, self.b = trechos, k1, b
        self.tf = [Counter(t.tokens) for t in trechos]
        self.dl = [len(t.tokens) for t in trechos]
        self.avgdl = sum(self.dl) / max(len(self.dl), 1)
        df = Counter(tok for t in trechos for tok in set(t.tokens))
        n = len(trechos)
        self.idf = {tok: math.log(1 + (n - f + 0.5) / (f + 0.5)) for tok, f in df.items()}

    def buscar(self, consulta: str, k: int = 4, docs: set[str] | None = None,
               max_por_doc: int = 2) -> list[tuple[Trecho, float]]:
        q = tokenizar(consulta, consulta=True)
        pontuados = []
        for i, t in enumerate(self.trechos):
            if docs and t.doc not in docs:
                continue
            s = 0.0
            for tok in q:
                f = self.tf[i].get(tok)
                if f:
                    s += self.idf[tok] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
            if s > 0:
                pontuados.append((t, s))
        pontuados.sort(key=lambda x: -x[1])
        # no máximo `max_por_doc` trechos de cada documento, para perguntas que comparam produtos
        escolhidos, por_doc = [], Counter()
        for t, s in pontuados:
            if por_doc[t.doc] < max_por_doc:
                escolhidos.append((t, s))
                por_doc[t.doc] += 1
            if len(escolhidos) == k:
                break
        return escolhidos


_INDICE: BM25 | None = None


def indice() -> BM25:
    global _INDICE
    if _INDICE is None:
        _INDICE = BM25(carregar_trechos())
    return _INDICE


def buscar(consulta: str, k: int = 4, docs: set[str] | None = None, max_por_doc: int = 2) -> list[Trecho]:
    return [t for t, _ in indice().buscar(consulta, k, docs, max_por_doc)]


def por_id(trecho_id: str) -> Trecho | None:
    return next((t for t in indice().trechos if t.id == trecho_id), None)
