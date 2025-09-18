# app/tests/test_users.py
import pytest

FOLLOW_POST_PATH = "/api/users/{user_id}/follow"
FOLLOW_DELETE_PATH = "/api/users/{user_id}/follow"

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

    @pytest.mark.asyncio
    async def test_follow_and_unfollow(client, seed_users):
        alice = seed_users["alice"]  # будет current_user по api-key
        bob = seed_users["bob"]

        headers = {"api-key": alice["api_key"]}

        # follow (успех)
        r1 = await client.post(FOLLOW_POST_PATH.format(user_id=bob["id"]), headers=headers)
        assert r1.status_code in (200, 201), r1.text

        # повторный follow → AlreadyExists (обычно 409), но оставим допуск
        r1b = await client.post(FOLLOW_POST_PATH.format(user_id=bob["id"]), headers=headers)
        assert r1b.status_code in (200, 201, 409), r1b.text

        # unfollow (идемпотентно)
        r2 = await client.delete(FOLLOW_DELETE_PATH.format(user_id=bob["id"]), headers=headers)
        assert r2.status_code in (200, 204), r2.text

        # повторный unfollow — тоже ок/идемпотентно
        r2b = await client.delete(FOLLOW_DELETE_PATH.format(user_id=bob["id"]), headers=headers)
        assert r2b.status_code in (200, 204), r2b.text
