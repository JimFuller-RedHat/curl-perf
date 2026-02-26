"""Benchmark runner that orchestrates scenarios across tools."""

from dataclasses import dataclass, field

from curl_perf.results import TimingResult, AggregatedResult, aggregate
from curl_perf.tools.base import ToolAdapter

HTTP_VERSION_LABELS = {"2": "HTTP/2", "1.1": "HTTP/1.1"}


@dataclass
class BenchmarkConfig:
    url: str
    iterations: int = 10
    concurrency: int = 10
    download_size: int = 10 * 1024 * 1024
    http_versions: list[str] = field(default_factory=lambda: ["1.1", "2"])
    scenarios: list[str] = field(
        default_factory=lambda: ["latency", "multiplex", "throughput"]
    )
    local_server: bool = False


class BenchmarkRunner:
    def __init__(self, config: BenchmarkConfig, tools: list[ToolAdapter]):
        self.config = config
        self.tools = tools

    def _versions_for_tool(self, tool: ToolAdapter) -> list[str]:
        """Return the HTTP versions this tool can actually run."""
        return [
            v for v in self.config.http_versions
            if v != "2" or tool.supports_http2()
        ]

    def run_latency(self, tool: ToolAdapter) -> list[tuple[str, AggregatedResult]]:
        results = []
        for version in self._versions_for_tool(tool):
            timings = []
            for _ in range(self.config.iterations):
                timing = tool.run(self.config.url, version)
                timings.append(timing)
            label = HTTP_VERSION_LABELS.get(version, f"HTTP/{version}")
            results.append((label, aggregate(timings)))
        return results

    def run_multiplex(self, tool: ToolAdapter) -> list[tuple[str, AggregatedResult]]:
        results = []
        urls = [self.config.url] * self.config.concurrency
        for version in self._versions_for_tool(tool):
            timings = []
            for _ in range(self.config.iterations):
                timing = tool.run_concurrent(urls, version)
                timings.append(timing)
            label = HTTP_VERSION_LABELS.get(version, f"HTTP/{version}")
            results.append((label, aggregate(timings)))
        return results

    def run_throughput(self, tool: ToolAdapter) -> list[tuple[str, AggregatedResult]]:
        results = []
        url = self.config.url
        if self.config.local_server and "/large" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url.rstrip('/')}/large{sep}size={self.config.download_size}"
        for version in self._versions_for_tool(tool):
            timings = []
            for _ in range(self.config.iterations):
                timing = tool.run(url, version)
                timings.append(timing)
            label = HTTP_VERSION_LABELS.get(version, f"HTTP/{version}")
            results.append((label, aggregate(timings)))
        return results

    def run_all(self) -> dict[str, dict[str, list[tuple[str, AggregatedResult]]]]:
        all_results: dict[str, dict[str, list[tuple[str, AggregatedResult]]]] = {}
        scenario_runners = {
            "latency": self.run_latency,
            "multiplex": self.run_multiplex,
            "throughput": self.run_throughput,
        }
        for scenario in self.config.scenarios:
            runner_fn = scenario_runners.get(scenario)
            if runner_fn is None:
                continue
            all_results[scenario] = {}
            for tool in self.tools:
                try:
                    all_results[scenario][tool.name] = runner_fn(tool)
                except RuntimeError as e:
                    print(f"  Warning: {tool.name} failed on {scenario}: {e}")
        return all_results
