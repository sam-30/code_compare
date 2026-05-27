from datetime import datetime
from pydantic import BaseModel

from app.models.comparison import ComparisonStatus


class MethodResultOut(BaseModel):
    method_id: str
    score: float
    weight: float
    details: dict
    duration_ms: int

    model_config = {"from_attributes": True}


class FileMatchOut(BaseModel):
    file_a_path: str
    file_b_path: str
    similarity_score: float
    method_id: str
    detail: dict

    model_config = {"from_attributes": True}


class ComparisonCreate(BaseModel):
    repo_a_id: int
    repo_b_id: int
    language: str
    config: dict = {}
    config_id: int | None = None


class ComparisonOut(BaseModel):
    id: int
    repo_a_id: int
    repo_b_id: int
    language: str
    status: ComparisonStatus
    overall_score: float | None
    config: dict
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    method_results: list[MethodResultOut] = []
    file_matches: list[FileMatchOut] = []

    model_config = {"from_attributes": True}


class ComparisonListOut(BaseModel):
    id: int
    repo_a_id: int
    repo_b_id: int
    language: str
    status: ComparisonStatus
    overall_score: float | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
