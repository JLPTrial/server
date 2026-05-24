"""Módulo principal da API JLPTrial.

Configura a aplicação FastAPI, incluindo CORS e rotas básicas.
"""

import os

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware


from src.database import create_db_and_tables
from src.models import User, Questions
from sqlmodel import Session, select
from fastapi.responses import JSONResponse

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

# Engine do banco (inicializa depois)
engine = None

# ==============================
# STARTUP
# ==============================
@app.on_event("startup")
def on_startup() -> None:
    # Cria o banco e tabelas quando a API inicia
    global engine
    engine = create_db_and_tables()

@app.get("/")
def read_root() -> dict[str, str]:
    """Retorna mensagem simples indicando que a API está ativa."""
    return {"message": "Backend JLPTrial ativo com sucesso."}


@app.get("/health")
def health() -> dict[str, str]:
    """Endpoint de verificação de saúde da aplicação."""
    return {"status": "ok"}

# Usuários

# Criação de usuário
@app.post("/signup")
def signup(request: Request, user: User):
    with Session(engine) as session:
        try:
            session.add(user)       # adiciona no banco
            session.commit()        # salva
            session.refresh(user)   # atualiza objeto

        except Exception:
            print("Erro ao adicionar novo usuário")
            raise


# Login do usuário
@app.post("/login")
def login(request: Request, response: Response, user : User):
    with Session(engine) as session:

        # Tenta logar com email
        statement = select(User).where(User.email == user.email)
        statement = statement.where(User.password == user.password)
        user = session.exec(statement).first()

        # Se não achou, tenta com handle
        if not user:
            raise HTTPException(status_code=401, 
                                detail="Invalid username or password")

        # Create JSONResponse and set cookie on it (temporário) **********
        resp = JSONResponse({"redirect": "/"})
        resp.set_cookie(key="session_user", 
                        value=str(user.id), httponly=True, path="/")

        return resp


@app.get("/questions/{id}")
def question(request: Request, response: Response, id: int):
    """Uga uga"""
    with Session(engine) as session:

        # Tenta logar com email
        statement = select(Questions).where(Questions.id == id)
        questao = session.exec(statement).first()

        # Se não achou, tenta com handle
        # Create JSONResponse and set cookie on it (temporário) **********
        # resp.set_cookie(key="session_user", 
        # value=questao, httponly=True, path="/")

        return questao
