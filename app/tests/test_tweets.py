import io

import pytest


@pytest.mark.asyncio
async def test_create_tweet_without_media_and_list(client, seed_users):
    headers = {"api-key": seed_users["bob"]["api_key"]}

    # создаём твит без медиа
    payload = {"tweet_data": "hello world", "tweet_media_ids": None}
    r = await client.post("/api/tweets", json=payload, headers=headers)
    assert r.status_code == 200
    tweet_id = r.json()["tweet_id"]
    assert isinstance(tweet_id, int)

    # получаем ленту боба — в ней должен быть его твит
    r2 = await client.get("/api/tweets", headers=headers)
    assert r2.status_code == 200
    items = r2.json()["tweets"]
    assert any(t["id"] == tweet_id for t in items)


@pytest.mark.asyncio
async def test_create_tweet_with_media(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}

    # загружаем медиа
    png = b"\x89PNG\r\n\x1a\nfake"
    files = {"files": ("a.png", io.BytesIO(png), "image/png")}
    rm = await client.post("api/medias", headers=headers, files=files)
    mid = rm.json()["media_ids"][0]

    # создаём твит с этим медиа
    payload = {"tweet_data": "тестовый твит", "tweet_media_ids": [mid]}
    rt = await client.post("api/tweets", headers=headers, json=payload)
    tid = rt.json()["tweet_id"]

    # проверяем, что он в ленте
    rf = await client.get("api/tweets", headers=headers)
    tweets = rf.json()["tweets"]
    assert any(t["id"] == tid for t in tweets)


@pytest.mark.asyncio
async def test_delete_tweet(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}

    # создаём твит без медиа (чтобы было что удалять)
    payload = {"tweet_data": "тест на удаление", "tweet_media_ids": []}
    rt = await client.post("api/tweets", headers=headers, json=payload)
    tid = rt.json()["tweet_id"]

    # удаляем его
    rd = await client.delete(f"api/tweets/{tid}", headers=headers)
    assert rd.json()["result"] is True

    # убеждаемся, что в ленте его больше нет
    rf = await client.get("api/tweets", headers=headers)
    tweets = rf.json()["tweets"]
    assert not any(t["id"] == tid for t in tweets)
