"""CLI entry point for curl-perf."""

import argparse
import sys

from curl_perf.output import format_table, format_throughput_table, write_json
from curl_perf.runner import BenchmarkConfig, BenchmarkRunner
from curl_perf.server import LocalServer
from curl_perf.tools import ALL_ADAPTERS, get_available_tools, get_tool


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="curl-perf",
        description="HTTP/2 performance benchmark tool for curl and other HTTP clients",
    )
    parser.add_argument("--url", help="Target URL to benchmark")
    parser.add_argument(
        "--iterations", "-n", type=int, default=10,
        help="Number of iterations per scenario (default: 10)",
    )
    parser.add_argument(
        "--tools", "-t",
        help="Comma-separated list of tools to test (default: all available)",
    )
    parser.add_argument(
        "--scenarios", "-s",
        default="latency,multiplex,throughput",
        help="Comma-separated scenarios: latency,multiplex,throughput (default: all)",
    )
    parser.add_argument(
        "--http-versions",
        default="1.1,2",
        help="Comma-separated HTTP versions to test (default: 1.1,2)",
    )
    parser.add_argument(
        "--output-json", "-o",
        help="Save raw results to JSON file",
    )
    parser.add_argument(
        "--local-server", action="store_true",
        help="Start built-in HTTP/2 test server",
    )
    parser.add_argument(
        "--concurrency", "-c", type=int, default=10,
        help="Concurrent requests for multiplex scenario (default: 10)",
    )
    parser.add_argument(
        "--download-size", type=int, default=10 * 1024 * 1024,
        help="Response size in bytes for throughput scenario (default: 10MB)",
    )
    parser.add_argument(
        "--list-tools", action="store_true",
        help="List all known tools and their availability, then exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # List tools mode
    if args.list_tools:
        for cls in ALL_ADAPTERS:
            adapter = cls()
            avail = "available" if adapter.is_available() else "not found"
            h2 = "HTTP/2" if adapter.supports_http2() else "HTTP/1.1 only"
            print(f"  {adapter.name:15s} {avail:12s}  {h2}")
        return 0

    # Resolve tools
    if args.tools:
        tool_names = [t.strip() for t in args.tools.split(",")]
        tools = []
        for name in tool_names:
            tool = get_tool(name)
            if tool is None:
                print(f"Error: tool '{name}' not found or not installed", file=sys.stderr)
                return 1
            tools.append(tool)
    else:
        tools = get_available_tools()

    if not tools:
        print("Error: no tools available", file=sys.stderr)
        return 1

    print(f"Tools: {', '.join(t.name for t in tools)}")

    # Resolve URL
    server = None
    url = args.url
    if args.local_server:
        server = LocalServer()
        url = server.start()
        print(f"Local server started at {url}")
    elif not url:
        print("Error: --url required (or use --local-server)", file=sys.stderr)
        return 1

    try:
        config = BenchmarkConfig(
            url=url,
            iterations=args.iterations,
            concurrency=args.concurrency,
            download_size=args.download_size,
            http_versions=[v.strip() for v in args.http_versions.split(",")],
            scenarios=[s.strip() for s in args.scenarios.split(",")],
            local_server=args.local_server,
        )

        runner = BenchmarkRunner(config, tools)
        all_results = runner.run_all()

        # Format and print results
        json_output = {"config": {"url": url, "iterations": args.iterations}, "scenarios": {}}

        for scenario, tool_results in all_results.items():
            rows = []
            json_scenario = []
            for tool_name, version_results in tool_results.items():
                for protocol, agg in version_results:
                    rows.append((tool_name, protocol, agg))
                    json_scenario.append({
                        "tool": tool_name,
                        "protocol": protocol,
                        "mean_total_ms": agg.mean.total_ms,
                        "median_total_ms": agg.median.total_ms,
                        "median_ttfb_ms": agg.median.ttfb_ms,
                        "p95_total_ms": agg.p95.total_ms,
                        "stddev_total_ms": agg.stddev.total_ms,
                        "count": agg.count,
                    })

            if scenario == "throughput":
                print(format_throughput_table(rows, args.iterations))
            else:
                label = {
                    "latency": "Single Request Latency",
                    "multiplex": f"Concurrent Multiplexing ({args.concurrency} requests)",
                }.get(scenario, scenario)
                print(format_table(label, rows, args.iterations))

            json_output["scenarios"][scenario] = json_scenario

        # Write JSON if requested
        if args.output_json:
            with open(args.output_json, "w") as f:
                write_json(json_output, f)
            print(f"Results saved to {args.output_json}")

    finally:
        if server:
            server.stop()
            print("Local server stopped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
