"""Tests for /configs CRUD endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_config(client: AsyncClient):
    resp = await client.post("/configs", json={
        "name": "Equal Weights",
        "description": "All methods equal",
        "method_weights": {"file_hash": 1.0, "line_similarity": 1.0, "function_names": 1.0},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Equal Weights"
    assert data["description"] == "All methods equal"
    assert data["id"] > 0
    assert not data["is_default"]


@pytest.mark.asyncio
async def test_create_config_normalizes_weights(client: AsyncClient):
    resp = await client.post("/configs", json={
        "name": "Norm Test",
        "method_weights": {"file_hash": 2.0, "line_similarity": 2.0},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert abs(data["method_weights"]["file_hash"] - 0.5) < 0.001
    assert abs(data["method_weights"]["line_similarity"] - 0.5) < 0.001
    total = sum(data["method_weights"].values())
    assert abs(total - 1.0) < 0.001


@pytest.mark.asyncio
async def test_create_config_empty_weights_rejected(client: AsyncClient):
    resp = await client.post("/configs", json={
        "name": "Bad Config",
        "method_weights": {},
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_config_negative_weight_rejected(client: AsyncClient):
    resp = await client.post("/configs", json={
        "name": "Bad Config",
        "method_weights": {"file_hash": -1.0},
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_config(client: AsyncClient):
    create_resp = await client.post("/configs", json={
        "name": "Get Test",
        "method_weights": {"file_hash": 1.0},
    })
    assert create_resp.status_code == 201
    cid = create_resp.json()["id"]

    resp = await client.get(f"/configs/{cid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cid
    assert resp.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_config_not_found(client: AsyncClient):
    resp = await client.get("/configs/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_configs(client: AsyncClient):
    await client.post("/configs", json={"name": "List A", "method_weights": {"file_hash": 1.0}})
    await client.post("/configs", json={"name": "List B", "method_weights": {"file_hash": 1.0}})

    resp = await client.get("/configs")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "List A" in names
    assert "List B" in names


@pytest.mark.asyncio
async def test_update_config(client: AsyncClient):
    create_resp = await client.post("/configs", json={
        "name": "Before Update",
        "method_weights": {"file_hash": 1.0},
    })
    cid = create_resp.json()["id"]

    resp = await client.put(f"/configs/{cid}", json={
        "name": "After Update",
        "method_weights": {"file_hash": 0.6, "line_similarity": 0.4},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "After Update"
    total = sum(data["method_weights"].values())
    assert abs(total - 1.0) < 0.001


@pytest.mark.asyncio
async def test_update_config_not_found(client: AsyncClient):
    resp = await client.put("/configs/999999", json={"name": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_config(client: AsyncClient):
    create_resp = await client.post("/configs", json={
        "name": "To Delete",
        "method_weights": {"file_hash": 1.0},
    })
    cid = create_resp.json()["id"]

    del_resp = await client.delete(f"/configs/{cid}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/configs/{cid}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_config_not_found(client: AsyncClient):
    resp = await client.delete("/configs/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_only_one_default_config(client: AsyncClient):
    """Setting a new default clears the previous one."""
    resp_a = await client.post("/configs", json={
        "name": "Default A", "method_weights": {"file_hash": 1.0}, "is_default": True
    })
    resp_b = await client.post("/configs", json={
        "name": "Default B", "method_weights": {"file_hash": 1.0}, "is_default": True
    })
    id_a = resp_a.json()["id"]

    config_a = (await client.get(f"/configs/{id_a}")).json()
    assert not config_a["is_default"]
    assert resp_b.json()["is_default"]
