"""Local HTTP/2 test server for reproducible benchmarks."""

import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import parse_qs


def generate_self_signed_cert(directory: Path | str) -> tuple[str, str]:
    directory = Path(directory)
    cert_path = str(directory / "cert.pem")
    key_path = str(directory / "key.pem")
    subprocess.run(
        [
            "/usr/bin/openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_path, "-out", cert_path,
            "-days", "1", "-nodes",
            "-subj", "/CN=localhost",
        ],
        capture_output=True,
        check=True,
    )
    return cert_path, key_path


def create_app():
    async def app(scope, receive, send):
        if scope["type"] != "http":
            return
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)

        if path == "/":
            body = b'{"status": "ok"}'
            await send({
                "type": "http.response.start", "status": 200,
                "headers": [[b"content-type", b"application/json"],
                             [b"content-length", str(len(body)).encode()]],
            })
            await send({"type": "http.response.body", "body": body})
        elif path == "/large":
            size = int(params.get("size", [str(10 * 1024 * 1024)])[0])
            body = b"x" * size
            await send({
                "type": "http.response.start", "status": 200,
                "headers": [[b"content-type", b"application/octet-stream"],
                             [b"content-length", str(size).encode()]],
            })
            await send({"type": "http.response.body", "body": body})
        else:
            body = b"Not Found"
            await send({
                "type": "http.response.start", "status": 404,
                "headers": [[b"content-type", b"text/plain"],
                             [b"content-length", str(len(body)).encode()]],
            })
            await send({"type": "http.response.body", "body": body})

    return app


class LocalServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8443):
        self.host = host
        self.port = port
        self._process = None
        self._tmpdir = None

    @property
    def url(self) -> str:
        return f"https://{self.host}:{self.port}"

    def start(self) -> str:
        self._tmpdir = tempfile.mkdtemp()
        cert_path, key_path = generate_self_signed_cert(self._tmpdir)
        # Project root is 3 levels up from src/curl_perf/server.py
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        self._process = subprocess.Popen(
            [
                "python", "-m", "hypercorn",
                "curl_perf.server:create_app()",
                "--bind", f"{self.host}:{self.port}",
                "--certfile", cert_path,
                "--keyfile", key_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
        )
        import time
        for _ in range(30):
            try:
                result = subprocess.run(
                    ["curl", "-sk", f"{self.url}/"],
                    capture_output=True, timeout=2,
                )
                if result.returncode == 0:
                    return self.url
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            time.sleep(0.5)
        raise RuntimeError("Server failed to start")

    def stop(self):
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._process = None
        if self._tmpdir:
            import shutil
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None
