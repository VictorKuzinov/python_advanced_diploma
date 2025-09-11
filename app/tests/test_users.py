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
async def test_me_unauthorized(client):
    # нет api-key
    r = await client.get("/api/users/me")
    # должен сработать обработчик EntityNotFound/Unauthorized по твоей логике
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_me_invalid_api_key(client):
    # несуществующий api-key
    headers = {"api-key": "wrong-key"}
    r = await client.get("/api/users/me", headers=headers)
    assert r.status_code == 401
    data = r.json()
    assert data["detail"] == "Invalid or missing api-key"

@pytest.mark.asyncio
async def test_get_user_by_id_ok(client, seed_users):
    alice_id = seed_users["alice"]["id"]
    r = await client.get(f"/api/users/{alice_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["result"] is True
    assert data["user"]["id"] == alice_id
    assert data["user"]["username"] == "alice"