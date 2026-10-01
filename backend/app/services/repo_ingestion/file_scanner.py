import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from app.services.repo_ingestion.ignore_rules import (
    should_ignore_directory,
    should_ignore_file,
)


@dataclass
class ScannedFile:
    relative_path: str
    absolute_path: str
    file_type: str
    language: str | None
    size_bytes: int
    file_hash: str


LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".sql": "SQL",
    ".prisma": "Prisma",
    ".sh": "Shell",
    ".ps1": "PowerShell",
}


CONFIG_FILE_NAMES = {
    "package.json",
    "tsconfig.json",
    "pyproject.toml",
    "requirements.txt",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    "Makefile",
    ".env.example",
    "alembic.ini",
}


DOC_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
}


TEST_PATH_MARKERS = {
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
}


def detect_language(file_path: Path) -> str | None:
    return LANGUAGE_BY_EXTENSION.get(
        file_path.suffix.lower()
    )


def detect_file_type(
    file_path: Path,
    relative_path: Path,
) -> str:
    path_parts = {
        part.lower()
        for part in relative_path.parts
    }

    if path_parts.intersection(TEST_PATH_MARKERS):
        return "test"

    if file_path.name in CONFIG_FILE_NAMES:
        return "config"

    if file_path.suffix.lower() in DOC_EXTENSIONS:
        return "doc"

    if detect_language(file_path) is not None:
        return "code"

    return "other"


def calculate_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def scan_repository(repo_path: str) -> list[ScannedFile]:
    repository_root = Path(repo_path).resolve()

    if not repository_root.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: {repository_root}"
        )

    if not repository_root.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {repository_root}"
        )

    scanned_files: list[ScannedFile] = []

    for current_root, directories, files in os.walk(
        repository_root
    ):
        directories[:] = [
            directory
            for directory in directories
            if not should_ignore_directory(directory)
        ]

        current_path = Path(current_root)

        for file_name in files:
            file_path = current_path / file_name

            if should_ignore_file(file_path):
                continue

            try:
                relative_path = file_path.relative_to(
                    repository_root
                )

                scanned_file = ScannedFile(
                    relative_path=relative_path.as_posix(),
                    absolute_path=str(file_path),
                    file_type=detect_file_type(
                        file_path,
                        relative_path,
                    ),
                    language=detect_language(file_path),
                    size_bytes=file_path.stat().st_size,
                    file_hash=calculate_file_hash(file_path),
                )

                scanned_files.append(scanned_file)

            except OSError:
                continue

    return scanned_files