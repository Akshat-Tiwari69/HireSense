"""Safety and validation contracts for admin content ingestion."""

import io
import zipfile
from pathlib import Path

import pytest
from flask_jwt_extended import create_access_token

from admin_content import _extract_resume_zip, _normalize_parsed_questions
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
