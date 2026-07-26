"""Shared backend test configuration."""

from pathlib import Path
import os
import sys

import pytest


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ["APP_ENV"] = "test"
os.environ["ALLOW_INSECURE_DEV_SECRET"] = "true"


@pytest.fixture(autouse=True)
def skip_live_user_version_check_for_unit_tests():
    """Unit JWTs are synthetic; production checks current database user state."""
    app_module = sys.modules.get("app")
    if app_module is None:
        yield
        return

    previous = app_module.app.config.get("JWT_SKIP_USER_VERSION_CHECK", False)
    app_module.app.config["JWT_SKIP_USER_VERSION_CHECK"] = True
    try:
        yield
    finally:
        app_module.app.config["JWT_SKIP_USER_VERSION_CHECK"] = previous
