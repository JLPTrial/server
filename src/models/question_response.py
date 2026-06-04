from pydantic import ConfigDict, field_serializer, model_serializer
from sqlmodel import SQLModel


class QuestionStatementResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    question_command: str


class QuestionAlternativesResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    alternative_1: str | None
    alternative_2: str | None
    alternative_3: str | None
    alternative_4: str | None
    correct_alternative: int


class QuestionContextualTextResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    contextual_text: str


class QuestionMediaResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    audio_file_path: str | None
    image_file_path: str | None
    contextual_text: QuestionContextualTextResponse | None = None

    @model_serializer(mode="plain")
    def serialize_media(self) -> dict[str, str | None]:
        return {
            "audio_file_path": self.audio_file_path,
            "image_file_path": self.image_file_path,
            "text_content": (
                self.contextual_text.contextual_text
                if self.contextual_text is not None
                else None
            ),
        }


class QuestionTagResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    name: str


class QuestionResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_type: str
    question_text: str
    statement: QuestionStatementResponse
    alternatives: QuestionAlternativesResponse
    media: QuestionMediaResponse | None = None
    tags: list[QuestionTagResponse]

    @field_serializer("tags")
    def serialize_tags(
        self,
        tags: list[QuestionTagResponse],
    ) -> list[str]:
        return [tag.name for tag in tags]
