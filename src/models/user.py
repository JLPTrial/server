from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    # Apenas o vínculo com o Firebase é registrado localmente; nome e email
    # ficam no Firebase e podem ser consultados por lá quando necessário.
    firebase_uid: str = Field(primary_key=True, index=True)
