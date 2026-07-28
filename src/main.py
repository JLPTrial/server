from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import api_router
from .core.config import settings
from .database.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.mount("/media", StaticFiles(directory="data/media"), name="media")

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Backend JLPTrial ativo com sucesso."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
