from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from ..database.metadata import QUESTION_METADATA


class QuestionStatus(Enum):
    CORRECT = 2
    INCORRECT = 1
    NOT_ANSWERED = 0

######################
# UserQuestion
######################
class UserQuestion(SQLModel, table=True):
    """Stores the relationship between a user and a question, including answer status."""

    __tablename__ = "user_question"
    metadata = QUESTION_METADATA

    user_firebase_uid: str | None = Field(
        default=None, foreign_key="user.firebase_uid", primary_key=True
    )

    question_id: int | None = Field(
        default=None, foreign_key="questions.id", primary_key=True
    )

    status: QuestionStatus = Field(
        default=QuestionStatus.NOT_ANSWERED
    )

    selected_alternative: int | None = Field(default=None)

    # Relationships
    question: Optional["Questions"] = Relationship(back_populates="users_link")


class QuestionTags(SQLModel, table=True):
    __tablename__ = "question_tags"
    metadata = QUESTION_METADATA

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
    metadata = QUESTION_METADATA

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(nullable=False, unique=True)

    questions: list["Questions"] = Relationship(
        back_populates="tags",
        link_model=QuestionTags,
    )


class Statement(SQLModel, table=True):
    metadata = QUESTION_METADATA

    id: int | None = Field(default=None, primary_key=True)
    question_command: str = Field(nullable=False, unique=True)
    questions: list["Questions"] = Relationship(back_populates="statement")


class ContextualTexts(SQLModel, table=True):
    __tablename__ = "contextual_texts"
    metadata = QUESTION_METADATA

    id: int | None = Field(default=None, primary_key=True)

    contextual_text: str = Field(nullable=False, unique=True)

    media: list["Media"] = Relationship(back_populates="contextual_text")


class Alternatives(SQLModel, table=True):
    metadata = QUESTION_METADATA

    id: int | None = Field(default=None, primary_key=True)

    alternative_1: str = Field(nullable=False)
    alternative_2: str = Field(nullable=False)
    alternative_3: str = Field(nullable=False)
    alternative_4: str | None = Field(default=None)

    correct_alternative: int = Field(nullable=False, ge=1, le=4)

    question: Optional["Questions"] = Relationship(back_populates="alternatives")


class Media(SQLModel, table=True):
    metadata = QUESTION_METADATA

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
    metadata = QUESTION_METADATA

    id: int | None = Field(default=None, primary_key=True)

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
