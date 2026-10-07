"""The demo reset must only ever delete entries that live inside the upload root."""

import importlib
import os
import sys
from pathlib import Path

import pytest

DATABASE_DIR = Path(__file__).resolve().parents[2] / "database"


@pytest.fixture
def seed_demo(monkeypatch, tmp_path):
    # Importing the seeder sets DEMO_MODE; monkeypatch restores the environment afterwards.
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    (tmp_path / "uploads").mkdir()
    monkeypatch.syspath_prepend(str(DATABASE_DIR))
    sys.modules.pop("seed_demo", None)
    return importlib.import_module("seed_demo")


def test_upload_entry_only_accepts_paths_inside_the_upload_root(seed_demo, tmp_path):
    root = (tmp_path / "uploads").resolve()
    outside = tmp_path / "elsewhere.docx"

    assert seed_demo.upload_entry(str(root / "resume.docx")) == root / "resume.docx"
    assert seed_demo.upload_entry("resume.docx") == root / "resume.docx"
    assert seed_demo.upload_entry("/uploads/violations/shot.png") == root / "violations" / "shot.png"
    assert seed_demo.upload_entry(str(outside)) is None
    assert seed_demo.upload_entry("../escape.docx") is None
    assert seed_demo.upload_entry(None) is None


def test_upload_entry_judges_a_symlink_by_where_it_sits(seed_demo, tmp_path):
    root = (tmp_path / "uploads").resolve()
    (root / "real.docx").write_text("resume")
    link = tmp_path / "link.docx"
    try:
        os.symlink(root / "real.docx", link)
    except OSError:
        pytest.skip("symlinks are not available on this platform")

    assert seed_demo.upload_entry(str(link)) is None
