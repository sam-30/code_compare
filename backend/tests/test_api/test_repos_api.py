import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_repo_valid_path(client: AsyncClient, tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    resp = await client.post("/repos", json={
        "name": "my-repo",
        "path": str(tmp_path),
        "language": "python",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] > 0
    assert data["name"] == "my-repo"
    assert data["language"] == "python"
    assert data["status"] in ("pending", "ingesting", "ready")


@pytest.mark.asyncio
async def test_create_repo_invalid_path(client: AsyncClient):
    resp = await client.post("/repos", json={
        "name": "bad",
        "path": "/no/such/path/abc123",
        "language": "python",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_repo_invalid_language(client: AsyncClient, tmp_path):
    resp = await client.post("/repos", json={
        "name": "bad",
        "path": str(tmp_path),
        "language": "cobol",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_repo_not_found(client: AsyncClient):
    resp = await client.get("/repos/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_repos(client: AsyncClient, tmp_path):
    await client.post("/repos", json={
        "name": "repo-list-test",
        "path": str(tmp_path),
        "language": "python",
    })
    resp = await client.get("/repos")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    names = [r["name"] for r in resp.json()]
    assert "repo-list-test" in names


@pytest.mark.asyncio
async def test_delete_repo(client: AsyncClient, tmp_path):
    create = await client.post("/repos", json={
        "name": "delete-me",
        "path": str(tmp_path),
        "language": "python",
    })
    repo_id = create.json()["id"]

    resp = await client.delete(f"/repos/{repo_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/repos/{repo_id}")
    assert resp.status_code == 404
