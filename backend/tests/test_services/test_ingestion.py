import hashlib
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository, RepositoryFile, RepositoryStatus
from app.services.ingestion import _sha256, collect_files, ingest_repository

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SAMPLE_PYTHON_DIR = FIXTURES_DIR / "sample_python"


def test_sha256_deterministic(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("hello world\n")
    h1 = _sha256(f)
    h2 = _sha256(f)
    assert h1 == h2
    assert len(h1) == 64


def test_sha256_correct(tmp_path):
    f = tmp_path / "test.py"
    content = b"hello world\n"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert _sha256(f) == expected


def test_collect_files_python(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    (tmp_path / "b.js").write_text("var x=1")
    (tmp_path / "README.md").write_text("# readme")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "c.py").write_text("cached")

    files = collect_files(tmp_path, "python")
    names = {f.name for f in files}
    assert "a.py" in names
    assert "b.js" not in names
    assert "c.py" not in names


def test_collect_files_javascript(tmp_path):
    (tmp_path / "app.ts").write_text("const x = 1;")
    (tmp_path / "comp.tsx").write_text("export default () => null;")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("module.exports={}")
    (tmp_path / "util.py").write_text("pass")

    files = collect_files(tmp_path, "javascript")
    names = {f.name for f in files}
    assert "app.ts" in names
    assert "comp.tsx" in names
    assert "pkg.js" not in names
    assert "util.py" not in names


def test_collect_files_sample_fixtures():
    files = collect_files(SAMPLE_PYTHON_DIR, "python")
    names = {f.name for f in files}
    assert "module_a.py" in names
    assert "module_b.py" in names
    assert len(files) == 2


@pytest.mark.asyncio
async def test_ingest_repository_success(db_session: AsyncSession, tmp_path):
    (tmp_path / "main.py").write_text("def hello(): pass\n")
    (tmp_path / "utils.py").write_text("x = 1\n")
    (tmp_path / "ignore.txt").write_text("not code")

    repo = Repository(name="test-repo", path=str(tmp_path), language="python")
    db_session.add(repo)
    await db_session.flush()

    await ingest_repository(repo.id, db_session)
    await db_session.refresh(repo)

    assert repo.status == RepositoryStatus.ready
    assert repo.file_count == 2

    result = await db_session.execute(
        select(RepositoryFile).where(RepositoryFile.repo_id == repo.id)
    )
    files = result.scalars().all()
    assert len(files) == 2
    paths = {f.relative_path for f in files}
    assert "main.py" in paths
    assert "utils.py" in paths
    for f in files:
        assert len(f.sha256) == 64
        assert f.size_bytes > 0
        assert f.line_count >= 0


@pytest.mark.asyncio
async def test_ingest_repository_invalid_path(db_session: AsyncSession):
    repo = Repository(name="bad-repo", path="/nonexistent/path/xyz", language="python")
    db_session.add(repo)
    await db_session.flush()

    await ingest_repository(repo.id, db_session)
    await db_session.refresh(repo)

    assert repo.status == RepositoryStatus.failed
    assert repo.error_message is not None


@pytest.mark.asyncio
async def test_ingest_sha256_values(db_session: AsyncSession, tmp_path):
    content = b"def foo(): pass\n"
    f = tmp_path / "foo.py"
    f.write_bytes(content)
    expected_sha = hashlib.sha256(content).hexdigest()

    repo = Repository(name="sha-repo", path=str(tmp_path), language="python")
    db_session.add(repo)
    await db_session.flush()
    await ingest_repository(repo.id, db_session)

    result = await db_session.execute(
        select(RepositoryFile).where(RepositoryFile.repo_id == repo.id)
    )
    file_row = result.scalar_one()
    assert file_row.sha256 == expected_sha
