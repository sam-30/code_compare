"""Tests for comparison_engine config behavior."""
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository, RepositoryStatus


async def _make_ready_repo(db: AsyncSession, path, name: str, owner_id: int | None = None) -> int:
    path.mkdir(parents=True, exist_ok=True)
    (path / "m.py").write_text("def foo(): pass\ndef bar(): return 1\n")
    repo = Repository(
        name=name,
        path=str(path),
        language="python",
        status=RepositoryStatus.ready,
        file_count=1,
        owner_id=owner_id,
    )
    db.add(repo)
    await db.flush()
    return repo.id


async def _wait_for_completion(client: AsyncClient, cid: int) -> dict:
    for _ in range(20):
        await asyncio.sleep(0.5)
        resp = await client.get(f"/comparisons/{cid}")
        data = resp.json()
        if data["status"] in ("complete", "failed"):
            return data
    return data


@pytest.mark.asyncio
async def test_disabled_methods_excluded(client: AsyncClient, db_session: AsyncSession, tmp_path, test_user):
    """Only enabled methods should appear in method_results."""
    id_a = await _make_ready_repo(db_session, tmp_path / "dm_a", "dm_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "dm_b", "dm_b", owner_id=test_user.id)

    resp = await client.post("/comparisons", json={
        "repo_a_id": id_a,
        "repo_b_id": id_b,
        "language": "python",
        "config": {
            "enabled_methods": ["file_hash"],
            "method_weights": {"file_hash": 1.0},
        },
    })
    assert resp.status_code == 201
    data = await _wait_for_completion(client, resp.json()["id"])

    assert data["status"] == "complete"
    method_ids = {r["method_id"] for r in data["method_results"]}
    assert method_ids == {"file_hash"}


@pytest.mark.asyncio
async def test_custom_weights_produce_correct_average(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    """overall_score must match the weighted average of enabled method scores."""
    id_a = await _make_ready_repo(db_session, tmp_path / "cw_a", "cw_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "cw_b", "cw_b", owner_id=test_user.id)

    resp = await client.post("/comparisons", json={
        "repo_a_id": id_a,
        "repo_b_id": id_b,
        "language": "python",
        "config": {
            "enabled_methods": ["file_hash", "function_names"],
            "method_weights": {"file_hash": 0.7, "function_names": 0.3},
        },
    })
    assert resp.status_code == 201
    data = await _wait_for_completion(client, resp.json()["id"])

    assert data["status"] == "complete"
    results_by_id = {r["method_id"]: r for r in data["method_results"]}
    assert set(results_by_id.keys()) == {"file_hash", "function_names"}

    # Recompute expected weighted average
    weighted_sum = sum(r["score"] * r["weight"] for r in results_by_id.values())
    total_weight = sum(r["weight"] for r in results_by_id.values())
    expected = round(weighted_sum / total_weight, 4)
    assert abs(data["overall_score"] - expected) < 0.001


@pytest.mark.asyncio
async def test_config_id_loads_preset(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    """Passing config_id should load method_weights from the stored preset."""
    # Create a preset with only file_hash
    cfg_resp = await client.post("/configs", json={
        "name": "EngineTestPreset",
        "method_weights": {"file_hash": 1.0},
    })
    assert cfg_resp.status_code == 201
    config_id = cfg_resp.json()["id"]

    id_a = await _make_ready_repo(db_session, tmp_path / "ci_a", "ci_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "ci_b", "ci_b", owner_id=test_user.id)

    resp = await client.post("/comparisons", json={
        "repo_a_id": id_a,
        "repo_b_id": id_b,
        "language": "python",
        "config_id": config_id,
    })
    assert resp.status_code == 201
    data = await _wait_for_completion(client, resp.json()["id"])

    assert data["status"] == "complete"
    method_ids = {r["method_id"] for r in data["method_results"]}
    assert method_ids == {"file_hash"}


@pytest.mark.asyncio
async def test_config_id_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession, tmp_path, test_user
):
    id_a = await _make_ready_repo(db_session, tmp_path / "cnf_a", "cnf_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "cnf_b", "cnf_b", owner_id=test_user.id)

    resp = await client.post("/comparisons", json={
        "repo_a_id": id_a,
        "repo_b_id": id_b,
        "language": "python",
        "config_id": 999999,
    })
    assert resp.status_code == 404
