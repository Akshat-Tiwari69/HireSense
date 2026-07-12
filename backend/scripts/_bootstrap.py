"""Shared path setup for directly executed backend maintenance scripts."""

from pathlib import Path
import sys


def add_backend_to_path() -> None:
    backend_dir = str(Path(__file__).resolve().parent.parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
