"""curl tool adapter."""

import json
import shutil
import subprocess
import time

from curl_perf.results import TimingResult
from curl_perf.tools.base import ToolAdapter

WRITE_OUT_FORMAT = json.dumps({
    "time_namelookup": "%{time_namelookup}",
    "time_connect": "%{time_connect}",
    "time_appconnect": "%{time_appconnect}",
    "time_starttransfer": "%{time_starttransfer}",
    "time_total": "%{time_total}",
    "size_download": "%{size_download}",
    "http_version": "%{http_version}",
}) + "\n"


class CurlAdapter(ToolAdapter):
    name = "curl"

    def is_available(self) -> bool:
        return shutil.which("curl") is not None

    def supports_http2(self) -> bool:
        try:
            result = subprocess.run(
                ["curl", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return "HTTP2" in result.stdout or "nghttp2" in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _build_command(self, url: str, http_version: str) -> list[str]:
        cmd = ["curl", "-s", "-o", "/dev/null", "-w", WRITE_OUT_FORMAT]
        if http_version == "2":
            cmd.append("--http2")
        else:
            cmd.append("--http1.1")
        cmd.extend(["-k", url])
        return cmd

    def _parse_output(self, output: str) -> TimingResult:
        data = json.loads(output)
        return TimingResult(
            dns_ms=float(data["time_namelookup"]) * 1000,
            connect_ms=float(data["time_connect"]) * 1000,
            tls_ms=float(data["time_appconnect"]) * 1000,
            ttfb_ms=float(data["time_starttransfer"]) * 1000,
            total_ms=float(data["time_total"]) * 1000,
            bytes_transferred=int(float(data["size_download"])),
            http_version_used=str(data["http_version"]),
        )

    def run(self, url: str, http_version: str = "2") -> TimingResult:
        cmd = self._build_command(url, http_version)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr}")
        return self._parse_output(result.stdout)

    def _build_concurrent_command(self, urls: list[str], http_version: str) -> list[str]:
        cmd = ["curl", "-s", "--parallel", "-w", WRITE_OUT_FORMAT]
        if http_version == "2":
            cmd.append("--http2")
        else:
            cmd.append("--http1.1")
        cmd.append("-k")
        # Each URL needs its own -o /dev/null to suppress response body output
        for url in urls:
            cmd.extend(["-o", "/dev/null", url])
        return cmd

    def run_concurrent(self, urls: list[str], http_version: str = "2") -> TimingResult:
        cmd = self._build_concurrent_command(urls, http_version)
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if result.returncode != 0:
            raise RuntimeError(f"curl concurrent failed: {result.stderr}")
        # Each -w output is followed by a newline, so split on newlines
        json_lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
        last = self._parse_output(json_lines[-1])
        return TimingResult(
            dns_ms=last.dns_ms, connect_ms=last.connect_ms,
            tls_ms=last.tls_ms, ttfb_ms=last.ttfb_ms,
            total_ms=elapsed_ms,
            bytes_transferred=last.bytes_transferred * len(urls),
            http_version_used=last.http_version_used,
        )
