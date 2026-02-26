import ssl
import os
import subprocess
import pytest
from curl_perf.server import create_app, generate_self_signed_cert


def _openssl_available() -> bool:
    try:
        result = subprocess.run(
            ["openssl", "version"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


@pytest.mark.skipif(not _openssl_available(), reason="openssl not available or broken")
def test_generate_self_signed_cert(tmp_path):
    cert_path, key_path = generate_self_signed_cert(tmp_path)
    assert os.path.isfile(cert_path)
    assert os.path.isfile(key_path)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_cert_chain(cert_path, key_path)


def test_create_app():
    app = create_app()
    assert callable(app)


async def _call_app(app, path, query_string=b""):
    response_started = False
    status_code = None
    body_parts = []
    scope = {
        "type": "http", "method": "GET", "path": path,
        "query_string": query_string, "headers": [],
    }
    async def receive():
        return {"type": "http.request", "body": b""}
    async def send(message):
        nonlocal response_started, status_code
        if message["type"] == "http.response.start":
            response_started = True
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            body_parts.append(message.get("body", b""))
    await app(scope, receive, send)
    return status_code, b"".join(body_parts)


@pytest.mark.asyncio
async def test_app_root():
    app = create_app()
    status, body = await _call_app(app, "/")
    assert status == 200
    assert b"ok" in body.lower() or len(body) > 0


@pytest.mark.asyncio
async def test_app_large():
    app = create_app()
    status, body = await _call_app(app, "/large", query_string=b"size=1024")
    assert status == 200
    assert len(body) == 1024


@pytest.mark.asyncio
async def test_app_large_default_size():
    app = create_app()
    status, body = await _call_app(app, "/large", query_string=b"")
    assert status == 200
    assert len(body) == 10 * 1024 * 1024


@pytest.mark.asyncio
async def test_app_404():
    app = create_app()
    status, body = await _call_app(app, "/nonexistent")
    assert status == 404
