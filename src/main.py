"""Módulo principal da API JLPTrial.

Configura a aplicação FastAPI, incluindo CORS e rotas básicas.
"""

import os

# Third-party imports
from fastapi import FastAPI, HTTPException  # Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

# Local application imports
from database import create_db_and_tables
from models import User, Questions

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


# ==============================
# STARTUP
# ==============================
@app.on_event("startup")
def on_startup() -> None:
    """Initialize application resources on startup.
    """
    # Cria o banco e tabelas quando a API inicia
    app.state.engine = create_db_and_tables()


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
def signup(user: User):
    """Create a new `User` record in the database.

    Persists the provided `user` model and refreshes it with generated
    values (e.g. `id`). Raises on failure.
    """
    with Session(app.state.engine) as session:
        try:
            session.add(user)       # adiciona no banco
            session.commit()        # salva
            session.refresh(user)   # atualiza objeto

        except Exception:
            print("Erro ao adicionar novo usuário")
            raise


# Login do usuário
@app.post("/login")
def login(user: User):
    """Authenticate a `User` and return a JSONResponse with a session cookie.

    Validates the provided credentials and sets a `session_user` cookie on
    successful authentication. Raises HTTPException(401) on failure.
    """
    with Session(app.state.engine) as session:

        # Tenta logar com email
        statement = select(User).where(User.email == user.email)
        statement = statement.where(User.password == user.password)
        temp = session.exec(statement).first()

        # Se não achou, tenta com handle
        if not temp:
            raise HTTPException(status_code=401,
                                detail="Invalid username or password")

        found_user = temp

        # Create JSONResponse and set cookie on it (temporário) **********
        resp = JSONResponse({"redirect": "/"})
        resp.set_cookie(key="session_user",
                        value=str(found_user.id),
                        httponly=True,
                        path="/")

        return resp


@app.get("/questions/{id_questao}")
def question(id_questao: int):
    """Retrieve a question by its integer `id`.

    Returns the `Questions` instance if found, otherwise `None`.
    """
    with Session(app.state.engine) as session:

        # Tenta logar com email
        statement = select(Questions).where(Questions.id == id_questao)
        questao = session.exec(statement).first()

        # Se não achou, tenta com handle
        # Create JSONResponse and set cookie on it (temporário) **********
        # resp.set_cookie(key="session_user",
        # value=questao, httponly=True, path="/")

        return questao
