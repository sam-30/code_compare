import hashlib
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository, RepositoryFile, RepositoryStatus

LANGUAGE_EXTENSIONS: dict[str, set[str]] = {
    "python": {".py"},
    "javascript": {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"},
}

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".mypy_cache",
    "node_modules", ".venv", "venv", "env", ".env",
    "dist", "build", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".ruff_cache",
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_lines(path: Path) -> int:
    try:
        return path.read_text(errors="replace").count("\n")
    except OSError:
        return 0


def collect_files(root: Path, language: str) -> list[Path]:
    extensions = LANGUAGE_EXTENSIONS.get(language, set())
    results: list[Path] = []
    for p in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix in extensions:
            results.append(p)
    return results


async def ingest_repository(repo_id: int, db: AsyncSession) -> None:
    result = await db.get(Repository, repo_id)
    if result is None:
        return

    repo = result
    repo.status = RepositoryStatus.ingesting
    await db.flush()

    try:
        root = Path(repo.path)
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Path does not exist or is not a directory: {repo.path}")

        files = collect_files(root, repo.language)

        for file_path in files:
            rel = str(file_path.relative_to(root))
            sha = _sha256(file_path)
            size = file_path.stat().st_size
            lines = _count_lines(file_path)
            db.add(RepositoryFile(
                repo_id=repo_id,
                relative_path=rel,
                sha256=sha,
                size_bytes=size,
                line_count=lines,
            ))

        repo.file_count = len(files)
        repo.status = RepositoryStatus.ready
    except Exception as exc:
        repo.status = RepositoryStatus.failed
        repo.error_message = str(exc)

    await db.commit()
