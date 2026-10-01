import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class GitHubRepositoryCreate(BaseModel):
    repo_url: HttpUrl


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    source_url: str | None
    local_path: str | None
    default_branch: str | None
    primary_language: str | None
    framework: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class RepositoryFileResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    file_path: str
    file_type: str
    language: str | None
    size_bytes: int
    module_type: str | None
    summary: str | None
    file_hash: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class RepositorySummaryResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    tech_stack: dict
    architecture_summary: str | None
    important_modules: list
    probable_entrypoints: list
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )    