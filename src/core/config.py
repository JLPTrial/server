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

    SERVER_DB_FILE: str = str(SERVER_DIR / "data" / "server.db")

    AVAILABLE_QUESTION_LEVELS: dict[int, str] = {4: "N4", 5: "N5"}

    AVAILABLE_QUESTION_TYPES: list[str] = [
        "grammar",
        "vocabulary",
        "kanji",
        "reading",
        "listening",
    ]

    AVAILABLE_QUESTION_ANSWER_STATUSES: list[str] = [
        "all",
        "answered",
        "unanswered",
        "correct",
        "incorrect",
    ]

    AVAILABLE_STATISTICS_PERIODS: list[str] = [
        "all",
        "day",
        "week",
        "month",
        "year",
    ]

    # Mock test guide (n, topic_id, statement_id)
    MOCK_GUIDE: dict[int, list[tuple]] = {
        5: [
            (7, "kanji", 3),
            (5, "kanji", 4),
            # (6, "vocabulary",14),
            (12, "vocabulary", 12),
            (6, "vocabulary", 13),
            (5, "grammar", 15),
            (4, "grammar", 2),
            (2, "reading", 16),
            (4, "reading", 11),
            (3, "reading", 17),
            (5, "reading", 10),
            (7, "listening", 6),
            (6, "listening", 5),
            (6, "listening", 8),
            (5, "listening", 7),
        ],
        4: [
            (7, "kanji", 3),
            (5, "kanji", 4),
            (8, "vocabulary", 12),
            (4, "vocabulary", 13),
            (4, "vocabulary", 14),
            (13, "grammar", 1),
            (4, "grammar", 2),
            (4, "reading", 11),
            (8, "reading", 10),
            (8, "listening", 6),
            (7, "listening", 5),
            (8, "listening", 8),
            (5, "listening", 7),
        ],
    }

    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite:///{self.SERVER_DB_FILE}"

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
