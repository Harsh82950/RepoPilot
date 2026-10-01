from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from git import Repo
from git.exc import GitCommandError

from app.core.config import settings


class InvalidGitHubUrlError(ValueError):
    pass


class RepositoryCloneError(RuntimeError):
    pass


@dataclass
class RepoCloneResult:
    name: str
    local_path: str
    default_branch: str | None


def validate_github_url(repo_url: str) -> None:
    parsed_url = urlparse(repo_url)

    if parsed_url.scheme not in {"http", "https"}:
        raise InvalidGitHubUrlError(
            "Repository URL must use HTTP or HTTPS."
        )

    if parsed_url.netloc.lower() not in {
        "github.com",
        "www.github.com",
    }:
        raise InvalidGitHubUrlError(
            "Only GitHub repository URLs are supported."
        )

    path_parts = [
        part
        for part in parsed_url.path.strip("/").split("/")
        if part
    ]

    if len(path_parts) != 2:
        raise InvalidGitHubUrlError(
            "Invalid GitHub repository URL."
        )


def get_repository_name(repo_url: str) -> str:
    parsed_url = urlparse(repo_url)

    repository_name = Path(
        parsed_url.path.rstrip("/")
    ).name

    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]

    return repository_name


def clone_github_repo(
    repo_url: str,
    repo_id: str,
) -> RepoCloneResult:
    validate_github_url(repo_url)

    repository_name = get_repository_name(repo_url)

    storage_root = Path(
        settings.REPO_STORAGE_PATH
    ).resolve()

    repository_path = storage_root / repo_id

    storage_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    if repository_path.exists():
        raise RepositoryCloneError(
            "Repository storage path already exists."
        )

    try:
        repo = Repo.clone_from(
            repo_url,
            repository_path,
            depth=1,
        )

        default_branch = None

        if repo.active_branch:
            default_branch = repo.active_branch.name

        return RepoCloneResult(
            name=repository_name,
            local_path=str(repository_path),
            default_branch=default_branch,
        )

    except GitCommandError as exc:
        if repository_path.exists():
            import shutil

            shutil.rmtree(
                repository_path,
                ignore_errors=True,
            )

        raise RepositoryCloneError(
            "Failed to clone GitHub repository."
        ) from exc