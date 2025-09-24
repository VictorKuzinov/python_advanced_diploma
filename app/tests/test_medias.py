# app/tests/test_medias.py
import io

import pytest


@pytest.mark.asyncio
async def test_upload_media_png(client, seed_users):
    """Успешная загрузка одного PNG, в ответе media_id (int)."""
    headers = {"api-key": seed_users["alice"]["api_key"]}
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"fake"  # минимальный фейк

    # одиночная загрузка: поле строго "file"
    files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
    r = await client.post("/api/medias", headers=headers, files=files)

    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert data["result"] is True
    assert isinstance(data["media_id"], int)


@pytest.mark.asyncio
async def test_create_tweet_with_uploaded_media(client, seed_users):
    """Загружаем медиа → создаём твит с этим медиа → в ленте есть вложение .png."""
    headers = {"api-key": seed_users["alice"]["api_key"]}

    files = {"file": ("a.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake"), "image/png")}
    rm = await client.post("/api/medias", headers=headers, files=files)
    assert rm.status_code in (200, 201), rm.text
    media_id = rm.json()["media_id"]

    payload = {"tweet_data": "тестовый твит", "tweet_media_ids": [media_id]}
    rt = await client.post("/api/tweets", headers=headers, json=payload)
    assert rt.status_code in (200, 201), rt.text
    tid = rt.json()["tweet_id"]

    rf = await client.get("/api/tweets", headers=headers)
    assert rf.status_code == 200, rf.text
    tweets = rf.json()["tweets"]
    t = next(t for t in tweets if t["id"] == tid)
    assert t["attachments"], "Ожидали хотя бы одно вложение"
    assert all(isinstance(p, str) for p in t["attachments"])
    # путь относительный и ведёт в media/
    assert any(a.startswith("media/") and a.endswith(".png") for a in t["attachments"])


@pytest.mark.asyncio
async def test_upload_media_invalid_type_returns_400(client, seed_users):
    """Попытка загрузить text/plain → 400 DomainValidation с сообщением о типе."""
    headers = {"api-key": seed_users["alice"]["api_key"]}
    bad_bytes = b"not-really-a-media-file"

    files = {"file": ("bad.txt", io.BytesIO(bad_bytes), "text/plain")}
    r = await client.post("/api/medias", headers=headers, files=files)

    assert r.status_code == 400, r.text
    data = r.json()
    assert data["result"] is False
    assert data["error_type"] == "DomainValidation"
    assert "unsupported media type" in data["error_message"]
