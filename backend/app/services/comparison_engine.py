"""
Orchestrates all enabled comparison methods and computes a weighted score.
"""
import json
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.comparison import Comparison, ComparisonMethodResult, ComparisonFileMatch, ComparisonStatus
from app.models.repository import Repository, RepositoryFile
from app.services.ingestion import collect_files
from app.services.methods.base import ComparisonMethod
from app.services.methods.file_hash import FileHashMethod
from app.services.methods.line_similarity import LineSimilarityMethod
from app.services.methods.function_names import FunctionNamesMethod
from app.services.methods.ast_structure import AstStructureMethod
from app.services.methods.token_ngram import TokenNgramMethod
from app.services.methods.call_graph import CallGraphMethod
from app.services.methods.import_analysis import ImportAnalysisMethod
from app.services.methods.identifier_similarity import IdentifierSimilarityMethod
from app.services.methods.complexity_profile import ComplexityProfileMethod

# Registry of all available methods (ordered by phase)
ALL_METHODS: list[ComparisonMethod] = [
    FileHashMethod(),
    LineSimilarityMethod(),
    FunctionNamesMethod(),
    AstStructureMethod(),
    TokenNgramMethod(),
    CallGraphMethod(),
    ImportAnalysisMethod(),
    IdentifierSimilarityMethod(),
    ComplexityProfileMethod(),
]


def _default_weights() -> dict[str, float]:
    total = sum(m.default_weight for m in ALL_METHODS)
    return {m.method_id: m.default_weight / total for m in ALL_METHODS}


def _redis_channel(comparison_id: int) -> str:
    return f"comparison:{comparison_id}:progress"


def _publish_event(comparison_id: int, event: dict) -> None:
    """Publish a progress event to Redis. Best-effort: swallows errors."""
    try:
        from redis import Redis
        from app.core.config import settings
        r = Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        r.publish(_redis_channel(comparison_id), json.dumps(event))
        r.close()
    except Exception:
        pass


async def run_comparison(comparison_id: int, db: AsyncSession) -> None:
    comparison = await db.get(Comparison, comparison_id)
    if comparison is None:
        return

    comparison.status = ComparisonStatus.running
    await db.flush()

    try:
        repo_a = await db.get(Repository, comparison.repo_a_id)
        repo_b = await db.get(Repository, comparison.repo_b_id)
        if repo_a is None or repo_b is None:
            raise ValueError("One or both repositories not found")

        root_a = Path(repo_a.path)
        root_b = Path(repo_b.path)
        files_a = collect_files(root_a, comparison.language)
        files_b = collect_files(root_b, comparison.language)

        config = comparison.config or {}
        weights = config.get("method_weights") or _default_weights()
        enabled = set(config.get("enabled_methods") or [m.method_id for m in ALL_METHODS])

        total_weight = 0.0
        weighted_sum = 0.0

        for method in ALL_METHODS:
            if method.method_id not in enabled:
                continue

            weight = weights.get(method.method_id, method.default_weight)
            start = time.monotonic()
            result = method.compare(root_a, files_a, root_b, files_b, comparison.language)
            duration_ms = int((time.monotonic() - start) * 1000)

            db.add(ComparisonMethodResult(
                comparison_id=comparison_id,
                method_id=result.method_id,
                score=result.score,
                weight=weight,
                details=result.details,
                duration_ms=duration_ms,
            ))

            for fm in result.file_matches:
                db.add(ComparisonFileMatch(
                    comparison_id=comparison_id,
                    file_a_path=fm.file_a,
                    file_b_path=fm.file_b,
                    similarity_score=fm.score,
                    method_id=result.method_id,
                    detail=fm.detail,
                ))

            weighted_sum += result.score * weight
            total_weight += weight

            _publish_event(comparison_id, {
                "type": "method",
                "method_id": result.method_id,
                "score": result.score,
                "weight": weight,
                "details": result.details,
                "duration_ms": duration_ms,
            })

        overall = weighted_sum / total_weight if total_weight > 0 else 0.0
        comparison.overall_score = round(overall, 4)
        comparison.status = ComparisonStatus.complete

        from datetime import datetime, timezone
        comparison.completed_at = datetime.now(timezone.utc)

        _publish_event(comparison_id, {
            "type": "done",
            "overall_score": comparison.overall_score,
        })

    except Exception as exc:
        comparison.status = ComparisonStatus.failed
        comparison.error_message = str(exc)[:2000]
        _publish_event(comparison_id, {
            "type": "error",
            "message": str(exc)[:500],
        })

    await db.commit()
