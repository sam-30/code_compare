"""Clone a remote git repository and ingest it."""
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.repository import Repository, RepositoryStatus
from app.services.ingestion import ingest_repository


async def clone_and_ingest(repo_id: int, url: str, db: AsyncSession) -> None:
    repo = await db.get(Repository, repo_id)
    if repo is None:
        return

    clone_dir = Path(settings.upload_dir) / f"git_{repo_id}"
    clone_dir.mkdir(parents=True, exist_ok=True)

    try:
        from git import Repo as GitRepo, GitCommandError
        GitRepo.clone_from(url, str(clone_dir), depth=1)

        # Update path to cloned directory
        repo.path = str(clone_dir)
        await db.flush()

        await ingest_repository(repo_id, db)
    except Exception as exc:
        repo.status = RepositoryStatus.failed
        repo.error_message = str(exc)[:1000]
        await db.commit()
