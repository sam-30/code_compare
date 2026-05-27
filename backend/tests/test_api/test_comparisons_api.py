import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository, RepositoryStatus


async def _make_ready_repo(
    db: AsyncSession, tmp_path, name: str,
    language: str = "python", owner_id: int | None = None,
) -> int:
    """Create a repository row in 'ready' status (bypasses background task)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / f"{name}.py").write_text("def foo(): pass\ndef bar(): return 1\n")
    repo = Repository(
        name=name,
        path=str(tmp_path),
        language=language,
        status=RepositoryStatus.ready,
        file_count=1,
        owner_id=owner_id,
    )
    db.add(repo)
    await db.flush()
    return repo.id


@pytest.mark.asyncio
async def test_create_comparison(client: AsyncClient, db_session: AsyncSession, tmp_path, test_user):
    id_a = await _make_ready_repo(db_session, tmp_path / "a", "repo_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "b", "repo_b", owner_id=test_user.id)

    resp = await client.post("/comparisons", json={
        "repo_a_id": id_a,
        "repo_b_id": id_b,
        "language": "python",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] > 0
    assert data["status"] in ("pending", "running", "complete")


@pytest.mark.asyncio
async def test_create_comparison_repo_not_found(client: AsyncClient):
    resp = await client.post("/comparisons", json={
        "repo_a_id": 999999,
        "repo_b_id": 999998,
        "language": "python",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_comparison_not_found(client: AsyncClient):
    resp = await client.get("/comparisons/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_comparisons(client: AsyncClient, db_session: AsyncSession, tmp_path, test_user):
    (tmp_path / "la").mkdir()
    (tmp_path / "lb").mkdir()
    id_a = await _make_ready_repo(db_session, tmp_path / "la", "list_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, tmp_path / "lb", "list_b", owner_id=test_user.id)

    await client.post("/comparisons", json={
        "repo_a_id": id_a,
        "repo_b_id": id_b,
        "language": "python",
    })

    resp = await client.get("/comparisons")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_comparison_runs_and_scores(client: AsyncClient, db_session: AsyncSession, tmp_path, test_user):
    """Submit a comparison against near-identical repos and verify a score is produced."""
    dir_a = tmp_path / "score_a"
    dir_b = tmp_path / "score_b"
    dir_a.mkdir()
    dir_b.mkdir()

    code = "def alpha(): return 1\ndef beta(): return 2\n"
    (dir_a / "m.py").write_text(code)
    (dir_b / "m.py").write_text(code)

    id_a = await _make_ready_repo(db_session, dir_a, "score_repo_a", owner_id=test_user.id)
    id_b = await _make_ready_repo(db_session, dir_b, "score_repo_b", owner_id=test_user.id)

    create_resp = await client.post("/comparisons", json={
        "repo_a_id": id_a,
        "repo_b_id": id_b,
        "language": "python",
    })
    assert create_resp.status_code == 201
    cid = create_resp.json()["id"]

    # Poll up to 10s for completion
    for _ in range(20):
        await asyncio.sleep(0.5)
        resp = await client.get(f"/comparisons/{cid}")
        data = resp.json()
        if data["status"] in ("complete", "failed"):
            break

    assert data["status"] == "complete"
    assert data["overall_score"] is not None
    assert data["overall_score"] >= 0.0
    assert len(data["method_results"]) > 0
