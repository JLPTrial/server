from alembic import command
from alembic.config import Config

from ..core.config import SERVER_DIR


def init_db() -> None:
    # Aplica as migrações pendentes no banco unificado
    alembic_cfg = Config(str(SERVER_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
