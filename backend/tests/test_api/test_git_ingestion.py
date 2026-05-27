"""Tests for git-based repository ingestion."""
import asyncio
import subprocess
import pytest
from httpx import AsyncClient
from pathlib import Path


def _make_local_git_repo(base: Path) -> str:
    """Create a minimal local git repo and return a file:// URL."""
    base.mkdir(parents=True)
    (base / "main.py").write_text("def hello():\n    return 'hello'\n")
    (base / "utils.py").write_text("def add(a, b):\n    return a + b\n")
    subprocess.run(["git", "init"], cwd=base, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=base, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=base, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=base, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=base, check=True, capture_output=True)
    return f"file://{base}"


@pytest.mark.asyncio
async def test_git_ingestion_clones_and_indexes_files(client: AsyncClient, tmp_path):
    git_url = _make_local_git_repo(tmp_path / "source_repo")

    resp = await client.post("/repos", json={
        "name": "GitTest",
        "language": "python",
        "source_type": "git",
        "url": git_url,
    })
    assert resp.status_code == 201
    repo_id = resp.json()["id"]
    assert resp.json()["source_type"] == "git"

    # Poll until ready
    for _ in range(20):
        await asyncio.sleep(0.5)
        data = (await client.get(f"/repos/{repo_id}")).json()
        if data["status"] in ("ready", "failed"):
            break

    assert data["status"] == "ready", f"Got status: {data['status']}, error: {data.get('error_message')}"
    assert data["file_count"] == 2  # main.py + utils.py


@pytest.mark.asyncio
async def test_git_ingestion_missing_url_rejected(client: AsyncClient):
    resp = await client.post("/repos", json={
        "name": "BadGit",
        "language": "python",
        "source_type": "git",
        "url": "",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_git_ingestion_invalid_url_fails_gracefully(client: AsyncClient, tmp_path):
    resp = await client.post("/repos", json={
        "name": "BadUrl",
        "language": "python",
        "source_type": "git",
        "url": "file:///nonexistent/path/to/repo",
    })
    assert resp.status_code == 201
    repo_id = resp.json()["id"]

    for _ in range(20):
        await asyncio.sleep(0.5)
        data = (await client.get(f"/repos/{repo_id}")).json()
        if data["status"] in ("ready", "failed"):
            break

    assert data["status"] == "failed"
