"""Upload-boundary tests for public candidate applications."""

from contextlib import contextmanager
import io
import inspect
import zipfile

import pytest
from flask import Flask

import resume_routes
from user_db import DuplicateEmailError


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


def test_resume_validation_enforces_file_limit_independently_of_multipart_size(
    tmp_path, monkeypatch
):
    filepath = tmp_path / "resume.pdf"
    filepath.write_bytes(b"%PDF-1.7\n" + (b"x" * 64) + b"\n%%EOF\n")
    monkeypatch.setattr(resume_routes, "MAX_FILE_SIZE_BYTES", 50)

    with pytest.raises(resume_routes.UploadValidationError, match="10 MB"):
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


def _active_job(_job_id):
    return (
        {"skills": [], "min_experience": 0, "title": "Engineer"},
        {"id": 7, "title": "Engineer", "department": "Technology"},
    )


def _resume_client(tmp_path):
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    app.register_blueprint(resume_routes.resume_bp)
    return app.test_client()


def _valid_pdf_upload(**fields):
    return {
        "job_id": "7",
        "file": (io.BytesIO(b"%PDF-1.7\nminimal fixture\n%%EOF\n"), "resume.pdf"),
        **fields,
    }


def test_manual_email_duplicate_is_normalized_and_rejected_before_parsing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(resume_routes, "_get_job_description_for_id", _active_job)
    checked_emails = []

    def existing_candidate(email):
        checked_emails.append(email)
        return {
            "name": "Private Applicant",
            "status": "hired",
            "created_at": "private timestamp",
        }

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("duplicates must be rejected before resume parsing or AI")

    monkeypatch.setattr(resume_routes, "get_candidate_by_email", existing_candidate)
    monkeypatch.setattr(resume_routes, "parse_resume", unexpected_call)
    monkeypatch.setattr(resume_routes, "analyze_resume", unexpected_call)
    monkeypatch.setattr(resume_routes, "insert_candidate_application", unexpected_call)

    response = _resume_client(tmp_path).post(
        "/resume/upload",
        data=_valid_pdf_upload(
            name="Candidate",
            email="  Candidate@Example.TEST  ",
            phone="+91 98765 43210",
        ),
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 409
    assert checked_emails == ["candidate@example.test"]
    assert payload == {
        "status": "error",
        "message": "An application already exists for this email address.",
    }
    assert "Private Applicant" not in response.get_data(as_text=True)
    assert "candidate@example.test" not in response.get_data(as_text=True).lower()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", "n" * 201, "Name must be 200 characters or fewer"),
        ("email", f"{'e' * 243}@example.test", "Email must be 254 characters or fewer"),
        ("phone", "1" * 33, "Phone must be 32 characters or fewer"),
    ],
)
def test_upload_rejects_oversized_manual_fields_before_database_or_parsing(
    tmp_path, monkeypatch, field, value, message
):
    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("oversized fields must be rejected at the request boundary")

    monkeypatch.setattr(resume_routes, "_get_job_description_for_id", unexpected_call)
    monkeypatch.setattr(resume_routes, "parse_resume", unexpected_call)
    monkeypatch.setattr(resume_routes, "get_candidate_by_email", unexpected_call)

    fields = {
        "name": "Candidate",
        "email": "candidate@example.test",
        "phone": "+91 98765 43210",
    }
    fields[field] = value
    response = _resume_client(tmp_path).post(
        "/resume/upload",
        data=_valid_pdf_upload(**fields),
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == message
    assert list(tmp_path.iterdir()) == []


def test_unique_constraint_race_returns_the_same_generic_conflict(
    tmp_path, monkeypatch
):
    import pypdf
    import resume_analyzer

    monkeypatch.setattr(resume_routes, "_get_job_description_for_id", _active_job)
    monkeypatch.setattr(resume_routes, "get_candidate_by_email", lambda _email: None)
    monkeypatch.setattr(
        resume_routes,
        "parse_resume",
        lambda _path, _job: {
            "name": "Candidate",
            "email": "candidate@example.test",
            "phone": "+91 98765 43210",
            "skills": [],
            "experience": 0,
            "match_score": 50,
        },
    )

    class PdfReader:
        pages = []

        def __init__(self, _file):
            pass

    monkeypatch.setattr(pypdf, "PdfReader", PdfReader)
    monkeypatch.setattr(
        resume_analyzer.ResumeAnalyzer,
        "extract_resume_data",
        lambda _self, _text: None,
    )
    monkeypatch.setattr(
        resume_routes,
        "analyze_resume",
        lambda **_kwargs: {
            "pros": [],
            "cons": [],
            "overall_assessment": "",
            "recommendation": "Pending Review",
            "confidence_score": 0,
        },
    )

    def duplicate_insert(**_kwargs):
        raise DuplicateEmailError("private database detail")

    monkeypatch.setattr(
        resume_routes, "insert_candidate_application", duplicate_insert
    )

    response = _resume_client(tmp_path).post(
        "/resume/upload",
        data=_valid_pdf_upload(
            name="Candidate",
            email="candidate@example.test",
            phone="+91 98765 43210",
        ),
        content_type="multipart/form-data",
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "status": "error",
        "message": "An application already exists for this email address.",
    }
    assert list(tmp_path.iterdir()) == []


def test_successful_public_upload_returns_only_a_minimal_application_receipt(
    tmp_path, monkeypatch
):
    import pypdf
    import resume_analyzer

    monkeypatch.setattr(resume_routes, "_get_job_description_for_id", _active_job)
    monkeypatch.setattr(resume_routes, "get_candidate_by_email", lambda _email: None)
    monkeypatch.setattr(
        resume_routes,
        "parse_resume",
        lambda _path, _job: {
            "name": "Private Candidate",
            "email": "private@example.test",
            "phone": "+91 98765 43210",
            "skills": ["sensitive skill"],
            "experience": 7,
            "match_score": 91,
        },
    )

    class PdfReader:
        pages = []

        def __init__(self, _file):
            pass

    monkeypatch.setattr(pypdf, "PdfReader", PdfReader)
    monkeypatch.setattr(
        resume_analyzer.ResumeAnalyzer,
        "extract_resume_data",
        lambda _self, _text: None,
    )
    monkeypatch.setattr(
        resume_routes,
        "analyze_resume",
        lambda **_kwargs: {
            "pros": ["private strength"],
            "cons": ["private concern"],
            "overall_assessment": "private assessment",
            "recommendation": "private recommendation",
            "confidence_score": 99,
        },
    )
    monkeypatch.setattr(
        resume_routes,
        "insert_candidate_application",
        lambda **_kwargs: 123,
    )

    response = _resume_client(tmp_path).post(
        "/resume/upload",
        data=_valid_pdf_upload(
            name="Private Candidate",
            email="private@example.test",
            phone="+91 98765 43210",
        ),
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "success",
        "message": "Application submitted successfully",
        "data": {
            "candidate_id": 123,
            "application_status": "applied",
            "selected_job": {"id": 7, "title": "Engineer"},
        },
    }


def test_resume_upload_logging_does_not_include_candidate_pii():
    source = inspect.getsource(resume_routes.upload_resume)

    assert "Name: {name}" not in source
    assert "Email: {email}" not in source
