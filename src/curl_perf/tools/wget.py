"""wget2 tool adapter."""

import shutil
import subprocess
import time

from curl_perf.results import TimingResult
from curl_perf.tools.base import ToolAdapter


class WgetAdapter(ToolAdapter):
    name = "wget2"

    def is_available(self) -> bool:
        return shutil.which("wget2") is not None or shutil.which("wget") is not None

    def _wget_cmd(self) -> str:
        if shutil.which("wget2"):
            return "wget2"
        return "wget"

    def supports_http2(self) -> bool:
        try:
            result = subprocess.run(
                [self._wget_cmd(), "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return "2" in result.stdout.split("\n")[0]
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _build_command(self, url: str, http_version: str) -> list[str]:
        cmd = [self._wget_cmd(), "-q", "-O", "/dev/null", "--no-check-certificate"]
        if http_version == "1.1":
            cmd.append("--no-http2")
        cmd.append(url)
        return cmd

    def run(self, url: str, http_version: str = "2") -> TimingResult:
        cmd = self._build_command(url, http_version)
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if result.returncode != 0:
            raise RuntimeError(f"wget failed (exit {result.returncode}): {result.stderr}")
        return TimingResult(
            total_ms=elapsed_ms, bytes_transferred=0, http_version_used=http_version,
        )

    def run_concurrent(self, urls: list[str], http_version: str = "2") -> TimingResult:
        cmd = [self._wget_cmd(), "-q", "-O", "/dev/null", "--no-check-certificate"]
        if http_version == "1.1":
            cmd.append("--no-http2")
        cmd.extend(urls)
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if result.returncode != 0:
            raise RuntimeError(f"wget concurrent failed (exit {result.returncode}): {result.stderr}")
        return TimingResult(
            total_ms=elapsed_ms, bytes_transferred=0, http_version_used=http_version,
        )
