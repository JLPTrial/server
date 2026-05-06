"""Módulo principal da API JLPTrial.

Configura a aplicação FastAPI, incluindo CORS e rotas básicas.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="JLPTrial API")

flavor = os.getenv("APP_FLAVOR", "dev").strip().lower()

if flavor == "prod":
    ORIGINS_KEY = "PROD_BACKEND_CORS_ORIGINS"
else:
    ORIGINS_KEY = "DEV_BACKEND_CORS_ORIGINS"

origins_raw = os.getenv(ORIGINS_KEY, "*")

origins = []
for origin in origins_raw.split(","):
    origin = origin.strip()
    if origin:
        origins.append(origin)

if not origins:
    raise ValueError(
        f"Variável de ambiente '{ORIGINS_KEY}' está vazia ou inválida. "
        f"Valor recebido: '{origins_raw}'."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Retorna mensagem simples indicando que a API está ativa."""
    return {"message": "Backend JLPTrial ativo com sucesso."}


@app.get("/health")
def health() -> dict[str, str]:
    """Endpoint de verificação de saúde da aplicação."""
    return {"status": "ok"}
