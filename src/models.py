from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, CheckConstraint


######################
# USER (TEMPORÁRIO)
######################
class User(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(
        default=None,
        primary_key=True

    )


    email: str = Field(nullable=False, unique=True)
    password: str = Field(nullable=False)

######################
# QUESTION TAGS
######################

class QuestionTags(SQLModel, table=True):
    __tablename__ = "question_tags"

    question_id: Optional[int] = Field(
        default=None,
        foreign_key="questions.id",
        primary_key=True
    )

    tag_id: Optional[int] = Field(
        default=None,
        foreign_key="tags.id",
        primary_key=True
    )


######################
# TAGS
######################

class Tags(SQLModel, table=True):
    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(nullable=False, unique=True)

    # Relationships
    questions: List["Questions"] = Relationship(
        back_populates="tags",
        link_model=QuestionTags
    )


######################
# STATEMENT
######################

class Statement(SQLModel, table=True):
    __tablename__ = "statement"

    id: Optional[int] = Field(default=None, primary_key=True)

    question_command: str = Field(nullable=False, unique=True)

    # Relationships
    questions: List["Questions"] = Relationship(
        back_populates="statement"
    )


######################
# CONTEXTUAL TEXTS
######################

class ContextualTexts(SQLModel, table=True):
    __tablename__ = "contextual_texts"

    id: Optional[int] = Field(default=None, primary_key=True)

    contextual_text: str = Field(nullable=False, unique=True)

    # Relationships
    media: List["Media"] = Relationship(
        back_populates="contextual_text"
    )


######################
# ALTERNATIVES
######################

class Alternatives(SQLModel, table=True):
    __tablename__ = "alternatives"

    __table_args__ = (
        CheckConstraint(
            "correct_alternative BETWEEN 1 AND 4",
            name="correct_alternative_check"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    alternative_1: str = Field(nullable=False)

    alternative_2: str = Field(nullable=False)

    alternative_3: str = Field(nullable=False)

    alternative_4: Optional[str] = Field(default=None)

    correct_alternative: int = Field(nullable=False)

    # Relationships
    question: Optional["Questions"] = Relationship(
        back_populates="alternative"
    )


######################
# MEDIA
######################

class Media(SQLModel, table=True):
    __tablename__ = "media"

    __table_args__ = (
        CheckConstraint(
            """
            contextual_text_id IS NOT NULL
            OR image_file_path IS NOT NULL
            OR audio_file_path IS NOT NULL
            """,
            name="media_not_empty_check"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    contextual_text_id: Optional[int] = Field(
        default=None,
        foreign_key="contextual_texts.id"
    )

    image_file_path: Optional[str] = Field(default=None)

    audio_file_path: Optional[str] = Field(default=None)

    # Relationships
    contextual_text: Optional["ContextualTexts"] = Relationship(
        back_populates="media"
    )

    questions: List["Questions"] = Relationship(
        back_populates="media"
    )


######################
# QUESTIONS
######################

class Questions(SQLModel, table=True):
    __tablename__ = "questions"

    __table_args__ = (
        CheckConstraint(
            """
            question_type IN (
                'grammar',
                'vocabulary',
                'kanji',
                'reading',
                'listening'
            )
            """,
            name="question_type_check"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    alternative_id: int = Field(
        foreign_key="alternatives.id",
        nullable=False,
        unique=True
    )

    media_id: Optional[int] = Field(
        default=None,
        foreign_key="media.id"
    )

    statement_id: int = Field(
        foreign_key="statement.id",
        nullable=False
    )

    question_text: str = Field(nullable=False)

    question_type: str = Field(
        sa_column=Column(String, nullable=False)
    )

    # Relationships

    alternative: Optional["Alternatives"] = Relationship(
        back_populates="question"
    )

    media: Optional["Media"] = Relationship(
        back_populates="questions"
    )

    statement: Optional["Statement"] = Relationship(
        back_populates="questions"
    )

    tags: List["Tags"] = Relationship(
        back_populates="questions",
        link_model=QuestionTags
    )
