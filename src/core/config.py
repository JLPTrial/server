from pathlib import Path

from pydantic_settings import BaseSettings

SERVER_DIR = Path(__file__).resolve().parents[2]

# Esta classe irá gerar as configurações principais do app
# caso você não esteja com o ambiente configurado


# Para levar isto a produção, é recomendado consultar o .env
# E colocar lá as informações necessárias.
# ISTO É APENAS UM PLACEHOLDER, NÃO ALTERE DADOS AQUI!
class Settings(BaseSettings):
    PROJECT_NAME: str = "JLPTrial API"
    APP_FLAVOR: str = "dev"
    SECURE_REQUEST: bool = True
    FRONTEND_HOST: str = "http://localhost:5173"
    FIREBASE_SESSION_COOKIE_EXPIRE_DAYS: int = 10
    FIREBASE_SERVICE_ACCOUNT_FILE: str = str(
        SERVER_DIR / "keys" / "serviceAccountKey.json"
    )

    DEV_BACKEND_CORS_ORIGINS: str = "*"
    PROD_BACKEND_CORS_ORIGINS: str = ""

    SQLITE_FILE: str = str(SERVER_DIR / "data" / "N5" / "N5.db")

    @property
    def IS_PROD(self) -> bool:
        return self.APP_FLAVOR.strip().lower() == "prod"

    @property
    def cors_origins(self) -> list[str]:
        raw = self.DEV_BACKEND_CORS_ORIGINS

        if self.IS_PROD:
            raw = self.PROD_BACKEND_CORS_ORIGINS

        origins = []

        for origin in raw.split(","):
            origin = origin.strip().rstrip("/")

            if origin:
                origins.append(origin)

        return origins


settings = Settings()
