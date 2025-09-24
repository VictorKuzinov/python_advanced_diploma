# app/tests/test_users.py
"""
Тесты /api/users*:
- /api/users/me: ok, 401 без/с неверным api-key
- /api/users/{id}: ok, 404 not found
- follow/unfollow: happy-path, запрет self-follow, дубль follow → 409,
  unfollow идемпотентен.
"""

import pytest

USERS_PATH = "/api/users"
ME_PATH = "/api/users/me"
FOLLOW_POST = "/api/users/{user_id}/follow"
FOLLOW_DEL = "/api/users/{user_id}/follow"


# ---------- /api/users/me ----------


@pytest.mark.asyncio
async def test_me_ok(client, seed_users):
    """/me возвращает профиль текущего пользователя по api-key."""
    headers = {"api-key": seed_users["alice"]["api_key"]}
    r = await client.get(ME_PATH, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["result"] is True
    assert data["user"]["name"] == "alice"
    assert "followers" in data["user"]
    assert "following" in data["user"]


@pytest.mark.asyncio
async def test_me_unauthorized_missing_key(client):
    """/me без api-key → 401 + 'Missing api-key'."""
    r = await client.get(ME_PATH)
    assert r.status_code == 401
    data = r.json()
    assert data["detail"] == "Missing api-key"


@pytest.mark.asyncio
async def test_me_unauthorized_invalid_key(client):
    """/me с неверным api-key → 401 + 'Invalid api-key'."""
    r = await client.get(ME_PATH, headers={"api-key": "wrong-key"})
    assert r.status_code == 401
    data = r.json()
    assert data["detail"] == "Invalid api-key"


# ---------- /api/users/{id} ----------


@pytest.mark.asyncio
async def test_get_user_by_id_ok(client, seed_users):
    """GET /users/{id} возвращает профиль с followers/following."""
    alice_id = seed_users["alice"]["id"]
    r = await client.get(f"{USERS_PATH}/{alice_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["result"] is True
    assert data["user"]["id"] == alice_id
    assert data["user"]["name"] == "alice"
    assert "followers" in data["user"]
    assert "following" in data["user"]


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(client, seed_users):
    """GET /users/{id} для несуществующего пользователя → 404."""
    r = await client.get(f"{USERS_PATH}/999999")
    assert r.status_code == 404
    data = r.json()
    assert data["result"] is False
    assert data["error_type"] == "EntityNotFound"


# ---------- follow / unfollow ----------


@pytest.mark.asyncio
async def test_follow_success_and_duplicate_conflict(client, seed_users):
    """
    POST /users/{id}/follow:
    - первый follow — 200/201
    - повторный follow — 409 AlreadyExists
    """
    alice = seed_users["alice"]
    bob = seed_users["bob"]
    h = {"api-key": alice["api_key"]}

    r1 = await client.post(FOLLOW_POST.format(user_id=bob["id"]), headers=h)
    assert r1.status_code in (200, 201), r1.text
    assert r1.json()["result"] is True

    r2 = await client.post(FOLLOW_POST.format(user_id=bob["id"]), headers=h)
    assert r2.status_code == 409, r2.text
    data = r2.json()
    assert data["result"] is False
    assert data["error_type"] == "AlreadyExists"


@pytest.mark.asyncio
async def test_follow_self_forbidden(client, seed_users):
    """Нельзя подписаться на себя → 403 ForbiddenAction."""
    alice = seed_users["alice"]
    h = {"api-key": alice["api_key"]}

    r = await client.post(FOLLOW_POST.format(user_id=alice["id"]), headers=h)
    assert r.status_code == 403, r.text
    data = r.json()
    assert data["result"] is False
    assert data["error_type"] == "ForbiddenAction"


@pytest.mark.asyncio
async def test_follow_nonexistent_user_not_found(client, seed_users):
    """Подписка на несуществующего пользователя → 404 EntityNotFound."""
    alice = seed_users["alice"]
    h = {"api-key": alice["api_key"]}

    r = await client.post(FOLLOW_POST.format(user_id=999999), headers=h)
    assert r.status_code == 404, r.text
    data = r.json()
    assert data["result"] is False
    assert data["error_type"] == "EntityNotFound"


@pytest.mark.asyncio
async def test_unfollow_idempotent(client, seed_users):
    """DELETE /users/{id}/follow идемпотентен: 200 даже
    если уже не подписан."""
    alice = seed_users["alice"]
    bob = seed_users["bob"]
    h = {"api-key": alice["api_key"]}

    # подготовка: подпишемся
    _ = await client.post(FOLLOW_POST.format(user_id=bob["id"]), headers=h)

    # первый unfollow
    r1 = await client.delete(FOLLOW_DEL.format(user_id=bob["id"]), headers=h)
    assert r1.status_code == 200, r1.text
    assert r1.json()["result"] is True

    # повторный unfollow (идемпотентно)
    r2 = await client.delete(FOLLOW_DEL.format(user_id=bob["id"]), headers=h)
    assert r2.status_code == 200, r2.text
    assert r2.json()["result"] is True
