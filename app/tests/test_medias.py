# app/tests/test_medias.py
import io

import pytest


@pytest.mark.asyncio
async def test_upload_media_png(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"fake"  # минимальный фейк
    files = [("files", ("test.png", io.BytesIO(png_bytes), "image/png"))]
    r = await client.post("/api/medias", headers=headers, files=files)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert data["result"] is True
    assert isinstance(data["media_ids"][0], int)


@pytest.mark.asyncio
async def test_upload_media_multi(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}

    jpg_bytes = b"\xff\xd8\xff" + b"fakejpeg"
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"fakepng"

    # multipart с несколькими файлами: список пар ("files", (<filename>, <fileobj>, <ctype>))
    files = [
        ("files", ("a.jpg", io.BytesIO(jpg_bytes), "image/jpeg")),
        ("files", ("b.png", io.BytesIO(png_bytes), "image/png")),
    ]

    r = await client.post("/api/medias", headers=headers, files=files)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert data["result"] is True
    assert isinstance(data.get("media_ids"), list)
    assert len(data["media_ids"]) == 2
    assert all(isinstance(x, int) for x in data["media_ids"])
