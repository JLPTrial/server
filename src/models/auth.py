from sqlmodel import SQLModel


class FirebaseSignupRequest(SQLModel):
    uid_token: str
    name: str


class FirebaseLoginRequest(SQLModel):
    uid_token: str
