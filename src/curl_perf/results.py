"""Benchmark result data classes and aggregation."""

from dataclasses import dataclass
import math
import statistics


@dataclass
class TimingResult:
    """Timing data from a single benchmark run."""
    total_ms: float
    bytes_transferred: int
    http_version_used: str
    dns_ms: float | None = None
    connect_ms: float | None = None
    tls_ms: float | None = None
    ttfb_ms: float | None = None

    @property
    def transfer_rate_bps(self) -> float:
        if self.total_ms <= 0:
            return 0.0
        return self.bytes_transferred / (self.total_ms / 1000.0)


@dataclass
class AggregatedResult:
    mean: TimingResult
    median: TimingResult
    p95: TimingResult
    stddev: TimingResult
    count: int


TIMING_FIELDS = ["dns_ms", "connect_ms", "tls_ms", "ttfb_ms", "total_ms"]
OPTIONAL_TIMING_FIELDS = ["dns_ms", "connect_ms", "tls_ms", "ttfb_ms"]
INT_FIELDS = ["bytes_transferred"]


def _percentile(sorted_values: list[float], pct: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = math.ceil(pct / 100.0 * (len(sorted_values) - 1))
    return sorted_values[idx]


def _aggregate_field(values: list[float]) -> dict:
    sorted_vals = sorted(values)
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95": _percentile(sorted_vals, 95),
        "stddev": statistics.pstdev(values),
    }


def aggregate(results: list[TimingResult]) -> AggregatedResult:
    stats: dict[str, dict] = {}
    none_stats = {"mean": None, "median": None, "p95": None, "stddev": None}
    for field_name in TIMING_FIELDS:
        values = [getattr(r, field_name) for r in results]
        if field_name in OPTIONAL_TIMING_FIELDS and all(v is None for v in values):
            stats[field_name] = none_stats
        else:
            stats[field_name] = _aggregate_field([v if v is not None else 0.0 for v in values])
    for field_name in INT_FIELDS:
        values = [float(getattr(r, field_name)) for r in results]
        stats[field_name] = _aggregate_field(values)

    def _build_result(stat_key: str) -> TimingResult:
        return TimingResult(
            total_ms=stats["total_ms"][stat_key],
            bytes_transferred=int(stats["bytes_transferred"][stat_key]),
            http_version_used=results[0].http_version_used,
            dns_ms=stats["dns_ms"][stat_key],
            connect_ms=stats["connect_ms"][stat_key],
            tls_ms=stats["tls_ms"][stat_key],
            ttfb_ms=stats["ttfb_ms"][stat_key],
        )

    return AggregatedResult(
        mean=_build_result("mean"),
        median=_build_result("median"),
        p95=_build_result("p95"),
        stddev=_build_result("stddev"),
        count=len(results),
    )
