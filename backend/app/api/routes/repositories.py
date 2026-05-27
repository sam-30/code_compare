import io
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.repository import Repository, SourceType
from app.models.user import User
from app.schemas.repository import RepositoryCreate, RepositoryListOut, RepositoryOut
from app.services.ingestion import ingest_repository
from app.services.git_ingestion import clone_and_ingest
from app.services.zip_ingestion import extract_and_ingest

router = APIRouter(prefix="/repos", tags=["repositories"])


async def _get_repo_with_files(repo_id: int, db: AsyncSession) -> Repository | None:
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.files))
        .where(Repository.id == repo_id)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=RepositoryOut, status_code=201)
async def create_repository(
    payload: RepositoryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.source_type == "local":
        path = Path(payload.path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(
                status_code=422,
                detail=f"Path does not exist or is not a directory: {payload.path}",
            )
        repo = Repository(
            name=payload.name,
            path=str(path.resolve()),
            language=payload.language,
            source_type=SourceType.local,
            owner_id=current_user.id,
        )
        db.add(repo)
        await db.commit()
        background_tasks.add_task(ingest_repository, repo.id, db)

    elif payload.source_type == "git":
        if not payload.url:
            raise HTTPException(status_code=422, detail="url is required for git source_type")
        repo = Repository(
            name=payload.name,
            path="",  # will be set after clone
            language=payload.language,
            source_type=SourceType.git,
            owner_id=current_user.id,
        )
        db.add(repo)
        await db.commit()
        background_tasks.add_task(clone_and_ingest, repo.id, payload.url, db)

    else:
        raise HTTPException(status_code=422, detail=f"Invalid source_type: {payload.source_type}")

    return await _get_repo_with_files(repo.id, db)


@router.post("/upload", response_model=RepositoryOut, status_code=201)
async def upload_repository(
    background_tasks: BackgroundTasks,
    name: str = File(...),
    language: str = File(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a zip archive as a repository."""
    if language not in ("python", "javascript"):
        raise HTTPException(status_code=422, detail="language must be python or javascript")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    repo = Repository(
        name=name,
        path="",  # will be set after extraction
        language=language,
        source_type=SourceType.zip,
        owner_id=current_user.id,
    )
    db.add(repo)
    await db.commit()
    background_tasks.add_task(extract_and_ingest, repo.id, content, db)

    return await _get_repo_with_files(repo.id, db)


@router.get("", response_model=list[RepositoryListOut])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository)
        .where(Repository.owner_id == current_user.id)
        .order_by(Repository.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{repo_id}", response_model=RepositoryOut)
async def get_repository(
    repo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await _get_repo_with_files(repo_id, db)
    if repo is None or repo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None or repo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")
    await db.delete(repo)
    await db.commit()
