from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, CheckConstraint


class User(SQLModel, table=True):
    firebase_uid: str = Field(primary_key=True, index=True)
    email: str = Field(nullable=False, unique=True)
    name: str = Field(nullable=False)
