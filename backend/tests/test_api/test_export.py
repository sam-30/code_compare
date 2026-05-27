"""Tests for the comparison export endpoints."""
import asyncio
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository, RepositoryStatus


async def _make_ready_repo(db: AsyncSession, path, name: str, owner_id: int | None = None) -> int:
    path.mkdir(parents=True, exist_ok=True)
    (path / "m.py").write_text(
        "import os\ndef foo(x):\n    if x: return x\n    return 0\n"
    )
    repo = Repository(
        name=name, path=str(path), language="python",
        status=RepositoryStatus.ready, file_count=1, owner_id=owner_id,
    )
    db.add(repo)
    await db.flush()
    return repo.id


async def _run_comparison(client: AsyncClient, id_a: int, id_b: int) -> int:
    resp = await client.post("/comparisons", json={
        "repo_a_id": id_a, "repo_b_id": id_b, "language": "python",
        "config": {"enabled_methods": ["file_hash", "function_names"],
                   "method_weights": {"file_hash": 0.6, "function_names": 0.4}},
    })
    assert resp.status_code == 201
    cid = resp.json()["id"]
    for _ in range(20):
        await asyncio.sleep(0.5)
        data = (await client.get(f"/comparisons/{cid}")).json()
        if data["status"] in ("complete", "failed"):
            break
    assert data["status"] == "complete"
    return cid


@pytest.mark.asyncio
async def test_export_json_contains_all_fields(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    id_a = await _make_ready_repo(db_session, tmp_path / "ex_a", "ex_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "ex_b", "ex_b", owner_id=test_user.id)
    cid = await _run_comparison(client, id_a, id_b)

    resp = await client.get(f"/comparisons/{cid}/export?format=json")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    assert "attachment" in resp.headers.get("content-disposition", "")

    data = json.loads(resp.content)
    assert data["id"] == cid
    assert "overall_score" in data
    assert "method_results" in data
    assert isinstance(data["method_results"], list)
    assert len(data["method_results"]) == 2  # file_hash + function_names
    assert "file_matches" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_export_json_method_results_structure(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    id_a = await _make_ready_repo(db_session, tmp_path / "ex2_a", "ex2_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "ex2_b", "ex2_b", owner_id=test_user.id)
    cid = await _run_comparison(client, id_a, id_b)

    resp = await client.get(f"/comparisons/{cid}/export?format=json")
    data = json.loads(resp.content)

    for mr in data["method_results"]:
        assert "method_id" in mr
        assert "score" in mr
        assert "weight" in mr
        assert "details" in mr
        assert "duration_ms" in mr


@pytest.mark.asyncio
async def test_export_pdf_returns_valid_bytes(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    id_a = await _make_ready_repo(db_session, tmp_path / "pdf_a", "pdf_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "pdf_b", "pdf_b", owner_id=test_user.id)
    cid = await _run_comparison(client, id_a, id_b)

    resp = await client.get(f"/comparisons/{cid}/export?format=pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers.get("content-disposition", "")
    # PDF magic bytes: %PDF
    assert resp.content[:4] == b"%PDF"
    assert len(resp.content) > 1000  # non-trivial PDF


@pytest.mark.asyncio
async def test_export_invalid_format_rejected(client: AsyncClient, db_session: AsyncSession, tmp_path, test_user):
    id_a = await _make_ready_repo(db_session, tmp_path / "fmt_a", "fmt_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "fmt_b", "fmt_b", owner_id=test_user.id)
    cid = await _run_comparison(client, id_a, id_b)

    resp = await client.get(f"/comparisons/{cid}/export?format=csv")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_export_not_found(client: AsyncClient):
    resp = await client.get("/comparisons/999999/export?format=json")
    assert resp.status_code == 404
