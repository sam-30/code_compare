"""Tests for Phase 10: User Authentication."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_unauthenticated_client(db_session: AsyncSession) -> AsyncClient:
    """Return a client with no get_current_user override (real auth enforced)."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Intentionally do NOT override get_current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

async def test_register_creates_user_and_returns_token(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        resp = await c.post("/auth/register", json={
            "email": "alice@example.com",
            "password": "password123",
        })
    app.dependency_overrides.clear()

    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


async def test_register_duplicate_email_returns_409(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        await c.post("/auth/register", json={
            "email": "duplicate@example.com",
            "password": "password123",
        })
        resp = await c.post("/auth/register", json={
            "email": "duplicate@example.com",
            "password": "differentpass",
        })
    app.dependency_overrides.clear()

    assert resp.status_code == 409


async def test_register_short_password_returns_422(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        resp = await c.post("/auth/register", json={
            "email": "shortpass@example.com",
            "password": "short",
        })
    app.dependency_overrides.clear()

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_returns_token(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        await c.post("/auth/register", json={
            "email": "bob@example.com",
            "password": "mypassword1",
        })
        resp = await c.post("/auth/login", json={
            "email": "bob@example.com",
            "password": "mypassword1",
        })
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password_returns_401(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        await c.post("/auth/register", json={
            "email": "carol@example.com",
            "password": "correctpass1",
        })
        resp = await c.post("/auth/login", json={
            "email": "carol@example.com",
            "password": "wrongpassword",
        })
    app.dependency_overrides.clear()

    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        resp = await c.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "doesntmatter",
        })
    app.dependency_overrides.clear()

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

async def test_me_returns_current_user(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        reg = await c.post("/auth/register", json={
            "email": "dave@example.com",
            "password": "davepassword",
        })
        token = reg.json()["access_token"]
        resp = await c.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "dave@example.com"
    assert "id" in body
    assert "created_at" in body


async def test_me_without_token_returns_401(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        resp = await c.get("/auth/me")
    app.dependency_overrides.clear()

    assert resp.status_code == 401


async def test_me_with_invalid_token_returns_401(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        resp = await c.get("/auth/me", headers={"Authorization": "Bearer not.a.token"})
    app.dependency_overrides.clear()

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Protected route access without token
# ---------------------------------------------------------------------------

async def test_unauthenticated_cannot_list_repos(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        resp = await c.get("/repos")
    app.dependency_overrides.clear()

    assert resp.status_code == 401


async def test_unauthenticated_cannot_list_comparisons(db_session):
    async with await _make_unauthenticated_client(db_session) as c:
        resp = await c.get("/comparisons")
    app.dependency_overrides.clear()

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# User isolation: User A cannot see User B's resources
# ---------------------------------------------------------------------------

async def test_user_isolation_repos(db_session, tmp_path):
    """User A's repo is invisible to User B."""
    repo_dir = tmp_path / "myrepo"
    repo_dir.mkdir()
    (repo_dir / "hello.py").write_text("print('hello')\n")

    async with await _make_unauthenticated_client(db_session) as c:
        # Register two users
        reg_a = await c.post("/auth/register", json={
            "email": "usera_iso@example.com", "password": "passwordA1"
        })
        token_a = reg_a.json()["access_token"]

        reg_b = await c.post("/auth/register", json={
            "email": "userb_iso@example.com", "password": "passwordB1"
        })
        token_b = reg_b.json()["access_token"]

        # User A creates a repo
        create_resp = await c.post(
            "/repos",
            json={"name": "A's repo", "path": str(repo_dir), "language": "python"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert create_resp.status_code == 201
        repo_id = create_resp.json()["id"]

        # User B cannot see it in list
        list_resp = await c.get("/repos", headers={"Authorization": f"Bearer {token_b}"})
        assert list_resp.status_code == 200
        ids = [r["id"] for r in list_resp.json()]
        assert repo_id not in ids

        # User B cannot fetch it directly
        get_resp = await c.get(
            f"/repos/{repo_id}", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert get_resp.status_code == 404

    app.dependency_overrides.clear()


async def test_user_isolation_comparisons(db_session, tmp_path):
    """User A's comparison is invisible to User B."""
    from app.models.user import User as UserModel
    from app.models.repository import Repository, SourceType, RepositoryStatus
    from app.models.comparison import Comparison, ComparisonStatus

    # Create two users and two ready repos owned by user_a directly in DB
    user_a = UserModel(email="compare_a@example.com", hashed_password="x")
    user_b = UserModel(email="compare_b@example.com", hashed_password="x")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    repo_a = Repository(
        name="ra", path="/tmp", language="python",
        source_type=SourceType.local, status=RepositoryStatus.ready, owner_id=user_a.id
    )
    repo_b = Repository(
        name="rb", path="/tmp", language="python",
        source_type=SourceType.local, status=RepositoryStatus.ready, owner_id=user_a.id
    )
    db_session.add_all([repo_a, repo_b])
    await db_session.flush()

    comparison = Comparison(
        repo_a_id=repo_a.id, repo_b_id=repo_b.id,
        language="python", config={}, owner_id=user_a.id,
        status=ComparisonStatus.complete, overall_score=0.5,
    )
    db_session.add(comparison)
    await db_session.flush()

    async with await _make_unauthenticated_client(db_session) as c:
        # Register user_b for a real token
        reg_b = await c.post("/auth/register", json={
            "email": "compare_b_token@example.com", "password": "passwordB2"
        })
        token_b = reg_b.json()["access_token"]

        list_resp = await c.get("/comparisons", headers={"Authorization": f"Bearer {token_b}"})
        assert list_resp.status_code == 200
        ids = [r["id"] for r in list_resp.json()]
        assert comparison.id not in ids

        get_resp = await c.get(
            f"/comparisons/{comparison.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert get_resp.status_code == 404

    app.dependency_overrides.clear()
