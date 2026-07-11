from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class QuestionStatus(Enum):
    CORRECT = 1
    INCORRECT = 0


######################
# UserQuestion
######################
class UserQuestion(SQLModel, table=True):
    """Stores the relationship between a user and a question, including answer status."""

    __tablename__ = "user_question"

    user_firebase_uid: str = Field(
        foreign_key="user.firebase_uid",
        primary_key=True,
        index=True,
    )

    question_id: int | None = Field(
        default=None, foreign_key="questions.id", primary_key=True
    )

    status: QuestionStatus | None = Field(default=None)

    selected_alternative: int | None = Field(default=None)

    # Relationships
    question: Optional["Questions"] = Relationship(back_populates="users_link")


class QuestionTags(SQLModel, table=True):
    __tablename__ = "question_tags"

    question_id: int | None = Field(
        default=None,
        foreign_key="questions.id",
        primary_key=True,
    )

    tag_id: int | None = Field(
        default=None,
        foreign_key="tags.id",
        primary_key=True,
    )


class Tags(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(nullable=False, unique=True)

    questions: list["Questions"] = Relationship(
        back_populates="tags",
        link_model=QuestionTags,
    )


class Statement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question_command: str = Field(nullable=False, unique=True)
    questions: list["Questions"] = Relationship(back_populates="statement")


class ContextualTexts(SQLModel, table=True):
    __tablename__ = "contextual_texts"

    id: int | None = Field(default=None, primary_key=True)

    contextual_text: str = Field(nullable=False, unique=True)

    media: list["Media"] = Relationship(back_populates="contextual_text")


class Alternatives(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    alternative_1: str = Field(nullable=False)
    alternative_2: str = Field(nullable=False)
    alternative_3: str = Field(nullable=False)
    alternative_4: str | None = Field(default=None)

    correct_alternative: int = Field(nullable=False, ge=1, le=4)

    question: Optional["Questions"] = Relationship(back_populates="alternatives")


class Media(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    contextual_text_id: int | None = Field(
        default=None,
        foreign_key="contextual_texts.id",
    )

    image_file_path: str | None = Field(default=None)
    audio_file_path: str | None = Field(default=None)

    contextual_text: ContextualTexts | None = Relationship(back_populates="media")
    questions: list["Questions"] = Relationship(back_populates="media")


class Questions(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    uid: str = Field(nullable=False, unique=True, index=True)

    # Nível JLPT de origem da questão ("N5", "N4", ...)
    level: str = Field(nullable=False, index=True)

    alternative_id: int = Field(
        foreign_key="alternatives.id",
        nullable=False,
        unique=True,
    )
    media_id: int | None = Field(default=None, foreign_key="media.id")
    statement_id: int = Field(foreign_key="statement.id", nullable=False)

    question_text: str = Field(nullable=False)
    question_type: str = Field(nullable=False)

    alternatives: Alternatives | None = Relationship(back_populates="question")
    media: Media | None = Relationship(back_populates="questions")
    statement: Statement | None = Relationship(back_populates="questions")
    tags: list["Tags"] = Relationship(
        back_populates="questions", link_model=QuestionTags
    )

    users_link: list[UserQuestion] = Relationship(back_populates="question")
