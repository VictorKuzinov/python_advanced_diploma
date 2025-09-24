# app/tests/test_follows.py
import pytest

FOLLOW_POST = "/api/users/{user_id}/follow"
FOLLOW_DEL = "/api/users/{user_id}/follow"
PROFILE_GET = "/api/users/{user_id}"


@pytest.mark.asyncio
async def test_follow_user(client, seed_users):
    """Первый follow — 200 OK, повторный — конфликт (409/400)."""
    headers = {"api-key": seed_users["alice"]["api_key"]}
    bob_id = seed_users["bob"]["id"]

    # первый follow
    r1 = await client.post(FOLLOW_POST.format(user_id=bob_id), headers=headers)
    assert r1.status_code == 200, r1.text
    assert r1.json()["result"] is True

    # повторный follow → AlreadyExists
    r2 = await client.post(FOLLOW_POST.format(user_id=bob_id), headers=headers)
    assert r2.status_code in (400, 409), r2.text


@pytest.mark.asyncio
async def test_unfollow_user(client, seed_users):
    """unfollow работает и идемпотентен: второй вызов тоже 200 OK."""
    headers = {"api-key": seed_users["alice"]["api_key"]}
    bob_id = seed_users["bob"]["id"]

    # подготовка: подписались
    _ = await client.post(FOLLOW_POST.format(user_id=bob_id), headers=headers)

    # первый unfollow
    r1 = await client.delete(FOLLOW_DEL.format(user_id=bob_id), headers=headers)
    assert r1.status_code == 200, r1.text
    assert r1.json()["result"] is True

    # повторный unfollow — тоже ок
    r2 = await client.delete(FOLLOW_DEL.format(user_id=bob_id), headers=headers)
    assert r2.status_code == 200, r2.text


@pytest.mark.asyncio
async def test_feed_contains_followee_tweets_and_sort(client, seed_users):
    """
    Лента содержит твиты подписок и сортируется по лайкам ↓ затем по дате ↓.

    Сценарий:
      - Bob постит B-1, B-2
      - Alice подписывается на Bob
      - Alice лайкает B-2
      - В ленте Alice: B-2 раньше B-1
    """
    alice = seed_users["alice"]
    bob = seed_users["bob"]
    h_alice = {"api-key": alice["api_key"]}
    h_bob = {"api-key": bob["api_key"]}

    # Bob публикует два твита
    t1 = await client.post(
        "/api/tweets",
        headers=h_bob,
        json={"tweet_data": "B-1", "tweet_media_ids": []},
    )
    t2 = await client.post(
        "/api/tweets",
        headers=h_bob,
        json={"tweet_data": "B-2", "tweet_media_ids": []},
    )
    assert t1.status_code in (200, 201) and t2.status_code in (200, 201)
    id1, id2 = t1.json()["tweet_id"], t2.json()["tweet_id"]

    # Alice подписывается на Bob (допускаем 409, если уже была подписка)
    rfollow = await client.post(FOLLOW_POST.format(user_id=bob["id"]), headers=h_alice)
    assert rfollow.status_code in (200, 201, 409), rfollow.text

    # Лайкнем второй твит, чтобы проверить сортировку по популярности
    _ = await client.post(f"/api/tweets/{id2}/likes", headers=h_alice)

    # Лента Alice
    rf = await client.get("/api/tweets", headers=h_alice)
    assert rf.status_code == 200, rf.text
    feed = rf.json()["tweets"]

    # Оба твита Bob должны быть в ленте
    feed_ids = [t["id"] for t in feed]
    assert id1 in feed_ids and id2 in feed_ids

    # Более залайканный твит (id2) должен идти раньше id1
    pos = {t["id"]: i for i, t in enumerate(feed)}
    assert pos[id2] < pos[id1]


@pytest.mark.asyncio
async def test_follow_nonexistent_user_returns_not_found(client, seed_users):
    """Подписка на несуществующего пользователя → EntityNotFound (404/400)."""
    alice = seed_users["alice"]
    h_alice = {"api-key": alice["api_key"]}

    nonexistent_id = 999_999
    r = await client.post(FOLLOW_POST.format(user_id=nonexistent_id), headers=h_alice)
    assert r.status_code in (400, 404), r.text
    body = r.json()
    assert body["result"] is False
    assert body["error_type"] in ("EntityNotFound", "DomainValidation")


@pytest.mark.asyncio
async def test_follow_self_forbidden(client, seed_users):
    """Нельзя подписаться на себя → ForbiddenAction (403/400)."""
    bob = seed_users["bob"]
    h_bob = {"api-key": bob["api_key"]}

    r = await client.post(FOLLOW_POST.format(user_id=bob["id"]), headers=h_bob)
    assert r.status_code in (400, 403), r.text
    body = r.json()
    assert body["result"] is False
    assert body["error_type"] in ("ForbiddenAction", "DomainValidation")


@pytest.mark.asyncio
async def test_follow_duplicate_returns_conflict(client, seed_users):
    """Повторная подписка → AlreadyExists (обычно 409)."""
    alice = seed_users["alice"]
    jack = seed_users["jack"]
    h_alice = {"api-key": alice["api_key"]}

    r1 = await client.post(FOLLOW_POST.format(user_id=jack["id"]), headers=h_alice)
    assert r1.status_code in (200, 201), r1.text

    r2 = await client.post(FOLLOW_POST.format(user_id=jack["id"]), headers=h_alice)
    assert r2.status_code in (400, 409), r2.text
    body = r2.json()
    assert body["result"] is False
    assert body["error_type"] in ("AlreadyExists", "DomainValidation")


@pytest.mark.asyncio
async def test_unfollow_is_idempotent_even_if_never_followed(client, seed_users):
    """Отписка без существующей подписки → 200 (идемпотентно)."""
    alice = seed_users["alice"]
    jack = seed_users["jack"]
    h_alice = {"api-key": alice["api_key"]}

    r = await client.delete(FOLLOW_DEL.format(user_id=jack["id"]), headers=h_alice)
    assert r.status_code == 200, r.text
    assert r.json()["result"] is True


@pytest.mark.asyncio
async def test_profile_nonexistent_user_returns_not_found(client, seed_users):
    """Профиль несуществующего пользователя → EntityNotFound (404/400)."""
    alice = seed_users["alice"]
    h_alice = {"api-key": alice["api_key"]}

    nonexistent_id = 888_888
    r = await client.get(PROFILE_GET.format(user_id=nonexistent_id), headers=h_alice)
    assert r.status_code in (400, 404), r.text
    body = r.json()
    assert body["result"] is False
    assert body["error_type"] in ("EntityNotFound", "DomainValidation")


@pytest.mark.asyncio
async def test_profile_lists_followers_and_following_consistently(client, seed_users):
    """Профиль содержит корректные followers/following (id+имя)."""
    alice = seed_users["alice"]
    bob = seed_users["bob"]
    jack = seed_users["jack"]

    h_alice = {"api-key": alice["api_key"]}
    h_bob = {"api-key": bob["api_key"]}

    # Alice → follow Bob, Jack
    await client.post(FOLLOW_POST.format(user_id=bob["id"]), headers=h_alice)
    await client.post(FOLLOW_POST.format(user_id=jack["id"]), headers=h_alice)

    # Bob → follow Alice
    await client.post(FOLLOW_POST.format(user_id=alice["id"]), headers=h_bob)

    rp = await client.get(PROFILE_GET.format(user_id=alice["id"]), headers=h_alice)
    assert rp.status_code == 200, rp.text
    profile = rp.json()["user"]

    # following у Alice: bob, jack
    following_names = sorted([u.get("name") for u in profile["following"]])
    assert following_names == sorted(["bob", "jack"])

    # followers у Alice: bob
    follower_names = sorted([u.get("name") for u in profile["followers"]])
    assert "bob" in follower_names
