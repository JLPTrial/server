import sqlite3
from pathlib import Path

from sqlmodel import Session, select

from src.models import Media, Questions, QuestionTags, Statement, Tags
from src.scripts.import_level_db import import_level_db

_SOURCE_SCHEMA = """
CREATE TABLE commands (id INTEGER PRIMARY KEY, question_command TEXT NOT NULL UNIQUE);
CREATE TABLE contextual_texts (id INTEGER PRIMARY KEY, contextual_text TEXT NOT NULL UNIQUE);
CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE alternatives (
	id INTEGER PRIMARY KEY,
	alternative_1 TEXT NOT NULL,
	alternative_2 TEXT NOT NULL,
	alternative_3 TEXT NOT NULL,
	alternative_4 TEXT,
	correct_alternative INTEGER NOT NULL
);
CREATE TABLE media (
	id INTEGER PRIMARY KEY,
	contextual_text_id INTEGER,
	image_file_path TEXT,
	audio_file_path TEXT
);
CREATE TABLE questions (
	id INTEGER PRIMARY KEY,
	uid TEXT NOT NULL UNIQUE,
	alternative_id INTEGER NOT NULL UNIQUE,
	media_id INTEGER UNIQUE,
	command_id INTEGER NOT NULL,
	question_text TEXT NOT NULL,
	question_type TEXT NOT NULL
);
CREATE TABLE question_tags (
	question_id INTEGER NOT NULL,
	tag_id INTEGER NOT NULL,
	PRIMARY KEY (question_id, tag_id)
);
"""


def _build_source_db(path: Path) -> None:
	con = sqlite3.connect(path)
	con.executescript(_SOURCE_SCHEMA)
	con.executescript(
		"""
		INSERT INTO commands (id, question_command) VALUES (1, 'Escolha a correta');
		INSERT INTO contextual_texts (id, contextual_text) VALUES (1, 'Texto de contexto');
		INSERT INTO tags (id, name) VALUES (1, 'particula'), (2, 'audio');
		INSERT INTO alternatives (id, alternative_1, alternative_2, alternative_3, alternative_4, correct_alternative)
			VALUES (1, 'A', 'B', 'C', 'D', 1), (2, 'A', 'B', 'C', NULL, 2);
		INSERT INTO media (id, contextual_text_id, image_file_path, audio_file_path)
			VALUES (1, 1, NULL, 'listening/JT4Y/L1-Q1.mp3');
		INSERT INTO questions (id, uid, alternative_id, media_id, command_id, question_text, question_type)
			VALUES (1, 'N5-grammar-0001', 1, NULL, 1, 'Pergunta 1', 'grammar');
		INSERT INTO questions (id, uid, alternative_id, media_id, command_id, question_text, question_type)
			VALUES (2, 'N5-listening-0001', 2, 1, 1, 'Pergunta 2', 'listening');
		INSERT INTO question_tags (question_id, tag_id) VALUES (1, 1), (2, 2);
		"""
	)
	con.commit()
	con.close()


def test_import_is_idempotent(db_engine, tmp_path: Path) -> None:
	source_db = tmp_path / "N5.db"
	_build_source_db(source_db)

	inserted, updated, unchanged = import_level_db(source_db, "N5")
	assert (inserted, updated, unchanged) == (2, 0, 0)

	# Reimportar sem mudanças na origem não altera nada
	inserted, updated, unchanged = import_level_db(source_db, "N5")
	assert (inserted, updated, unchanged) == (0, 0, 2)

	with Session(db_engine) as session:
		questions = session.exec(select(Questions)).all()
		assert len(questions) == 2
		assert {q.uid for q in questions} == {"N5-grammar-0001", "N5-listening-0001"}
		assert all(q.level == "N5" for q in questions)
		assert len(session.exec(select(Statement)).all()) == 1
		assert len(session.exec(select(Tags)).all()) == 2
		assert len(session.exec(select(Media)).all()) == 1


def test_import_prefixes_media_paths_with_level(db_engine, tmp_path: Path) -> None:
	source_db = tmp_path / "N5.db"
	_build_source_db(source_db)

	# reimportar não duplica prefixo
	import_level_db(source_db, "N5")
	import_level_db(source_db, "N5")

	with Session(db_engine) as session:
		media = session.exec(select(Media)).one()
		assert media.audio_file_path == "N5/listening/JT4Y/L1-Q1.mp3"
		assert media.image_file_path is None
		assert media.contextual_text_id is not None


def test_import_updates_existing_questions(db_engine, tmp_path: Path) -> None:
	source_db = tmp_path / "N5.db"
	_build_source_db(source_db)
	import_level_db(source_db, "N5")

	# Simula uma atualização do banco de origem: texto novo e tag removida
	con = sqlite3.connect(source_db)
	con.execute("UPDATE questions SET question_text = 'Pergunta 1 revisada' WHERE id = 1")
	con.execute("DELETE FROM question_tags WHERE question_id = 1")
	con.commit()
	con.close()

	# Apenas a questão 1 mudou na origem; a 2 fica inalterada
	inserted, updated, unchanged = import_level_db(source_db, "N5")
	assert (inserted, updated, unchanged) == (0, 1, 1)

	with Session(db_engine) as session:
		question = session.exec(
			select(Questions).where(Questions.uid == "N5-grammar-0001")
		).one()
		assert question.question_text == "Pergunta 1 revisada"
		links = session.exec(
			select(QuestionTags).where(QuestionTags.question_id == question.id)
		).all()
		assert links == []


def test_import_remaps_ids_across_levels(db_engine, tmp_path: Path) -> None:
	n5_db = tmp_path / "N5.db"
	n4_db = tmp_path / "N4.db"
	_build_source_db(n5_db)
	_build_source_db(n4_db)

	# Os dois níveis usam os mesmos ids de origem (1 e 2), mas uids distintos
	con = sqlite3.connect(n4_db)
	con.execute("UPDATE questions SET uid = replace(uid, 'N5-', 'N4-')")
	con.commit()
	con.close()

	import_level_db(n5_db, "N5")
	import_level_db(n4_db, "N4")

	with Session(db_engine) as session:
		questions = session.exec(select(Questions)).all()
		assert len(questions) == 4
		assert len({q.id for q in questions}) == 4  # ids novos, sem colisão
		# statements e tags idênticos são deduplicados entre níveis
		assert len(session.exec(select(Statement)).all()) == 1
		assert len(session.exec(select(Tags)).all()) == 2
