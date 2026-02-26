from curl_perf.tools.base import ToolAdapter
from curl_perf.results import TimingResult


class FakeAdapter(ToolAdapter):
    name = "fake"

    def is_available(self) -> bool:
        return True

    def supports_http2(self) -> bool:
        return True

    def run(self, url: str, http_version: str = "2") -> TimingResult:
        return TimingResult(total_ms=10, bytes_transferred=100, http_version_used=http_version,
                            dns_ms=1, connect_ms=2, tls_ms=3, ttfb_ms=5)

    def run_concurrent(self, urls: list[str], http_version: str = "2") -> TimingResult:
        return TimingResult(total_ms=50, bytes_transferred=500, http_version_used=http_version,
                            dns_ms=1, connect_ms=2, tls_ms=3, ttfb_ms=5)


def test_adapter_interface():
    adapter = FakeAdapter()
    assert adapter.name == "fake"
    assert adapter.is_available()
    assert adapter.supports_http2()


def test_adapter_run():
    adapter = FakeAdapter()
    result = adapter.run("http://example.com", "2")
    assert isinstance(result, TimingResult)
    assert result.total_ms == 10


def test_adapter_run_concurrent():
    adapter = FakeAdapter()
    result = adapter.run_concurrent(["http://example.com"] * 5, "2")
    assert isinstance(result, TimingResult)
    assert result.total_ms == 50


import json
from curl_perf.tools.curl import CurlAdapter


def test_curl_is_available():
    adapter = CurlAdapter()
    assert adapter.is_available()


def test_curl_supports_http2():
    adapter = CurlAdapter()
    assert adapter.supports_http2()


def test_curl_build_command_http2():
    adapter = CurlAdapter()
    cmd = adapter._build_command("https://example.com", "2")
    assert "--http2" in cmd
    assert "-s" in cmd
    assert "-o" in cmd
    assert "https://example.com" in cmd


def test_curl_build_command_http11():
    adapter = CurlAdapter()
    cmd = adapter._build_command("https://example.com", "1.1")
    assert "--http1.1" in cmd
    assert "--http2" not in cmd


def test_curl_parse_output():
    adapter = CurlAdapter()
    write_out = json.dumps({
        "time_namelookup": 0.001,
        "time_connect": 0.002,
        "time_appconnect": 0.003,
        "time_starttransfer": 0.005,
        "time_total": 0.010,
        "size_download": 1024,
        "http_version": "2",
    })
    result = adapter._parse_output(write_out)
    assert result.dns_ms == 1.0
    assert result.connect_ms == 2.0
    assert result.tls_ms == 3.0
    assert result.ttfb_ms == 5.0
    assert result.total_ms == 10.0
    assert result.bytes_transferred == 1024
    assert result.http_version_used == "2"


def test_curl_build_concurrent_command():
    adapter = CurlAdapter()
    urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
    cmd = adapter._build_concurrent_command(urls, "2")
    assert "--parallel" in cmd
    assert "--http2" in cmd
    for url in urls:
        assert url in cmd


from curl_perf.tools.wget import WgetAdapter


def test_wget_is_available():
    adapter = WgetAdapter()
    assert adapter.is_available()


def test_wget_build_command_http2():
    adapter = WgetAdapter()
    cmd = adapter._build_command("https://example.com", "2")
    assert "https://example.com" in cmd
    assert "--no-check-certificate" in cmd


def test_wget_build_command_http11():
    adapter = WgetAdapter()
    cmd = adapter._build_command("https://example.com", "1.1")
    assert "--no-http2" in cmd


def test_wget_name():
    adapter = WgetAdapter()
    assert adapter.name == "wget2"


from curl_perf.tools.httpie import HTTPieAdapter


def test_httpie_build_command():
    adapter = HTTPieAdapter()
    cmd = adapter._build_command("https://example.com", "2")
    assert "http" == cmd[0]
    assert "--print=h" in cmd
    assert "--verify=no" in cmd
    assert "https://example.com" in cmd


def test_httpie_name():
    adapter = HTTPieAdapter()
    assert adapter.name == "httpie"


def test_httpie_no_http2():
    adapter = HTTPieAdapter()
    assert not adapter.supports_http2()


from curl_perf.tools.xh import XhAdapter


def test_xh_name():
    adapter = XhAdapter()
    assert adapter.name == "xh"


def test_xh_supports_http2():
    adapter = XhAdapter()
    assert adapter.supports_http2()


def test_xh_build_command_http2():
    adapter = XhAdapter()
    cmd = adapter._build_command("https://example.com", "2")
    assert "xh" == cmd[0]
    assert "--print=h" in cmd
    assert "--verify=no" in cmd
    assert "--https" in cmd
    assert "https://example.com" in cmd


def test_xh_build_command_http11():
    adapter = XhAdapter()
    cmd = adapter._build_command("https://example.com", "1.1")
    assert "--http-version=1.1" in cmd
    assert "--https" not in cmd


from curl_perf.tools.py_requests import PyRequestsAdapter


def test_py_requests_name():
    adapter = PyRequestsAdapter()
    assert adapter.name == "py-requests"


def test_py_requests_is_available():
    adapter = PyRequestsAdapter()
    assert adapter.is_available()


def test_py_requests_no_http2():
    adapter = PyRequestsAdapter()
    assert not adapter.supports_http2()


from curl_perf.tools import get_available_tools, get_tool


def test_get_available_tools():
    tools = get_available_tools()
    names = [t.name for t in tools]
    assert "curl" in names


def test_get_tool_by_name():
    tool = get_tool("curl")
    assert tool is not None
    assert tool.name == "curl"


def test_get_tool_unknown():
    tool = get_tool("nonexistent")
    assert tool is None
