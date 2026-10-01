from pathlib import Path

from app.core.config import settings
from app.core.constants import (
    IGNORED_DIRECTORIES,
    IGNORED_FILE_EXTENSIONS,
)


IGNORED_FILE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
}

ALLOWED_SPECIAL_FILES = {
    "Dockerfile",
    "Makefile",
    ".env.example",
}


def should_ignore_directory(directory_name: str) -> bool:
    return directory_name in IGNORED_DIRECTORIES


def should_ignore_file(file_path: Path) -> bool:
    if file_path.name in ALLOWED_SPECIAL_FILES:
        return False

    if file_path.name in IGNORED_FILE_NAMES:
        return True

    if file_path.suffix.lower() in IGNORED_FILE_EXTENSIONS:
        return True

    try:
        if file_path.stat().st_size > settings.MAX_FILE_SIZE_BYTES:
            return True
    except OSError:
        return True

    return False