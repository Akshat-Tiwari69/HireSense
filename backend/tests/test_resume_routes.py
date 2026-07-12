"""Upload-boundary tests for public candidate applications."""

from contextlib import contextmanager
import io
import zipfile

import pytest
from flask import Flask

import resume_routes


def _write_docx(path, extra_entries=None):
    entries = {
        "[Content_Types].xml": b"<Types/>",
        "_rels/.rels": b"<Relationships/>",
        "word/document.xml": b"<document/>",
    }
    entries.update(extra_entries or {})
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)


def test_pdf_validation_rejects_renamed_arbitrary_file(tmp_path):
    filepath = tmp_path / "resume.pdf"
    filepath.write_bytes(b"this is not a PDF")

    with pytest.raises(resume_routes.UploadValidationError, match="signature"):
        resume_routes._validate_resume_file(filepath, "pdf")


def test_pdf_validation_requires_header_and_eof_marker(tmp_path):
    filepath = tmp_path / "resume.pdf"
    filepath.write_bytes(b"%PDF-1.7\nminimal fixture\n%%EOF\n")

    resume_routes._validate_resume_file(filepath, "pdf")


def test_docx_validation_accepts_required_safe_container(tmp_path):
    filepath = tmp_path / "resume.docx"
    _write_docx(filepath)

    resume_routes._validate_resume_file(filepath, "docx")


def test_docx_validation_rejects_unsafe_paths(tmp_path):
    filepath = tmp_path / "resume.docx"
    _write_docx(filepath, {"../outside.xml": b"unsafe"})

    with pytest.raises(resume_routes.UploadValidationError, match="unsafe file path"):
        resume_routes._validate_resume_file(filepath, "docx")


def test_docx_validation_rejects_excessive_expansion(tmp_path, monkeypatch):
    filepath = tmp_path / "resume.docx"
    _write_docx(filepath, {"word/large.xml": b"x" * 100})
    monkeypatch.setattr(resume_routes, "MAX_DOCX_UNCOMPRESSED_BYTES", 50)

    with pytest.raises(resume_routes.UploadValidationError, match="expands beyond"):
        resume_routes._validate_resume_file(filepath, "docx")


def test_job_application_lookup_excludes_expired_postings(monkeypatch):
    class Cursor:
        query = None

        def execute(self, query, _params):
            self.query = " ".join(query.split())

        def fetchone(self):
            return None

    cursor = Cursor()

    class Connection:
        def cursor(self):
            return cursor

    @contextmanager
    def fake_db_connection():
        yield Connection()

    monkeypatch.setattr(resume_routes, "db_connection", fake_db_connection)

    assert resume_routes._get_job_description_for_id(7) == (None, None)
    assert "closes_at IS NULL OR closes_at > CURRENT_TIMESTAMP" in cursor.query


def test_upload_rejects_invalid_pdf_before_parsing_or_persisting(tmp_path, monkeypatch):
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    app.register_blueprint(resume_routes.resume_bp)

    monkeypatch.setattr(
        resume_routes,
        "_get_job_description_for_id",
        lambda _job_id: (
            {"skills": [], "min_experience": 0, "title": "Engineer"},
            {"id": 7, "title": "Engineer", "department": "Technology"},
        ),
    )

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("invalid files must be rejected before parsing or persistence")

    monkeypatch.setattr(resume_routes, "parse_resume", unexpected_call)
    monkeypatch.setattr(resume_routes, "insert_candidate_application", unexpected_call)

    response = app.test_client().post(
        "/resume/upload",
        data={
            "job_id": "7",
            "name": "Candidate",
            "email": "candidate@example.test",
            "file": (io.BytesIO(b"not really a pdf"), "resume.pdf"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "signature" in response.get_json()["message"]
    assert list(tmp_path.iterdir()) == []
