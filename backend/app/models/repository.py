import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SourceType(str, enum.Enum):
    local = "local"
    git = "git"
    zip = "zip"


class RepositoryStatus(str, enum.Enum):
    pending = "pending"
    ingesting = "ingesting"
    ready = "ready"
    failed = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.local)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RepositoryStatus] = mapped_column(Enum(RepositoryStatus), default=RepositoryStatus.pending)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    files: Mapped[list["RepositoryFile"]] = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repo_id: Mapped[int] = mapped_column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    line_count: Mapped[int] = mapped_column(Integer, default=0)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="files")
