"""Shared configuration for private runtime upload storage."""

from __future__ import annotations

import os
from pathlib import Path

from flask import current_app, has_app_context


BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_UPLOAD_ROOT = BACKEND_DIR / "uploads"


def get_upload_root(*, create: bool = False) -> Path:
    """Return the configured absolute upload root.

    Relative ``UPLOAD_FOLDER`` values are resolved from the backend directory,
    not from the process working directory, so every entry point behaves the
    same way.
    """

    configured = ""
    if has_app_context():
        configured = str(current_app.config.get("UPLOAD_FOLDER") or "").strip()
    if not configured:
        configured = os.environ.get("UPLOAD_FOLDER", "").strip()
    root = Path(configured).expanduser() if configured else DEFAULT_UPLOAD_ROOT
    if not root.is_absolute():
        root = BACKEND_DIR / root
    root = root.resolve()
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def get_upload_subdirectory(*parts: str, create: bool = False) -> Path:
    """Return a safe directory nested below the configured upload root."""

    if not parts or any(
        not isinstance(part, str)
        or not part
        or part in {".", ".."}
        or "/" in part
        or "\\" in part
        or "\x00" in part
        or Path(part).name != part
        for part in parts
    ):
        raise ValueError("Upload subdirectory parts must be simple path names")
    root = get_upload_root(create=create)
    directory = root.joinpath(*parts).resolve()
    if root != directory and root not in directory.parents:
        raise ValueError("Upload subdirectory escapes configured root")
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def is_within_upload_root(path) -> bool:
    """Return whether a resolved path belongs to the configured upload root."""

    try:
        candidate = Path(path).resolve()
        root = get_upload_root()
        return candidate == root or root in candidate.parents
    except (OSError, TypeError, ValueError):
        return False
