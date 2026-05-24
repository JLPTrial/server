# TODO: linkar com o \database

from sqlmodel import SQLModel, create_engine

arquivo_sqlite = "./data/N5/N5.db"
url_sqlite = f"sqlite:///{arquivo_sqlite}"

engine = create_engine(url_sqlite)

def create_db_and_tables():

    SQLModel.metadata.create_all(engine)
    return engine
