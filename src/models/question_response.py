# Simplificação dos DTOs para forçar o carregamento das coisas de maneira implicita
# Para que o Davi não tenha que buscar os dados da questão, estes DTOs juntos do
# format_questions resolvem para ele.

from sqlmodel import SQLModel


class QuestionStatementResponse(SQLModel):
    question_command: str


class QuestionAlternativesResponse(SQLModel):
    alternative_1: str
    alternative_2: str
    alternative_3: str
    alternative_4: str | None
    correct_alternative: int


class QuestionContextualTextResponse(SQLModel):
    contextual_text: str


class QuestionMediaResponse(SQLModel):
    audio_file_path: str | None
    image_file_path: str | None
    text_content: str | None = None


class QuestionResponse(SQLModel):
    id: int
    question_type: str
    question_text: str
    statement: QuestionStatementResponse
    alternatives: QuestionAlternativesResponse
    media: QuestionMediaResponse | None = None
    tags: list[str]
