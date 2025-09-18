# app/tests/test_likes.py
import pytest


async def _create_tweet(client, *, author_api_key: str, text: str) -> int:
    """Хелпер: создаёт твит и возвращает его id."""
    headers = {"api-key": author_api_key}
    payload = {"tweet_data": text, "tweet_media_ids": None}
    resp = await client.post("/api/tweets", headers=headers, json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["tweet_id"]


@pytest.mark.asyncio
async def test_like_then_duplicate_returns_error(client, seed_users):
    """Поставить лайк и проверить, что повторный лайк даёт 400/409."""
    alice_api_key = seed_users["alice"]["api_key"]  # автор твита
    bob_api_key = seed_users["bob"]["api_key"]  # ставит лайк

    tweet_id = await _create_tweet(client, author_api_key=alice_api_key, text="like me")

    # первый лайк — ок
    like_resp = await client.post(f"/api/tweets/{tweet_id}/likes", headers={"api-key": bob_api_key})
    assert like_resp.status_code == 200
    assert like_resp.json()["result"] is True

    # повторный лайк — конфликт (наш хендлер может вернуть 400 или 409)
    duplicate_like_resp = await client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": bob_api_key}
    )
    assert duplicate_like_resp.status_code in (400, 409), duplicate_like_resp.text


@pytest.mark.asyncio
async def test_unlike_is_idempotent(client, seed_users):
    """Снятие лайка дважды подряд возвращает 200 оба раза (идемпотентно)."""
    alice_api_key = seed_users["alice"]["api_key"]
    bob_api_key = seed_users["bob"]["api_key"]

    tweet_id = await _create_tweet(client, author_api_key=alice_api_key, text="unlike me")

    # предварительно поставим лайк
    first_like = await client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": bob_api_key}
    )
    assert first_like.status_code == 200

    # первый анлайк — ок
    first_unlike = await client.delete(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": bob_api_key}
    )
    assert first_unlike.status_code == 200
    assert first_unlike.json()["result"] is True

    # второй анлайк — тоже ок (идемпотентно)
    second_unlike = await client.delete(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": bob_api_key}
    )
    assert second_unlike.status_code == 200
