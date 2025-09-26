# app/tests/test_tweets.py
"""
Тесты /api/tweets:
- создание без/с медиа
- валидации (пусто → 400; >280 → 422 от Pydantic; несуществующий media → 404)
- удаление: своё (ок), чужое → 403, несуществующее → 404
- сортировка ленты: likes ↓, затем created_at ↓
- attachments: относительные пути "media/<...>"
"""

import io

import pytest

TWEETS_PATH = "/api/tweets"
MEDIAS_PATH = "/api/medias"


# --------- helpers ---------
async def _upload_png(client, headers, name="a.png"):
    png = b"\x89PNG\r\n\x1a\nfake"
    files = {"file": (name, io.BytesIO(png), "image/png")}
    r = await client.post(MEDIAS_PATH, headers=headers, files=files)
    assert r.status_code in (200, 201), r.text
    return r.json()["media_id"]


async def _create_tweet(client, headers, text, media_ids=None):
    payload = {"tweet_data": text, "tweet_media_ids": media_ids or []}
    return await client.post(TWEETS_PATH, headers=headers, json=payload)


# --------- базовые сценарии ---------
@pytest.mark.asyncio
async def test_create_tweet_without_media_and_list(client, seed_users):
    """Создание твита без медиа и проверка появления в ленте автора."""
    h = {"api-key": seed_users["bob"]["api_key"]}

    r = await _create_tweet(client, h, text="hello world")
    assert r.status_code == 200, r.text
    tid = r.json()["tweet_id"]
    assert isinstance(tid, int)

    r2 = await client.get(TWEETS_PATH, headers=h)
    assert r2.status_code == 200, r2.text
    items = r2.json()["tweets"]
    assert any(t["id"] == tid for t in items)


@pytest.mark.asyncio
async def test_create_tweet_with_media(client, seed_users):
    """Создание твита с предварительно загруженным PNG."""
    h = {"api-key": seed_users["alice"]["api_key"]}

    mid = await _upload_png(client, h, name="pic.png")

    rt = await _create_tweet(client, h, text="тестовый твит", media_ids=[mid])
    assert rt.status_code == 200, rt.text
    tid = rt.json()["tweet_id"]

    rf = await client.get(TWEETS_PATH, headers=h)
    assert rf.status_code == 200, rf.text
    tweets = rf.json()["tweets"]
    assert any(t["id"] == tid for t in tweets)


@pytest.mark.asyncio
async def test_delete_own_tweet(client, seed_users):
    """Создание и удаление своего твита — из ленты пропадает."""
    h = {"api-key": seed_users["alice"]["api_key"]}

    rt = await _create_tweet(client, h, text="тест на удаление")
    assert rt.status_code == 200, rt.text
    tid = rt.json()["tweet_id"]

    rd = await client.delete(f"{TWEETS_PATH}/{tid}", headers=h)
    assert rd.status_code == 200, rd.text
    assert rd.json()["result"] is True

    rf = await client.get(TWEETS_PATH, headers=h)
    assert rf.status_code == 200, rf.text
    tweets = rf.json()["tweets"]
    assert not any(t["id"] == tid for t in tweets)


# --------- валидации ---------
@pytest.mark.asyncio
async def test_create_tweet_validation_empty(client, seed_users):
    """Пустой контент → 400 DomainValidation (валидация сервиса)."""
    h = {"api-key": seed_users["alice"]["api_key"]}
    r = await _create_tweet(client, h, text="  ")
    assert r.status_code == 400, r.text
    body = r.json()
    assert body["result"] is False
    assert body["error_type"] == "DomainValidation"


@pytest.mark.asyncio
async def test_create_tweet_validation_too_long(client, seed_users):
    """Контент >280 символов → 422 от Pydantic-схемы TweetCreate."""
    h = {"api-key": seed_users["alice"]["api_key"]}
    long_text = "x" * 281
    r = await _create_tweet(client, h, text=long_text)
    assert r.status_code == 422, r.text
    detail = r.json().get("detail", [])
    assert any(
        e.get("type") == "string_too_long" and e.get("loc") == ["body", "tweet_data"]
        for e in detail
    )


@pytest.mark.asyncio
async def test_create_tweet_with_nonexistent_media_returns_not_found(client, seed_users):
    """Несуществующий media_id → 404 EntityNotFound."""
    h = {"api-key": seed_users["alice"]["api_key"]}
    r = await _create_tweet(client, h, text="hello", media_ids=[999_999])
    assert r.status_code == 404, r.text
    body = r.json()
    assert body["result"] is False
    assert body["error_type"] == "EntityNotFound"


# --------- удаление: ошибки ---------
@pytest.mark.asyncio
async def test_delete_foreign_tweet_forbidden(client, seed_users):
    """Удаление чужого твита → 403 ForbiddenAction."""
    alice = seed_users["alice"]
    bob = seed_users["bob"]

    h_alice = {"api-key": alice["api_key"]}
    h_bob = {"api-key": bob["api_key"]}

    rb = await _create_tweet(client, h_bob, text="bob tweet")
    assert rb.status_code == 200, rb.text
    tid = rb.json()["tweet_id"]

    rd = await client.delete(f"{TWEETS_PATH}/{tid}", headers=h_alice)
    assert rd.status_code == 403, rd.text
    body = rd.json()
    assert body["result"] is False
    assert body["error_type"] == "ForbiddenAction"


@pytest.mark.asyncio
async def test_delete_nonexistent_tweet_not_found(client, seed_users):
    """Удаление несуществующего твита → 404 EntityNotFound."""
    h = {"api-key": seed_users["alice"]["api_key"]}
    rd = await client.delete(f"{TWEETS_PATH}/987654321", headers=h)
    assert rd.status_code == 404, rd.text
    body = rd.json()
    assert body["result"] is False
    assert body["error_type"] == "EntityNotFound"


# --------- сортировка ленты ---------
@pytest.mark.asyncio
async def test_feed_sort_by_likes_then_date(client, seed_users):
    """
    Лента сортируется по лайкам ↓, затем по дате ↓:
      - Bob постит B1, B2
      - Alice фолловит Bob
      - Alice лайкает B2
      - В ленте Alice: B2 раньше B1
    """
    alice = seed_users["alice"]
    bob = seed_users["bob"]

    h_alice = {"api-key": alice["api_key"]}
    h_bob = {"api-key": bob["api_key"]}

    r1 = await _create_tweet(client, h_bob, text="B1")
    r2 = await _create_tweet(client, h_bob, text="B2")
    assert r1.status_code == 200 and r2.status_code == 200
    id1, id2 = r1.json()["tweet_id"], r2.json()["tweet_id"]

    rf = await client.post(f"/api/users/{bob['id']}/follow", headers=h_alice)
    assert rf.status_code in (200, 201, 409), rf.text

    _ = await client.post(f"/api/tweets/{id2}/likes", headers=h_alice)

    feed = (await client.get(TWEETS_PATH, headers=h_alice)).json()["tweets"]
    pos = {t["id"]: i for i, t in enumerate(feed)}
    assert pos[id2] < pos[id1]


# --------- attachments ---------
@pytest.mark.asyncio
async def test_attachments_paths_echo_back(client, seed_users):
    """PNG попадает в attachments как относительный путь 'media/<file>'."""
    h = {"api-key": seed_users["alice"]["api_key"]}
    mid = await _upload_png(client, h, name="pic.png")

    r = await _create_tweet(client, h, text="with image", media_ids=[mid])
    assert r.status_code == 200, r.text
    tid = r.json()["tweet_id"]

    feed = (await client.get(TWEETS_PATH, headers=h)).json()["tweets"]
    tw = next(t for t in feed if t["id"] == tid)
    assert tw["attachments"], "attachments must not be empty"
    assert any(p.endswith(".png") and p.startswith("media/") for p in tw["attachments"])
