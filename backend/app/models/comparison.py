import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ComparisonStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class Comparison(Base):
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repo_a_id: Mapped[int] = mapped_column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    repo_b_id: Mapped[int] = mapped_column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ComparisonStatus] = mapped_column(Enum(ComparisonStatus), default=ComparisonStatus.pending)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    method_results: Mapped[list["ComparisonMethodResult"]] = relationship(
        "ComparisonMethodResult", back_populates="comparison", cascade="all, delete-orphan"
    )
    file_matches: Mapped[list["ComparisonFileMatch"]] = relationship(
        "ComparisonFileMatch", back_populates="comparison", cascade="all, delete-orphan"
    )


class ComparisonMethodResult(Base):
    __tablename__ = "comparison_method_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparison_id: Mapped[int] = mapped_column(Integer, ForeignKey("comparisons.id", ondelete="CASCADE"), nullable=False)
    method_id: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    comparison: Mapped["Comparison"] = relationship("Comparison", back_populates="method_results")


class ComparisonFileMatch(Base):
    __tablename__ = "comparison_file_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparison_id: Mapped[int] = mapped_column(Integer, ForeignKey("comparisons.id", ondelete="CASCADE"), nullable=False)
    file_a_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_b_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    method_id: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    comparison: Mapped["Comparison"] = relationship("Comparison", back_populates="file_matches")
