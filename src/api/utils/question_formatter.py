from ...models import Questions


def format_question(question: Questions) -> dict[str, object]:
    media = None
    if question.media is not None:
        # prefixing media file paths with "media/" to serve them correctly
        if question.media.audio_file_path is not None:
            question.media.audio_file_path = f"media/{question.media.audio_file_path}"

        if question.media.image_file_path is not None:
            question.media.image_file_path = f"media/{question.media.image_file_path}"

        # handling contextual text
        media = {
            "audio_file_path": question.media.audio_file_path,
            "image_file_path": question.media.image_file_path,
            "text_content": (
                question.media.contextual_text.contextual_text
                if question.media.contextual_text is not None
                else None
            ),
        }

    if question.statement is None:
        raise ValueError("Question has no statement")

    if question.alternatives is None:
        raise ValueError("Question has no alternatives")

    return {
        "id": question.id,
        "uid": question.uid,
        "level": question.level,
        "question_type": question.question_type,
        "question_text": question.question_text,
        "statement": {
            "question_command": question.statement.question_command,
        },
        "alternatives": {
            "alternative_1": question.alternatives.alternative_1,
            "alternative_2": question.alternatives.alternative_2,
            "alternative_3": question.alternatives.alternative_3,
            "alternative_4": question.alternatives.alternative_4,
            "correct_alternative": question.alternatives.correct_alternative,
        },
        "media": media,
        "tags": [tag.name for tag in question.tags],
    }
