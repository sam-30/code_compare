"""Tests for zip-based repository ingestion."""
import asyncio
import io
import zipfile
import pytest
from httpx import AsyncClient


def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_zip_ingestion_extracts_and_indexes_files(client: AsyncClient):
    zip_bytes = _make_zip({
        "main.py": "def hello():\n    return 'hello'\n",
        "utils.py": "def add(a, b):\n    return a + b\n",
        "README.md": "# My Project\n",  # non-Python, should not be counted
    })

    resp = await client.post(
        "/repos/upload",
        data={"name": "ZipTest", "language": "python"},
        files={"file": ("repo.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 201
    repo_id = resp.json()["id"]
    assert resp.json()["source_type"] == "zip"

    for _ in range(20):
        await asyncio.sleep(0.5)
        data = (await client.get(f"/repos/{repo_id}")).json()
        if data["status"] in ("ready", "failed"):
            break

    assert data["status"] == "ready", f"Got: {data['status']}, error: {data.get('error_message')}"
    assert data["file_count"] == 2  # only .py files


@pytest.mark.asyncio
async def test_zip_with_nested_top_dir(client: AsyncClient):
    """Zip with a single top-level directory should unwrap it."""
    zip_bytes = _make_zip({
        "myproject/main.py": "x = 1\n",
        "myproject/sub/helper.py": "y = 2\n",
    })

    resp = await client.post(
        "/repos/upload",
        data={"name": "NestedZip", "language": "python"},
        files={"file": ("repo.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 201
    repo_id = resp.json()["id"]

    for _ in range(20):
        await asyncio.sleep(0.5)
        data = (await client.get(f"/repos/{repo_id}")).json()
        if data["status"] in ("ready", "failed"):
            break

    assert data["status"] == "ready"
    assert data["file_count"] == 2


@pytest.mark.asyncio
async def test_zip_invalid_language_rejected(client: AsyncClient):
    zip_bytes = _make_zip({"main.py": "x = 1\n"})
    resp = await client.post(
        "/repos/upload",
        data={"name": "Bad", "language": "ruby"},
        files={"file": ("repo.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_zip_invalid_zip_file_fails_gracefully(client: AsyncClient):
    resp = await client.post(
        "/repos/upload",
        data={"name": "BadZip", "language": "python"},
        files={"file": ("bad.zip", b"not a zip file", "application/zip")},
    )
    assert resp.status_code == 201
    repo_id = resp.json()["id"]

    for _ in range(20):
        await asyncio.sleep(0.5)
        data = (await client.get(f"/repos/{repo_id}")).json()
        if data["status"] in ("ready", "failed"):
            break

    assert data["status"] == "failed"
