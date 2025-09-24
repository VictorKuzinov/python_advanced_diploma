# app/tests/test_likes.py
import pytest

TWEETS_PATH = "/api/tweets"


async def _create_tweet(client, *, api_key: str, text: str) -> int:
    """Хелпер: создаёт твит и возвращает его id."""
    headers = {"api-key": api_key}
    payload = {"tweet_data": text, "tweet_media_ids": None}
    resp = await client.post(TWEETS_PATH, headers=headers, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["tweet_id"]


@pytest.mark.asyncio
async def test_like_then_duplicate_returns_conflict(client, seed_users):
    """Первый лайк — OK, повторный — конфликт (400/409)."""
    alice = seed_users["alice"]["api_key"]  # автор твита
    bob = seed_users["bob"]["api_key"]  # ставит лайк

    tweet_id = await _create_tweet(client, api_key=alice, text="like me")

    # первый лайк — ок
    r1 = await client.post(f"{TWEETS_PATH}/{tweet_id}/likes", headers={"api-key": bob})
    assert r1.status_code == 200, r1.text
    assert r1.json()["result"] is True

    # повторный лайк — конфликт
    r2 = await client.post(f"{TWEETS_PATH}/{tweet_id}/likes", headers={"api-key": bob})
    assert r2.status_code in (400, 409), r2.text


@pytest.mark.asyncio
async def test_unlike_is_idempotent(client, seed_users):
    """Снятие лайка дважды подряд возвращает 200 оба раза (идемпотентно)."""
    alice = seed_users["alice"]["api_key"]
    bob = seed_users["bob"]["api_key"]

    tweet_id = await _create_tweet(client, api_key=alice, text="unlike me")

    # предварительно поставим лайк
    like = await client.post(f"{TWEETS_PATH}/{tweet_id}/likes", headers={"api-key": bob})
    assert like.status_code == 200, like.text

    # первый анлайк — ок
    r1 = await client.delete(f"{TWEETS_PATH}/{tweet_id}/likes", headers={"api-key": bob})
    assert r1.status_code == 200, r1.text
    assert r1.json()["result"] is True

    # второй анлайк — тоже ок (идемпотентно)
    r2 = await client.delete(f"{TWEETS_PATH}/{tweet_id}/likes", headers={"api-key": bob})
    assert r2.status_code == 200, r2.text


@pytest.mark.asyncio
async def test_unlike_without_like_is_ok(client, seed_users):
    """Снятие лайка без предварительного лайка → 200 (идемпотентно)."""
    alice = seed_users["alice"]["api_key"]
    bob = seed_users["bob"]["api_key"]

    tweet_id = await _create_tweet(client, api_key=alice, text="no like yet")

    r = await client.delete(f"{TWEETS_PATH}/{tweet_id}/likes", headers={"api-key": bob})
    assert r.status_code == 200, r.text
    assert r.json()["result"] is True


@pytest.mark.asyncio
async def test_like_nonexistent_tweet_returns_not_found(client, seed_users):
    """Лайк несуществующего твита → 404/400 (EntityNotFound/DomainValidation)."""
    bob = seed_users["bob"]["api_key"]
    nonexistent_id = 999_999

    r = await client.post(f"{TWEETS_PATH}/{nonexistent_id}/likes", headers={"api-key": bob})
    assert r.status_code in (400, 404), r.text
    body = r.json()
    assert body["result"] is False
    assert body["error_type"] in ("EntityNotFound", "DomainValidation")


@pytest.mark.asyncio
async def test_likes_reflected_in_feed(client, seed_users):
    """После лайка твит содержит в likes пользователя, который лайкнул."""
    alice_key = seed_users["alice"]["api_key"]  # автор
    bob_key = seed_users["bob"]["api_key"]  # лайкает
    bob_id = seed_users["bob"]["id"]
    alice_id = seed_users["alice"]["id"]

    tweet_id = await _create_tweet(client, api_key=alice_key, text="check likes")

    # Bob подписывается на Alice, чтобы видеть её твиты в своей ленте
    r_follow = await client.post(f"/api/users/{alice_id}/follow", headers={"api-key": bob_key})
    assert r_follow.status_code in (200, 201, 409), r_follow.text  # 409 допустим, если уже подписан

    # лайк от Bob
    r_like = await client.post(f"{TWEETS_PATH}/{tweet_id}/likes", headers={"api-key": bob_key})
    assert r_like.status_code == 200, r_like.text

    # запрос ленты Bob — теперь твит Alice должен быть виден
    feed = await client.get(TWEETS_PATH, headers={"api-key": bob_key})
    assert feed.status_code == 200, feed.text

    tws = feed.json()["tweets"]
    target = next(t for t in tws if t["id"] == tweet_id)

    liker_names = [u["name"] for u in target["likes"]]
    liker_ids = [u["user_id"] for u in target["likes"]]

    # в лайкерах есть Bob
    assert bob_id in liker_ids
    assert "bob" in liker_names
