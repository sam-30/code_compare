import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.comparison import Comparison
from app.models.config import ComparisonConfig
from app.models.repository import Repository, RepositoryStatus
from app.models.user import User
from app.schemas.comparison import ComparisonCreate, ComparisonListOut, ComparisonOut
from app.services.comparison_engine import run_comparison

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


async def _get_comparison_full(cid: int, db: AsyncSession) -> Comparison | None:
    result = await db.execute(
        select(Comparison)
        .options(
            selectinload(Comparison.method_results),
            selectinload(Comparison.file_matches),
        )
        .where(Comparison.id == cid)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=ComparisonOut, status_code=201)
async def create_comparison(
    payload: ComparisonCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for repo_id in (payload.repo_a_id, payload.repo_b_id):
        repo = await db.get(Repository, repo_id)
        if repo is None or repo.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found")
        if repo.status != RepositoryStatus.ready:
            raise HTTPException(
                status_code=422,
                detail=f"Repository {repo_id} is not ready (status: {repo.status})",
            )

    config = dict(payload.config)
    if payload.config_id is not None:
        db_config = await db.get(ComparisonConfig, payload.config_id)
        if db_config is None:
            raise HTTPException(status_code=404, detail=f"Config {payload.config_id} not found")
        config["method_weights"] = db_config.method_weights
        config.setdefault("enabled_methods", list(db_config.method_weights.keys()))

    comparison = Comparison(
        repo_a_id=payload.repo_a_id,
        repo_b_id=payload.repo_b_id,
        language=payload.language,
        config=config,
        owner_id=current_user.id,
    )
    db.add(comparison)
    await db.commit()

    background_tasks.add_task(run_comparison, comparison.id, db)

    return await _get_comparison_full(comparison.id, db)


@router.get("", response_model=list[ComparisonListOut])
async def list_comparisons(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comparison)
        .where(Comparison.owner_id == current_user.id)
        .order_by(Comparison.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{comparison_id}", response_model=ComparisonOut)
async def get_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_comparison_full(comparison_id, db)
    if c is None or c.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return c


@router.delete("/{comparison_id}", status_code=204)
async def delete_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(Comparison, comparison_id)
    if c is None or c.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Comparison not found")
    await db.delete(c)
    await db.commit()


async def _get_user_from_token(token: str, db: AsyncSession):
    """Decode a raw JWT token string and return the User (for SSE query-param auth)."""
    from jose import JWTError, jwt
    from app.core.config import settings
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
    return await db.get(User, user_id)


@router.get("/{comparison_id}/stream")
async def stream_comparison(
    comparison_id: int,
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Server-Sent Events endpoint that streams per-method progress."""
    from app.core.config import settings
    from app.models.comparison import ComparisonStatus as CS
    from app.services.comparison_engine import _redis_channel

    current_user = await _get_user_from_token(token or "", db) if token else None
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    c = await _get_comparison_full(comparison_id, db)
    if c is None or c.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Comparison not found")

    async def event_gen():
        # If already complete, synthesize events from stored results.
        if c.status in (CS.complete, CS.failed):
            for mr in c.method_results:
                yield _sse({"type": "method", "method_id": mr.method_id,
                             "score": mr.score, "weight": mr.weight,
                             "details": mr.details, "duration_ms": mr.duration_ms})
            if c.status == CS.complete:
                yield _sse({"type": "done", "overall_score": c.overall_score})
            else:
                yield _sse({"type": "error", "message": c.error_message or "failed"})
            return

        # Subscribe first, then check state — avoids race with engine publishing.
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        pubsub = r.pubsub()
        channel = _redis_channel(comparison_id)
        await pubsub.subscribe(channel)

        try:
            deadline = asyncio.get_event_loop().time() + 300  # 5 min timeout
            async for message in pubsub.listen():
                if asyncio.get_event_loop().time() > deadline:
                    break
                if message["type"] != "message":
                    continue
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                yield _sse(json.loads(data))
                event = json.loads(data)
                if event.get("type") in ("done", "error"):
                    break
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await r.aclose()

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.get("/{comparison_id}/export")
async def export_comparison(
    comparison_id: int,
    format: str = Query(default="json", pattern="^(json|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export a completed comparison as JSON or PDF."""
    from app.services.report import build_json_report, build_pdf_bytes

    c = await _get_comparison_full(comparison_id, db)
    if c is None or c.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Comparison not found")

    if format == "json":
        import json as _json
        body = _json.dumps(build_json_report(c), indent=2).encode()
        return Response(
            content=body,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="comparison_{comparison_id}.json"'
            },
        )

    # PDF
    try:
        pdf_bytes = build_pdf_bytes(c)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="comparison_{comparison_id}.pdf"'
        },
    )
