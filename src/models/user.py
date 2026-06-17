from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    firebase_uid: str = Field(primary_key=True, index=True)
    email: str = Field(nullable=False, unique=True)
    name: str = Field(nullable=False)
