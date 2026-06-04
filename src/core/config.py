from pathlib import Path
from typing import Annotated, Any

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings

SERVER_DIR = Path(__file__).resolve().parents[2]


def parse_cors(value: Any) -> list[str] | str:
    if isinstance(value, str) and not value.startswith("["):
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    if isinstance(value, list | str):
        return value
    raise ValueError(value)


# Esta classe irá gerar as configurações principais do app
# caso você não esteja com o ambiente configurado


# Para levar isto a produção, é recomendado consultar o .env
# E colocar lá as informações necessárias.
# ISTO É APENAS UM PLACEHOLDER, NÃO ALTERE DADOS AQUI!
class Settings(BaseSettings):
    PROJECT_NAME: str = "JLPTrial API"
    APP_FLAVOR: str = "dev"
    IS_PROD: bool = APP_FLAVOR.strip().lower() == "prod"
    SECURE_REQUEST: bool = True
    FRONTEND_HOST: str = "http://localhost:5173"
    FIREBASE_SESSION_COOKIE_EXPIRE_DAYS: int = 10
    FIREBASE_SERVICE_ACCOUNT_FILE: str = str(
        SERVER_DIR / "keys" / "serviceAccountKey.json"
    )

    DEV_BACKEND_CORS_ORIGINS: Annotated[
        list[str] | str, BeforeValidator(parse_cors)
    ] = "*"
    PROD_BACKEND_CORS_ORIGINS: Annotated[
        list[str] | str, BeforeValidator(parse_cors)
    ] = []

    SQLITE_FILE: str = str(SERVER_DIR / "data" / "N5" / "N5.db")

    @property
    def cors_origins(self) -> list[str]:
        origins: list[str]
        if self.IS_PROD:
            raw = self.PROD_BACKEND_CORS_ORIGINS
        else:
            raw = self.DEV_BACKEND_CORS_ORIGINS

        if isinstance(raw, str):
            origins = [raw]
        else:
            origins = raw

        return [origin.rstrip("/") for origin in origins if origin]


settings = Settings()
