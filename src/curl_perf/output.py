"""Output formatting for benchmark results."""

import json
from typing import IO

from curl_perf.results import AggregatedResult


def _fmt_ms(value: float | None) -> str:
    if value is None:
        return f"{'-':>10}"
    return f"{value:>9.1f}ms"


def format_table(
    scenario: str,
    rows: list[tuple[str, str, AggregatedResult]],
    iterations: int,
) -> str:
    lines = []
    lines.append(f"\nScenario: {scenario} ({iterations} iterations)")
    lines.append("-" * 78)
    header = (
        f"{'Tool':<10} {'Protocol':<10} {'TTFB med':>10} "
        f"{'Total med':>10} {'p95':>10} {'stddev':>10}"
    )
    lines.append(header)
    lines.append("-" * 78)
    for tool_name, protocol, agg in rows:
        line = (
            f"{tool_name:<10} {protocol:<10} "
            f"{_fmt_ms(agg.median.ttfb_ms)} "
            f"{_fmt_ms(agg.median.total_ms)} "
            f"{_fmt_ms(agg.p95.total_ms)} "
            f"{_fmt_ms(agg.stddev.total_ms)}"
        )
        lines.append(line)
    lines.append("")
    return "\n".join(lines)


def format_throughput_table(
    rows: list[tuple[str, str, AggregatedResult]],
    iterations: int,
) -> str:
    lines = []
    lines.append(f"\nScenario: Throughput ({iterations} iterations)")
    lines.append("-" * 78)
    header = (
        f"{'Tool':<10} {'Protocol':<10} {'Total med':>10} "
        f"{'Rate med':>12} {'p95':>10} {'stddev':>10}"
    )
    lines.append(header)
    lines.append("-" * 78)
    for tool_name, protocol, agg in rows:
        rate = agg.median.transfer_rate_bps
        if rate > 1_000_000:
            rate_str = f"{rate / 1_000_000:.1f} MB/s"
        elif rate > 1_000:
            rate_str = f"{rate / 1_000:.1f} KB/s"
        else:
            rate_str = f"{rate:.0f} B/s"
        line = (
            f"{tool_name:<10} {protocol:<10} "
            f"{_fmt_ms(agg.median.total_ms)} "
            f"{rate_str:>12} "
            f"{_fmt_ms(agg.p95.total_ms)} "
            f"{_fmt_ms(agg.stddev.total_ms)}"
        )
        lines.append(line)
    lines.append("")
    return "\n".join(lines)


def write_json(results: dict, output: IO[str]) -> None:
    json.dump(results, output, indent=2, default=str)
    output.write("\n")
