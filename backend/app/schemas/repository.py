from datetime import datetime
from pydantic import BaseModel, Field

from app.models.repository import RepositoryStatus, SourceType


class RepositoryFileOut(BaseModel):
    id: int
    relative_path: str
    sha256: str
    size_bytes: int
    line_count: int

    model_config = {"from_attributes": True}


class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(default="")
    language: str = Field(..., pattern="^(python|javascript)$")
    source_type: str = Field(default="local", pattern="^(local|git)$")
    url: str = Field(default="")


class RepositoryOut(BaseModel):
    id: int
    name: str
    path: str
    source_type: SourceType
    language: str
    status: RepositoryStatus
    file_count: int
    error_message: str | None
    created_at: datetime
    files: list[RepositoryFileOut] = []

    model_config = {"from_attributes": True}


class RepositoryListOut(BaseModel):
    id: int
    name: str
    language: str
    status: RepositoryStatus
    file_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
