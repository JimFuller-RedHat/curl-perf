"""HTTPie tool adapter."""

import concurrent.futures
import shutil
import subprocess
import time

from curl_perf.results import TimingResult
from curl_perf.tools.base import ToolAdapter


class HTTPieAdapter(ToolAdapter):
    name = "httpie"

    def is_available(self) -> bool:
        return shutil.which("http") is not None

    def supports_http2(self) -> bool:
        return False

    def _build_command(self, url: str, http_version: str) -> list[str]:
        cmd = [
            "http", "--print=h", "--verify=no", "--timeout=30",
        ]
        cmd.append(url)
        return cmd

    def run(self, url: str, http_version: str = "2") -> TimingResult:
        cmd = self._build_command(url, http_version)
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if result.returncode != 0:
            raise RuntimeError(f"httpie failed (exit {result.returncode}): {result.stderr}")
        return TimingResult(
            total_ms=elapsed_ms, bytes_transferred=0,
            http_version_used="1.1",
        )

    def _run_single(self, url: str, http_version: str) -> None:
        cmd = self._build_command(url, http_version)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"httpie failed (exit {result.returncode}): {result.stderr}")

    def run_concurrent(self, urls: list[str], http_version: str = "2") -> TimingResult:
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as pool:
            futures = [pool.submit(self._run_single, url, http_version) for url in urls]
            for f in concurrent.futures.as_completed(futures):
                f.result()
        elapsed_ms = (time.perf_counter() - start) * 1000
        return TimingResult(
            total_ms=elapsed_ms, bytes_transferred=0,
            http_version_used="1.1",
        )
