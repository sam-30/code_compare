"""Extract a zip archive and ingest its contents."""
import zipfile
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.repository import Repository, RepositoryStatus
from app.services.ingestion import ingest_repository


async def extract_and_ingest(repo_id: int, zip_bytes: bytes, db: AsyncSession) -> None:
    repo = await db.get(Repository, repo_id)
    if repo is None:
        return

    extract_dir = Path(settings.upload_dir) / f"zip_{repo_id}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(extract_dir)

        # If the zip has a single top-level directory, use it as root
        children = list(extract_dir.iterdir())
        if len(children) == 1 and children[0].is_dir():
            extract_dir = children[0]

        repo.path = str(extract_dir)
        await db.flush()

        await ingest_repository(repo_id, db)
    except zipfile.BadZipFile as exc:
        repo.status = RepositoryStatus.failed
        repo.error_message = f"Invalid zip file: {exc}"
        await db.commit()
    except Exception as exc:
        repo.status = RepositoryStatus.failed
        repo.error_message = str(exc)[:1000]
        await db.commit()
