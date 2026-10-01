import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


class InvalidZipFileError(ValueError):
    pass


class ZipExtractionError(RuntimeError):
    pass


@dataclass
class ZipExtractionResult:
    name: str
    local_path: str


def validate_zip_file(upload_file: UploadFile) -> None:
    if upload_file.filename is None:
        raise InvalidZipFileError(
            "Uploaded file must have a filename."
        )

    if not upload_file.filename.lower().endswith(".zip"):
        raise InvalidZipFileError(
            "Only ZIP files are supported."
        )


def is_safe_member(
    destination: Path,
    member_name: str,
) -> bool:
    member_path = (
        destination / member_name
    ).resolve()

    try:
        member_path.relative_to(destination)
        return True
    except ValueError:
        return False


def extract_zip_repository(
    upload_file: UploadFile,
    repo_id: str,
) -> ZipExtractionResult:
    validate_zip_file(upload_file)

    storage_root = Path(
        settings.REPO_STORAGE_PATH
    ).resolve()

    repository_path = storage_root / repo_id

    storage_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    if repository_path.exists():
        raise ZipExtractionError(
            "Repository storage path already exists."
        )

    repository_path.mkdir(
        parents=True,
        exist_ok=False,
    )

    temporary_zip_path = (
        storage_root / f"{repo_id}.zip"
    )

    try:
        with temporary_zip_path.open("wb") as zip_file:
            shutil.copyfileobj(
                upload_file.file,
                zip_file,
            )

        if not zipfile.is_zipfile(
            temporary_zip_path
        ):
            raise InvalidZipFileError(
                "Uploaded file is not a valid ZIP archive."
            )

        with zipfile.ZipFile(
            temporary_zip_path,
            "r",
        ) as zip_archive:
            for member in zip_archive.infolist():
                if not is_safe_member(
                    repository_path,
                    member.filename,
                ):
                    raise InvalidZipFileError(
                        "ZIP archive contains an unsafe path."
                    )

            zip_archive.extractall(
                repository_path
            )

        repository_root = find_repository_root(
            repository_path
        )

        repository_name = Path(
            upload_file.filename
        ).stem

        return ZipExtractionResult(
            name=repository_name,
            local_path=str(repository_root),
        )

    except (
        InvalidZipFileError,
        zipfile.BadZipFile,
    ):
        shutil.rmtree(
            repository_path,
            ignore_errors=True,
        )

        raise

    except Exception as exc:
        shutil.rmtree(
            repository_path,
            ignore_errors=True,
        )

        raise ZipExtractionError(
            "Failed to extract ZIP repository."
        ) from exc

    finally:
        temporary_zip_path.unlink(
            missing_ok=True
        )


def find_repository_root(
    extraction_path: Path,
) -> Path:
    entries = [
        entry
        for entry in extraction_path.iterdir()
        if entry.name != "__MACOSX"
    ]

    if (
        len(entries) == 1
        and entries[0].is_dir()
    ):
        return entries[0]

    return extraction_path