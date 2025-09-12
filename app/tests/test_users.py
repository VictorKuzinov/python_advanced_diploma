# app/tests/test_users.py
import pytest


@pytest.mark.asyncio
async def test_me_ok(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}
    r = await client.get("/api/users/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["result"] is True
    assert data["user"]["username"] == "alice"
    assert "followers" in data["user"]
    assert "following" in data["user"]


@pytest.mark.asyncio
async def test_me_unauthorized_missing_key(client):
    # нет api-key → 401 + Missing api-key
    r = await client.get("/api/users/me")
    assert r.status_code == 401
    data = r.json()
    assert data["detail"] == "Missing api-key"


@pytest.mark.asyncio
async def test_me_unauthorized_invalid_key(client):
    # неверный api-key → 401 + Invalid api-key
    headers = {"api-key": "wrong-key"}
    r = await client.get("/api/users/me", headers=headers)
    assert r.status_code == 401
    data = r.json()
    assert data["detail"] == "Invalid api-key"


@pytest.mark.asyncio
async def test_get_user_by_id_ok(client, seed_users):
    alice_id = seed_users["alice"]["id"]
    r = await client.get(f"/api/users/{alice_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["result"] is True
    assert data["user"]["id"] == alice_id
    assert data["user"]["username"] == "alice"
