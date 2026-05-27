"""Tests for the /comparisons/{id}/stream SSE endpoint."""
import asyncio
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comparison import Comparison, ComparisonMethodResult, ComparisonStatus
from app.models.repository import Repository, RepositoryStatus


async def _make_ready_repo(db: AsyncSession, path, name: str, owner_id: int | None = None) -> int:
    path.mkdir(parents=True, exist_ok=True)
    (path / "m.py").write_text("def foo(): pass\n")
    repo = Repository(
        name=name, path=str(path), language="python",
        status=RepositoryStatus.ready, file_count=1, owner_id=owner_id,
    )
    db.add(repo)
    await db.flush()
    return repo.id


async def _read_sse_events(client: AsyncClient, url: str, limit: int = 20) -> list[dict]:
    """Collect up to `limit` SSE events or until a done/error event."""
    events: list[dict] = []
    async with client.stream("GET", url) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                events.append(event)
                if event.get("type") in ("done", "error"):
                    break
            if len(events) >= limit:
                break
    return events


@pytest.mark.asyncio
async def test_stream_not_found(client: AsyncClient):
    resp = await client.get("/comparisons/999999/stream")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stream_already_complete_sends_stored_results(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    """For a completed comparison, SSE synthesizes events from stored method results."""
    id_a = await _make_ready_repo(db_session, tmp_path / "sse_a", "sse_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "sse_b", "sse_b", owner_id=test_user.id)

    # Create comparison, wait for it to complete
    create_resp = await client.post("/comparisons", json={
        "repo_a_id": id_a, "repo_b_id": id_b, "language": "python",
        "config": {"enabled_methods": ["file_hash"], "method_weights": {"file_hash": 1.0}},
    })
    assert create_resp.status_code == 201
    cid = create_resp.json()["id"]

    for _ in range(20):
        await asyncio.sleep(0.5)
        resp = await client.get(f"/comparisons/{cid}")
        if resp.json()["status"] in ("complete", "failed"):
            break

    assert resp.json()["status"] == "complete"

    # Now connect to SSE for the completed comparison
    events = await _read_sse_events(client, f"/comparisons/{cid}/stream")

    method_events = [e for e in events if e.get("type") == "method"]
    done_events = [e for e in events if e.get("type") == "done"]

    assert len(method_events) >= 1
    assert len(done_events) == 1
    assert "overall_score" in done_events[0]


@pytest.mark.asyncio
async def test_stream_publishes_method_events_live(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    """Running a comparison while connected to SSE receives live method events."""
    id_a = await _make_ready_repo(db_session, tmp_path / "live_a", "live_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "live_b", "live_b", owner_id=test_user.id)

    create_resp = await client.post("/comparisons", json={
        "repo_a_id": id_a, "repo_b_id": id_b, "language": "python",
        "config": {"enabled_methods": ["file_hash", "function_names"],
                   "method_weights": {"file_hash": 0.5, "function_names": 0.5}},
    })
    assert create_resp.status_code == 201
    cid = create_resp.json()["id"]

    # Wait for completion (background task runs immediately in tests)
    for _ in range(20):
        await asyncio.sleep(0.5)
        st = (await client.get(f"/comparisons/{cid}")).json()["status"]
        if st in ("complete", "failed"):
            break

    # Connect after completion — synthesized events must include both methods
    events = await _read_sse_events(client, f"/comparisons/{cid}/stream")

    method_ids = {e["method_id"] for e in events if e.get("type") == "method"}
    assert "file_hash" in method_ids
    assert "function_names" in method_ids

    done = [e for e in events if e.get("type") == "done"]
    assert len(done) == 1
    assert done[0]["overall_score"] is not None
