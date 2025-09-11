# app/tests/test_follows.py
import pytest

@pytest.mark.asyncio
async def test_follow_user(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}
    bob_id = seed_users["bob"]["id"]

    # первый follow
    response_follow = await client.post(f"/api/users/{bob_id}/follow", headers=headers)
    assert response_follow.status_code == 200
    assert response_follow.json()["result"] is True

    # повторный follow → AlreadyExists
    response_duplicate = await client.post(f"/api/users/{bob_id}/follow", headers=headers)
    assert response_duplicate.status_code in (400, 409)


@pytest.mark.asyncio
async def test_unfollow_user(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}
    bob_id = seed_users["bob"]["id"]

    # подписываемся, чтобы было что удалять
    await client.post(f"/api/users/{bob_id}/follow", headers=headers)

    # первый unfollow
    response_unfollow = await client.delete(f"/api/users/{bob_id}/follow", headers=headers)
    assert response_unfollow.status_code == 200
    assert response_unfollow.json()["result"] is True

    # проверка идемпотентно: тоже ок
    response_repeat_unfollow = await client.delete(f"/api/users/{bob_id}/follow", headers=headers)
    assert response_repeat_unfollow.status_code == 200