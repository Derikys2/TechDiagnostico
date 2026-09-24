"""Servidor compartilhado do TechDiagnóstico.

Instale: python -m pip install fastapi uvicorn openai
Execute: uvicorn techdiagnostico_servidor:app --host 0.0.0.0 --port 8000

Configure OPENAI_API_KEY no servidor para habilitar buscas com fontes.
Configure TECH_ADMIN_TOKEN antes de disponibilizar o servidor na internet.
"""

import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


DB_PATH = Path(os.getenv("TECH_DB_PATH", Path(__file__).with_name("casos_compartilhados.db")))
APP_TOKEN = os.getenv("TECH_ADMIN_TOKEN", "")
app = FastAPI(title="TechDiagnóstico: casos compartilhados")


def conectar():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def iniciar_banco():
    with conectar() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS casos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criado_em TEXT NOT NULL,
                sintomas TEXT NOT NULL,
                sugestao TEXT NOT NULL,
                resolvido INTEGER,
                UNIQUE(id)
            );
        """)


iniciar_banco()


def autenticar(token):
    if APP_TOKEN and token != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")


class Caso(BaseModel):
    sintomas: dict[str, bool]
    sugestao: str = Field(min_length=3, max_length=200)


class Retorno(BaseModel):
    resolvido: bool


class Pesquisa(BaseModel):
    sintomas: list[str] = Field(min_length=1, max_length=8)


@app.post("/casos")
def registrar(caso: Caso, x_app_token: str | None = Header(default=None)):
    autenticar(x_app_token)
    if len(caso.sintomas) > 40 or any(len(chave) > 60 for chave in caso.sintomas):
        raise HTTPException(status_code=422, detail="Sintomas inválidos")
    with conectar() as db:
        cursor = db.execute(
            "INSERT INTO casos(criado_em, sintomas, sugestao) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(),
             json.dumps(caso.sintomas, ensure_ascii=False, sort_keys=True), caso.sugestao),
        )
        return {"id": cursor.lastrowid}


@app.post("/casos/{identificador}/retorno")
def registrar_retorno(identificador: int, retorno: Retorno,
                     x_app_token: str | None = Header(default=None)):
    autenticar(x_app_token)
    with conectar() as db:
        cursor = db.execute(
            "UPDATE casos SET resolvido = ? WHERE id = ? AND resolvido IS NULL",
            (int(retorno.resolvido), identificador),
        )
        if not cursor.rowcount:
            raise HTTPException(status_code=404, detail="Caso inexistente ou já avaliado")
    return {"ok": True}


@app.post("/sugestoes")
def sugestoes(caso: Caso, x_app_token: str | None = Header(default=None)):
    autenticar(x_app_token)
    with conectar() as db:
        rows = db.execute(
            "SELECT sintomas, sugestao FROM casos WHERE resolvido = 1 ORDER BY id DESC LIMIT 1000"
        ).fetchall()
    contagem = Counter()
    for row in rows:
        antigos = json.loads(row["sintomas"])
        coincidencias = sum(
            chave in caso.sintomas and caso.sintomas[chave] == valor
            for chave, valor in antigos.items()
        )
        if coincidencias >= 2 and coincidencias / max(len(antigos), 1) >= 0.6:
            contagem[row["sugestao"]] += 1
    return [{"sugestao": nome, "casos_confirmados_semelhantes": total}
            for nome, total in contagem.most_common(3)]


@app.post("/pesquisar")
def pesquisar(pesquisa: Pesquisa, x_app_token: str | None = Header(default=None)):
    autenticar(x_app_token)
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="Busca online não configurada no servidor")
    from openai import OpenAI

    termos = ", ".join(item[:100] for item in pesquisa.sintomas)
    try:
        resposta = OpenAI(timeout=30).responses.create(
            model=os.getenv("TECH_SEARCH_MODEL", "gpt-5.5"),
            tools=[{"type": "web_search"}],
            tool_choice="required",
            input=("Pesquise orientação inicial para problemas de computador a partir destes "
                   f"sintomas: {termos}. Priorize documentação oficial dos fabricantes. "
                   "Informe até três hipóteses com passos externos simples. "
                   "Inclua links das fontes consultadas. Não afirme diagnóstico definitivo."),
        )
    except Exception as erro:
        raise HTTPException(status_code=502, detail="Falha ao consultar a busca online") from erro
    return {"texto": resposta.output_text}
