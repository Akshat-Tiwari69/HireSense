"""Safety and validation contracts for admin content ingestion."""

import io
import zipfile
from contextlib import contextmanager
from pathlib import Path

import pytest
from flask_jwt_extended import create_access_token

import admin_content
from admin_content import (
    _extract_resume_zip,
    _normalize_parsed_questions,
    _process_single_resume,
)
from app import app


def _write_zip(path, members):
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def test_zip_extraction_rejects_path_traversal(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    destination = tmp_path / "extract"
    destination.mkdir()
    _write_zip(archive_path, {"../outside.pdf": b"resume"})

    with pytest.raises(ValueError, match="unsafe file path"):
        _extract_resume_zip(archive_path, destination)

    assert not (tmp_path / "outside.pdf").exists()


def test_zip_extraction_only_materializes_supported_resumes(tmp_path):
    archive_path = tmp_path / "resumes.zip"
    destination = tmp_path / "extract"
    destination.mkdir()
    _write_zip(
        archive_path,
        {
            "engineering/Alice Resume.pdf": b"pdf-content",
            "notes.txt": b"not a resume",
        },
    )

    extracted = _extract_resume_zip(archive_path, destination)

    assert len(extracted) == 1
    assert extracted[0][1] == "engineering/Alice Resume.pdf"
    assert Path(extracted[0][0]).read_bytes() == b"pdf-content"


def test_question_normalization_rejects_non_list_provider_output():
    with pytest.raises(ValueError, match="did not return a list"):
        _normalize_parsed_questions({"question": "Not a list"})


def test_question_normalization_bounds_and_defaults_fields():
    normalized = _normalize_parsed_questions(
        [{"question": "  What is Python?  ", "options": "invalid", "difficulty": "unknown"}]
    )

    assert normalized == [{
        "question": "What is Python?",
        "options": None,
        "correct_answer": None,
        "category": "custom",
        "difficulty": "medium",
    }]


def test_ai_enhance_requires_json_object():
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "admin", "name": "Admin"},
        )

    response = app.test_client().post(
        "/api/admin/ai-enhance",
        headers={"Authorization": f"Bearer {token}"},
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "A JSON object is required"


def test_bulk_upload_rejects_rar_archives():
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "admin", "name": "Admin"},
        )

    response = app.test_client().post(
        "/api/admin/bulk-upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"file": (io.BytesIO(b"not-rar"), "resumes.rar")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Please upload a .zip file"


def test_unreadable_bulk_resume_has_no_fake_shortlist_decision(monkeypatch, tmp_path):
    import pypdf
    import resume_parser

    resume_path = tmp_path / "unreadable.pdf"
    resume_path.write_bytes(b"not-a-real-pdf")
    captured = {}

    class Page:
        @staticmethod
        def extract_text():
            return ""

    class Reader:
        pages = [Page()]

    monkeypatch.setattr(pypdf, "PdfReader", lambda _stream: Reader())
    monkeypatch.setattr(resume_parser, "parse_resume", lambda *_args: {})

    def fake_insert_candidate_application(**kwargs):
        captured.update(kwargs)
        return 17

    monkeypatch.setattr(
        admin_content,
        "insert_candidate_application",
        fake_insert_candidate_application,
    )

    result = _process_single_resume(
        str(resume_path),
        resume_path.name,
        {"skills": [], "min_experience": 0},
        {"title": "Engineer"},
        3,
    )

    assert result["status"] == "success"
    assert captured["parsed_data"]["shortlist_status"] is None


def test_question_bank_persists_one_canonical_filename(monkeypatch, tmp_path):
    class Cursor:
        def execute(self, query, params):
            self.query = " ".join(query.split())
            self.params = params

        @staticmethod
        def fetchone():
            return (17,)

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()

        def cursor(self):
            return self.cursor_instance

        def commit(self):
            pass

    connection = Connection()

    @contextmanager
    def fake_db_connection():
        yield connection

    monkeypatch.setattr(admin_content, "db_connection", fake_db_connection)
    monkeypatch.setattr(
        admin_content, "get_upload_subdirectory", lambda *args, **kwargs: tmp_path
    )
    monkeypatch.setattr(
        admin_content, "_extract_text_from_file", lambda *args: "Q" * 40
    )
    monkeypatch.setattr(
        admin_content,
        "_parse_questions_from_text",
        lambda *args: [{"question": "What is Python?"}],
    )

    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "admin", "name": "Admin"},
        )

    response = app.test_client().post(
        "/api/admin/question-bank/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"file": (io.BytesIO(b"question bank"), "questions.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert "(original_filename, file_path" in connection.cursor_instance.query
    assert "(filename, original_filename" not in connection.cursor_instance.query
    assert len(connection.cursor_instance.params) == 7
