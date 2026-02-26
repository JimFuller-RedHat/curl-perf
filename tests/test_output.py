import json
import io

from curl_perf.output import format_table, write_json
from curl_perf.results import TimingResult, AggregatedResult


def _make_agg(total_mean=15.0, ttfb_mean=6.0) -> AggregatedResult:
    def _tr(total_ms, ttfb_ms, bytes_transferred=100, **kw):
        return TimingResult(total_ms=total_ms, bytes_transferred=bytes_transferred,
                            http_version_used="2", ttfb_ms=ttfb_ms, **kw)
    return AggregatedResult(
        mean=_tr(total_mean, ttfb_mean),
        median=_tr(total_mean, ttfb_mean),
        p95=_tr(total_mean + 5, ttfb_mean + 2),
        stddev=_tr(1.0, 0.5, bytes_transferred=10),
        count=10,
    )


def test_format_table_contains_tool_name():
    rows = [("curl", "HTTP/2", _make_agg())]
    output = format_table("Single Request Latency", rows, iterations=10)
    assert "curl" in output
    assert "HTTP/2" in output


def test_format_table_contains_values():
    rows = [("curl", "HTTP/2", _make_agg(total_mean=15.0, ttfb_mean=6.0))]
    output = format_table("Test", rows, iterations=10)
    assert "15.0" in output
    assert "6.0" in output


def test_format_table_multiple_rows():
    rows = [
        ("curl", "HTTP/2", _make_agg(total_mean=15.0)),
        ("wget2", "HTTP/2", _make_agg(total_mean=18.0)),
    ]
    output = format_table("Test", rows, iterations=10)
    assert "curl" in output
    assert "wget2" in output


def test_write_json():
    results = {"scenario": "latency", "data": [{"tool": "curl", "total_ms": 15.0}]}
    buf = io.StringIO()
    write_json(results, buf)
    parsed = json.loads(buf.getvalue())
    assert parsed["scenario"] == "latency"
    assert parsed["data"][0]["tool"] == "curl"
