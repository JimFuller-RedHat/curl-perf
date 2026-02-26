from curl_perf.runner import BenchmarkRunner, BenchmarkConfig
from curl_perf.results import TimingResult
from curl_perf.tools.base import ToolAdapter


class StubAdapter(ToolAdapter):
    name = "stub"

    def __init__(self):
        self.run_count = 0

    def is_available(self):
        return True

    def supports_http2(self):
        return True

    def run(self, url, http_version="2"):
        self.run_count += 1
        return TimingResult(total_ms=10 + self.run_count, bytes_transferred=100,
                            http_version_used=http_version, dns_ms=1, connect_ms=2,
                            tls_ms=3, ttfb_ms=5)

    def run_concurrent(self, urls, http_version="2"):
        self.run_count += 1
        return TimingResult(total_ms=50, bytes_transferred=500,
                            http_version_used=http_version, dns_ms=1, connect_ms=2,
                            tls_ms=3, ttfb_ms=5)


def test_config_defaults():
    config = BenchmarkConfig(url="https://example.com")
    assert config.iterations == 10
    assert config.concurrency == 10
    assert config.download_size == 10 * 1024 * 1024
    assert "1.1" in config.http_versions
    assert "2" in config.http_versions


def test_runner_latency_scenario():
    adapter = StubAdapter()
    config = BenchmarkConfig(
        url="https://example.com", iterations=3,
        http_versions=["2"], scenarios=["latency"],
    )
    runner = BenchmarkRunner(config, [adapter])
    results = runner.run_latency(adapter)
    assert len(results) == 1
    protocol, agg = results[0]
    assert protocol == "HTTP/2"
    assert agg.count == 3


def test_runner_multiplex_scenario():
    adapter = StubAdapter()
    config = BenchmarkConfig(
        url="https://example.com", iterations=2,
        http_versions=["2"], concurrency=5, scenarios=["multiplex"],
    )
    runner = BenchmarkRunner(config, [adapter])
    results = runner.run_multiplex(adapter)
    assert len(results) == 1
    protocol, agg = results[0]
    assert protocol == "HTTP/2"
    assert agg.count == 2


def test_runner_run_all():
    adapter = StubAdapter()
    config = BenchmarkConfig(
        url="https://example.com", iterations=2,
        http_versions=["2"], scenarios=["latency"],
    )
    runner = BenchmarkRunner(config, [adapter])
    all_results = runner.run_all()
    assert "latency" in all_results
    assert "stub" in all_results["latency"]
