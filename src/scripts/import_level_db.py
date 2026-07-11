import argparse
import logging
import sqlite3
from pathlib import Path

from sqlmodel import Session, select

from ..core.config import settings
from ..database import session as database_session
from ..database.init_db import init_db
from ..models.question import (
    Alternatives,
    ContextualTexts,
    Media,
    Questions,
    QuestionTags,
    Statement,
    Tags,
)

logger = logging.getLogger(__name__)


def _required_id(record_id: int | None) -> int:
    if record_id is None:
        raise RuntimeError("Registro sem id após o flush")
    return record_id


def _add_level_prefix(path: str | None, level: str) -> str | None:
    if not path:
        return None
    return f"{level}/{path}"


def _set_fields(obj: object, **fields: object) -> bool:
    changed = False
    for name, value in fields.items():
        if getattr(obj, name) != value:
            setattr(obj, name, value)
            changed = True
    return changed


def _import_statements(session: Session, source: sqlite3.Connection) -> dict[int, int]:
    ids: dict[int, int] = {}
    for row in source.execute("SELECT id, question_command FROM statement"):
        statement = session.exec(
            select(Statement).where(Statement.question_command == row["question_command"])
        ).first()
        if statement is None:
            statement = Statement(question_command=row["question_command"])
            session.add(statement)
            session.flush()
        ids[row["id"]] = _required_id(statement.id)
    return ids


def _import_contextual_texts(session: Session, source: sqlite3.Connection) -> dict[int, int]:
    ids: dict[int, int] = {}
    for row in source.execute("SELECT id, contextual_text FROM contextual_texts"):
        text = session.exec(
            select(ContextualTexts).where(
                ContextualTexts.contextual_text == row["contextual_text"]
            )
        ).first()
        if text is None:
            text = ContextualTexts(contextual_text=row["contextual_text"])
            session.add(text)
            session.flush()
        ids[row["id"]] = _required_id(text.id)
    return ids


def _import_tags(session: Session, source: sqlite3.Connection) -> dict[int, int]:
    ids: dict[int, int] = {}
    for row in source.execute("SELECT id, name FROM tags"):
        tag = session.exec(select(Tags).where(Tags.name == row["name"])).first()
        if tag is None:
            tag = Tags(name=row["name"])
            session.add(tag)
            session.flush()
        ids[row["id"]] = _required_id(tag.id)
    return ids


def _import_alternatives(session: Session, question: Questions | None, row: sqlite3.Row) -> tuple[int, bool]:
    alternatives = None
    if question is not None:
        alternatives = session.get(Alternatives, question.alternative_id)

    if alternatives is None:
        alternatives = Alternatives(
            alternative_1=row["alternative_1"],
            alternative_2=row["alternative_2"],
            alternative_3=row["alternative_3"],
            alternative_4=row["alternative_4"],
            correct_alternative=row["correct_alternative"],
        )
        session.add(alternatives)
        changed = True
    else:
        changed = _set_fields(
            alternatives,
            alternative_1=row["alternative_1"],
            alternative_2=row["alternative_2"],
            alternative_3=row["alternative_3"],
            alternative_4=row["alternative_4"],
            correct_alternative=row["correct_alternative"],
        )

    session.flush()
    return _required_id(alternatives.id), changed


def _import_media(
    session: Session,
    question: Questions | None,
    row: sqlite3.Row | None,
    level: str,
    text_ids: dict[int, int],
) -> tuple[int | None, bool]:
    media = None
    if question is not None and question.media_id is not None:
        media = session.get(Media, question.media_id)

    if row is None:
        if media is not None and question is not None:
            question.media_id = None
            session.flush()
            session.delete(media)
            return None, True
        return None, False

    contextual_text_id = None
    if row["contextual_text_id"] is not None:
        contextual_text_id = text_ids[row["contextual_text_id"]]

    created = media is None
    if media is None:
        media = Media()
        session.add(media)

    changed = _set_fields(
        media,
        contextual_text_id=contextual_text_id,
        image_file_path=_add_level_prefix(row["image_file_path"], level),
        audio_file_path=_add_level_prefix(row["audio_file_path"], level),
    )

    session.flush()
    return _required_id(media.id), created or changed


def _import_question_tags(
    session: Session,
    source: sqlite3.Connection,
    source_question_id: int,
    question_id: int,
    tag_ids: dict[int, int],
) -> bool:
    
    links = session.exec(
        select(QuestionTags).where(QuestionTags.question_id == question_id)
    ).all()
    current_tags = {link.tag_id for link in links}
    desired_tags = {
        tag_ids[row["tag_id"]]
        for row in source.execute(
            "SELECT tag_id FROM question_tags WHERE question_id = ?",
            (source_question_id,),
        )
    }

    if current_tags == desired_tags:
        return False

    for link in links:
        session.delete(link)
    session.flush()

    for tag_id in desired_tags:
        session.add(QuestionTags(question_id=question_id, tag_id=tag_id))
    return True


def import_level_db(source_db: Path, level: str) -> tuple[int, int, int]:
    source = sqlite3.connect(f"file:{source_db}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row

    inserted = 0
    updated = 0
    unchanged = 0

    with Session(database_session.ENGINE) as session:
        statement_ids = _import_statements(session, source)
        text_ids = _import_contextual_texts(session, source)
        tag_ids = _import_tags(session, source)

        for row in source.execute("SELECT * FROM questions ORDER BY id"):
            question = session.exec(
                select(Questions).where(Questions.uid == row["uid"])
            ).first()

            alternatives_row = source.execute(
                "SELECT * FROM alternatives WHERE id = ?", (row["alternative_id"],)
            ).fetchone()
            media_row = None
            if row["media_id"] is not None:
                media_row = source.execute(
                    "SELECT * FROM media WHERE id = ?", (row["media_id"],)
                ).fetchone()

            alternative_id, alternatives_changed = _import_alternatives(
                session, question, alternatives_row
            )
            media_id, media_changed = _import_media(
                session, question, media_row, level, text_ids
            )

            if question is None:
                question = Questions(
                    uid=row["uid"],
                    level=level,
                    alternative_id=alternative_id,
                    media_id=media_id,
                    statement_id=statement_ids[row["statement_id"]],
                    question_text=row["question_text"],
                    question_type=row["question_type"],
                )
                session.add(question)
                session.flush()
                _import_question_tags(
                    session, source, row["id"], _required_id(question.id), tag_ids
                )
                inserted += 1
                continue

            question_changed = _set_fields(
                question,
                level=level,
                alternative_id=alternative_id,
                media_id=media_id,
                statement_id=statement_ids[row["statement_id"]],
                question_text=row["question_text"],
                question_type=row["question_type"],
            )
            tags_changed = _import_question_tags(
                session, source, row["id"], _required_id(question.id), tag_ids
            )

            if question_changed or alternatives_changed or media_changed or tags_changed:
                updated += 1
            else:
                unchanged += 1

        session.commit()

    source.close()
    return inserted, updated, unchanged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_db", type=Path)
    parser.add_argument("level", choices=sorted(settings.AVAILABLE_QUESTION_LEVELS.values()))
    args = parser.parse_args()

    
    init_db()

    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", force=True)

    inserted, updated, unchanged = import_level_db(args.source_db, args.level)
    logger.info(
        "Importação de %s concluída: %d inseridas, %d atualizadas, %d inalteradas",
        args.level,
        inserted,
        updated,
        unchanged,
    )


if __name__ == "__main__":
    main()
