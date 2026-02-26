"""Python requests tool adapter."""

import concurrent.futures
import time
import urllib3

from curl_perf.results import TimingResult
from curl_perf.tools.base import ToolAdapter

# Suppress insecure request warnings for --verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PyRequestsAdapter(ToolAdapter):
    name = "py-requests"

    def is_available(self) -> bool:
        try:
            import requests  # noqa: F401
            return True
        except ImportError:
            return False

    def supports_http2(self) -> bool:
        return False

    def run(self, url: str, http_version: str = "2") -> TimingResult:
        import requests

        start = time.perf_counter()
        resp = requests.get(url, verify=False, timeout=30)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return TimingResult(
            total_ms=elapsed_ms,
            bytes_transferred=len(resp.content),
            http_version_used="1.1",
        )

    def _run_single(self, url: str) -> int:
        import requests

        resp = requests.get(url, verify=False, timeout=30)
        return len(resp.content)

    def run_concurrent(self, urls: list[str], http_version: str = "2") -> TimingResult:
        start = time.perf_counter()
        total_bytes = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as pool:
            futures = [pool.submit(self._run_single, url) for url in urls]
            for f in concurrent.futures.as_completed(futures):
                total_bytes += f.result()
        elapsed_ms = (time.perf_counter() - start) * 1000
        return TimingResult(
            total_ms=elapsed_ms,
            bytes_transferred=total_bytes,
            http_version_used="1.1",
        )
