from .metadata import QUESTION_METADATA, USER_METADATA
from .session import ENGINES


def init_db() -> None:
    # Cria as tabelas para os usuários
    USER_METADATA.create_all(ENGINES["users"])

    # Cria as tabelas para as questões em todos os bancos de dados, exceto "users"
    for name in ENGINES:
        if name != "users":
            QUESTION_METADATA.create_all(ENGINES[name])
