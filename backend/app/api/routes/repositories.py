import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.constants import (
    REPO_STATUS_FAILED,
    REPO_STATUS_PROCESSING,
    REPO_STATUS_READY,
    SOURCE_TYPE_GITHUB,
    SOURCE_TYPE_ZIP,
)
from app.db.session import get_db
from app.models.repository import Repository
from app.models.repository_summary import RepositorySummary
from app.models.repository_file import RepositoryFile
from app.schemas.repository import (
    GitHubRepositoryCreate,
    RepositoryFileResponse,
    RepositoryResponse,
    RepositorySummaryResponse,
)
from app.services.repo_ingestion.file_scanner import scan_repository
from app.services.repo_ingestion.github_loader import (
    InvalidGitHubUrlError,
    RepositoryCloneError,
    clone_github_repo,
)

from app.services.repo_ingestion.zip_loader import (
    InvalidZipFileError,
    ZipExtractionError,
    extract_zip_repository,
)

from app.services.repo_analysis.tech_stack_classifier import (
    classify_tech_stack,
)

from app.services.repo_analysis.repository_analyzer import (
    analyze_repository,
)

from app.services.chunking.chunking_service import (
    chunk_repository,
)

router = APIRouter(
    prefix="/api/repositories",
    tags=["repositories"],
)


@router.post(
    "/github",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_github_repository(
    payload: GitHubRepositoryCreate,
    db: Session = Depends(get_db),
):
    repository = Repository(
        name="pending",
        source_type=SOURCE_TYPE_GITHUB,
        source_url=str(payload.repo_url),
        status=REPO_STATUS_PROCESSING,
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    try:
        clone_result = clone_github_repo(
            repo_url=str(payload.repo_url),
            repo_id=str(repository.id),
        )

        repository.name = clone_result.name
        repository.local_path = clone_result.local_path
        repository.default_branch = clone_result.default_branch

        scanned_files = scan_repository(
            clone_result.local_path
        )

        repository_files = [
            RepositoryFile(
                repository_id=repository.id,
                file_path=scanned_file.relative_path,
                file_type=scanned_file.file_type,
                language=scanned_file.language,
                size_bytes=scanned_file.size_bytes,
                file_hash=scanned_file.file_hash,
            )
            for scanned_file in scanned_files
        ]

        db.add_all(repository_files)
        db.flush()

        analyze_repository(
            db=db,
            repository=repository,
            scanned_files=scanned_files,
)
        
        db.flush()

        chunk_repository(
            db=db,
            repository=repository,
      )
        repository.status = REPO_STATUS_READY

        db.commit()
        db.refresh(repository)

        return repository

    except InvalidGitHubUrlError as exc:
        db.rollback()

        repository = db.get(
            Repository,
            repository.id,
        )

        if repository is not None:
            repository.status = REPO_STATUS_FAILED
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RepositoryCloneError as exc:
        db.rollback()

        repository = db.get(
            Repository,
            repository.id,
        )

        if repository is not None:
            repository.status = REPO_STATUS_FAILED
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        repository = db.get(
            Repository,
            repository.id,
        )

        if repository is not None:
            repository.status = REPO_STATUS_FAILED
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository processing failed.",
        ) from exc

@router.post(
    "/upload",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_repository(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    repository = Repository(
        name=file.filename or "pending",
        source_type=SOURCE_TYPE_ZIP,
        source_url=None,
        status=REPO_STATUS_PROCESSING,
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    repository_id = repository.id

    try:
        extraction_result = extract_zip_repository(
            upload_file=file,
            repo_id=str(repository_id),
        )

        repository.name = extraction_result.name
        repository.local_path = extraction_result.local_path
        repository.default_branch = None

        scanned_files = scan_repository(
            extraction_result.local_path
        )

        repository_files = [
            RepositoryFile(
                repository_id=repository.id,
                file_path=scanned_file.relative_path,
                file_type=scanned_file.file_type,
                language=scanned_file.language,
                size_bytes=scanned_file.size_bytes,
                file_hash=scanned_file.file_hash,
            )
            for scanned_file in scanned_files
        ]

       
    
        db.add_all(repository_files)

        analyze_repository(
            db=db,
            repository=repository,
            scanned_files=scanned_files,
         )
        
        db.flush()

        chunk_repository(
            db=db,
            repository=repository,
      )

        repository.status = REPO_STATUS_READY

        db.commit()
        db.refresh(repository)

        return repository

    except InvalidZipFileError as exc:
        db.rollback()

        failed_repository = db.get(
            Repository,
            repository_id,
        )

        if failed_repository is not None:
            failed_repository.status = REPO_STATUS_FAILED
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except ZipExtractionError as exc:
        db.rollback()

        failed_repository = db.get(
            Repository,
            repository_id,
        )

        if failed_repository is not None:
            failed_repository.status = REPO_STATUS_FAILED
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        failed_repository = db.get(
            Repository,
            repository_id,
        )

        if failed_repository is not None:
            failed_repository.status = REPO_STATUS_FAILED
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository processing failed.",
        ) from exc

@router.get(
    "/{repo_id}",
    response_model=RepositoryResponse,
)
def get_repository(
    repo_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repository = db.get(
        Repository,
        repo_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    return repository


@router.get(
    "/{repo_id}/files",
    response_model=list[RepositoryFileResponse],
)
def get_repository_files(
    repo_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repository = db.get(
        Repository,
        repo_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    repository_files = (
        db.query(RepositoryFile)
        .filter(
            RepositoryFile.repository_id == repo_id
        )
        .order_by(RepositoryFile.file_path)
        .all()
    )

    return repository_files

@router.get(
    "/{repo_id}/summary",
    response_model=RepositorySummaryResponse,
)
def get_repository_summary(
    repo_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repository = db.get(
        Repository,
        repo_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    repository_summary = (
        db.query(RepositorySummary)
        .filter(
            RepositorySummary.repository_id == repo_id
        )
        .first()
    )

    if repository_summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository summary not found.",
        )

    return repository_summary