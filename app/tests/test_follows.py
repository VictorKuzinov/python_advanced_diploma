# app/tests/test_follows.py
import pytest

FOLLOW_POST_PATH = "/api/users/{user_id}/follow"


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

    @pytest.mark.asyncio
    async def test_feed_contains_followee_tweets_and_sort(client, seed_users):
        # Alice будет смотреть ленту, Bob — автор
        alice = seed_users["alice"]
        bob = seed_users["bob"]
        h_alice = {"api-key": alice["api_key"]}
        h_bob = {"api-key": bob["api_key"]}

        # Bob публикует два твита
        t1 = await client.post(
            "/api/tweets", headers=h_bob, json={"tweet_data": "B-1", "tweet_media_ids": []}
        )
        t2 = await client.post(
            "/api/tweets", headers=h_bob, json={"tweet_data": "B-2", "tweet_media_ids": []}
        )
        assert t1.status_code in (200, 201) and t2.status_code in (200, 201)
        id1, id2 = t1.json()["tweet_id"], t2.json()["tweet_id"]

        # Alice подписывается на Bob (если требуется)
        rfollow = await client.post(FOLLOW_POST_PATH.format(user_id=bob["id"]), headers=h_alice)
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

        # Если у вас сортировка: по лайкам ↓, затем по дате ↓,
        # то более залайканный твит (id2) должен идти раньше id1.
        # Проверим относительный порядок:
        pos = {t["id"]: i for i, t in enumerate(feed)}
        assert pos[id2] < pos[id1]
