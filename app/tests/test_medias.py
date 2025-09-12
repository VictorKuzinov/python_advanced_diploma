# app/tests/test_medias.py
import io

import pytest


@pytest.mark.asyncio
async def test_upload_media_png(client, seed_users):
    headers = {"api-key": seed_users["alice"]["api_key"]}
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"fake"  # минимальный фейк

    files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
    r = await client.post("/api/medias", headers=headers, files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["result"] is True
    assert isinstance(data["media_id"], int)
