from sqlmodel import Field, SQLModel

from ..database.metadata import USER_METADATA


class User(SQLModel, table=True):
    metadata = USER_METADATA

    firebase_uid: str = Field(primary_key=True, index=True)
    email: str = Field(nullable=False, unique=True)
    name: str = Field(nullable=False)
