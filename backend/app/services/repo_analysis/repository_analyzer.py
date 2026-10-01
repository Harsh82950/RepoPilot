from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.repository_summary import RepositorySummary
from app.services.repo_analysis.repository_mapper import (
    map_repository,
)
from app.services.repo_analysis.tech_stack_classifier import (
    classify_tech_stack,
)
from app.services.repo_ingestion.file_scanner import ScannedFile


def analyze_repository(
    db: Session,
    repository: Repository,
    scanned_files: list[ScannedFile],
) -> RepositorySummary:
    if repository.local_path is None:
        raise ValueError(
            "Repository local path is required for analysis."
        )

    classification_result = classify_tech_stack(
        repository_path=repository.local_path,
        scanned_files=scanned_files,
    )

    repository_map = map_repository(
        scanned_files=scanned_files,
    )

    repository.primary_language = (
        classification_result.primary_language
    )

    repository.framework = (
        classification_result.primary_framework
    )

    repository_summary = RepositorySummary(
        repository_id=repository.id,
        tech_stack=classification_result.tech_stack,
        architecture_summary=None,
        important_modules=repository_map.important_modules,
        probable_entrypoints=repository_map.probable_entrypoints,
    )

    db.add(repository_summary)

    update_repository_file_module_types(
        db=db,
        repository=repository,
        file_module_types=repository_map.file_module_types,
    )

    return repository_summary


def update_repository_file_module_types(
    db: Session,
    repository: Repository,
    file_module_types: dict[str, str],
) -> None:
    repository_files = (
        db.query(RepositoryFile)
        .filter(
            RepositoryFile.repository_id == repository.id
        )
        .all()
    )

    for repository_file in repository_files:
        module_type = file_module_types.get(
            repository_file.file_path
        )

        if module_type is not None:
            repository_file.module_type = module_type