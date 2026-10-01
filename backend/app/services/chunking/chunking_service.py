from pathlib import Path

from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.repository_chunk import RepositoryChunk
from app.models.repository_file import RepositoryFile
from app.services.chunking.code_chunker import (
    chunk_text_by_lines,
)


CHUNKABLE_FILE_TYPES = {
    "code",
    "doc",
}


EXCLUDED_PATH_PARTS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
}


EXCLUDED_FILE_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "migration_lock.toml",
}


MAX_FILE_SIZE_BYTES = 500_000


def should_chunk_file(
    repository_file: RepositoryFile,
) -> bool:
    """
    Decide whether a repository file contains useful content
    for semantic retrieval.
    """

    if (
        repository_file.file_type
        not in CHUNKABLE_FILE_TYPES
    ):
        return False

    if (
        repository_file.size_bytes
        > MAX_FILE_SIZE_BYTES
    ):
        return False

    file_path = Path(
        repository_file.file_path
    )

    if (
        file_path.name
        in EXCLUDED_FILE_NAMES
    ):
        return False

    path_parts = {
        part.lower()
        for part in file_path.parts
    }

    if path_parts.intersection(
        EXCLUDED_PATH_PARTS
    ):
        return False

    # Prisma schema is useful, but generated migration history
    # usually adds noise to semantic retrieval.
    if (
        "prisma" in path_parts
        and "migrations" in path_parts
    ):
        return False

    return True


def read_text_file(
    file_path: Path,
) -> str | None:
    """
    Read a UTF-8 text file safely.

    Unreadable or non-UTF-8 files are skipped instead of causing
    the whole repository chunking process to fail.
    """

    try:
        return file_path.read_text(
            encoding="utf-8"
        )

    except (
        OSError,
        UnicodeDecodeError,
    ):
        return None


def build_chunk_content(
    repository_file: RepositoryFile,
    raw_content: str,
    start_line: int,
    end_line: int,
) -> str:
    """
    Add repository metadata to the chunk before it is stored.

    This metadata will later become useful context for embedding
    and semantic retrieval.
    """

    metadata_lines = [
        f"File: {repository_file.file_path}",
        (
            "Language: "
            f"{repository_file.language or 'Unknown'}"
        ),
        (
            "Module type: "
            f"{repository_file.module_type or 'Unknown'}"
        ),
        f"Lines: {start_line}-{end_line}",
    ]

    metadata = "\n".join(
        metadata_lines
    )

    return (
        f"{metadata}\n\n"
        f"{raw_content}"
    )


def delete_existing_chunks(
    db: Session,
    repository_files: list[RepositoryFile],
) -> None:
    """
    Delete existing chunks for the repository files before
    rebuilding them.

    This makes repository chunking idempotent and prevents
    duplicate chunks when analysis is retried.
    """

    repository_file_ids = [
        repository_file.id
        for repository_file in repository_files
    ]

    if not repository_file_ids:
        return

    (
        db.query(RepositoryChunk)
        .filter(
            RepositoryChunk.repository_file_id.in_(
                repository_file_ids
            )
        )
        .delete(
            synchronize_session=False
        )
    )

    db.flush()


def chunk_repository(
    db: Session,
    repository: Repository,
) -> int:
    """
    Chunk all eligible files belonging to a repository and
    persist the resulting chunks.

    Returns the total number of chunks created.
    """

    if repository.local_path is None:
        raise ValueError(
            "Repository local path is required for chunking."
        )

    repository_root = Path(
        repository.local_path
    ).resolve()

    repository_files = (
        db.query(RepositoryFile)
        .filter(
            RepositoryFile.repository_id
            == repository.id
        )
        .order_by(
            RepositoryFile.file_path
        )
        .all()
    )

    delete_existing_chunks(
        db=db,
        repository_files=repository_files,
    )

    created_chunk_count = 0

    for repository_file in repository_files:
        if not should_chunk_file(
            repository_file
        ):
            continue

        absolute_file_path = (
            repository_root
            / repository_file.file_path
        ).resolve()

        # Defense-in-depth:
        # never allow a stored path to escape the repository root.
        try:
            absolute_file_path.relative_to(
                repository_root
            )
        except ValueError:
            continue

        if not absolute_file_path.is_file():
            continue

        content = read_text_file(
            absolute_file_path
        )

        if content is None:
            continue

        code_chunks = chunk_text_by_lines(
            content
        )

        for chunk_index, code_chunk in enumerate(
            code_chunks
        ):
            chunk_content = build_chunk_content(
                repository_file=repository_file,
                raw_content=code_chunk.content,
                start_line=code_chunk.start_line,
                end_line=code_chunk.end_line,
            )

            repository_chunk = RepositoryChunk(
                repository_id=repository.id,
                repository_file_id=repository_file.id,
                chunk_index=chunk_index,
                content=chunk_content,
                start_line=code_chunk.start_line,
                end_line=code_chunk.end_line,
            )

            db.add(
                repository_chunk
            )

            created_chunk_count += 1

    db.flush()

    return created_chunk_count