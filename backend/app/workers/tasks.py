import asyncio

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="run_comparison")
def run_comparison(self, comparison_id: int) -> dict:
    from app.core.database import AsyncSessionLocal
    from app.services.comparison_engine import run_comparison as _run

    async def _execute():
        async with AsyncSessionLocal() as db:
            await _run(comparison_id, db)

    asyncio.run(_execute())
    return {"comparison_id": comparison_id, "status": "done"}
