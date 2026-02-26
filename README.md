# curl-perf

Performance benchmark tool for curl/libcurl and other HTTP clients.

Compares request latency, multiplexing, and throughput across tools and HTTP versions using subprocess-based adapters for fair measurement.

## Install

```bash
uv sync
```

Requires `curl` and optionally `wget2`,`xh`,etc on your PATH.

## Usage

```bash
# Benchmark against a URL
uv run curl-perf --url https://example.com

# Compare specific tools
uv run curl-perf --url https://example.com --tools curl,wget2

# Run specific scenarios
uv run curl-perf --url https://example.com --scenarios latency,multiplex,throughput

# Control iterations and concurrency
uv run curl-perf --url https://example.com -n 20 -c 15

# Save results to JSON
uv run curl-perf --url https://example.com -o results.json

# Use built-in local HTTP/2 test server
uv run curl-perf --local-server -n 10
```

## Options

```
--url URL             Target URL to benchmark
--iterations, -n N    Runs per scenario (default: 10)
--tools, -t LIST      Comma-separated tools (default: all available)
--scenarios, -s LIST  latency, multiplex, throughput (default: all)
--http-versions LIST  1.1, 2 (default: both)
--concurrency, -c N   Concurrent requests for multiplex (default: 10)
--download-size N     Response bytes for throughput (default: 10MB)
--output-json, -o F   Save raw results to JSON file
--local-server        Start built-in HTTP/2 test server
```

## Scenarios

**Latency** — Single request timing (DNS, connect, TLS, TTFB, total) for HTTP/1.1 vs HTTP/2.

**Multiplex** — N concurrent requests measuring HTTP/2 multiplexing vs HTTP/1.1 parallel connections.

**Throughput** — Large file download measuring transfer rate.

## Sample output

```
Tools: curl, wget2

Scenario: Single Request Latency (10 iterations)
------------------------------------------------------------------------------
Tool       Protocol     TTFB med  Total med        p95     stddev
------------------------------------------------------------------------------
curl       HTTP/1.1       42.3ms      48.1ms      55.2ms       4.1ms
curl       HTTP/2         38.1ms      43.7ms      50.6ms       3.5ms
wget2      HTTP/1.1        0.0ms      50.6ms      56.2ms       4.8ms
wget2      HTTP/2          0.0ms      45.3ms      51.7ms       3.9ms
```

curl provides detailed timing breakdown (TTFB, DNS, TLS). wget2 reports wall-clock total only.

## Adding a tool

Create `src/curl_perf/tools/newtool.py`:

```python
from curl_perf.tools.base import ToolAdapter
from curl_perf.results import TimingResult

class NewToolAdapter(ToolAdapter):
    name = "newtool"

    def is_available(self) -> bool: ...
    def supports_http2(self) -> bool: ...
    def run(self, url, http_version="2") -> TimingResult: ...
    def run_concurrent(self, urls, http_version="2") -> TimingResult: ...
```

Then add it to `ALL_ADAPTERS` in `src/curl_perf/tools/__init__.py`.

## Tests

```bash
uv run pytest tests/ -v
```

# Example run


```commandline
uv run curl-perf --local-server --iterations 100 --scenarios latency,multiplex,throughput --http-versions 1.1,2  
      2>&1
Tools: curl, httpie, wget2, xh
Local server started at https://127.0.0.1:8443

Scenario: Single Request Latency (100 iterations)
------------------------------------------------------------------------------
Tool       Protocol     TTFB med  Total med        p95     stddev
------------------------------------------------------------------------------
curl       HTTP/1.1         2.8ms       2.8ms       3.5ms       0.4ms
curl       HTTP/2           3.1ms       3.2ms       4.0ms       0.4ms
httpie     HTTP/1.1            -     343.1ms     374.2ms      34.6ms
wget2      HTTP/1.1            -       6.7ms       7.4ms       0.4ms
wget2      HTTP/2              -       7.2ms       8.0ms       0.4ms
xh         HTTP/1.1            -      14.8ms      16.0ms       0.6ms
xh         HTTP/2              -      15.3ms      16.4ms       0.6ms


Scenario: Concurrent Multiplexing (10 requests) (100 iterations)
------------------------------------------------------------------------------
Tool       Protocol     TTFB med  Total med        p95     stddev
------------------------------------------------------------------------------
curl       HTTP/1.1         7.9ms      13.1ms      16.3ms       1.3ms
curl       HTTP/2           4.2ms       9.2ms      11.2ms       0.9ms
httpie     HTTP/1.1            -     435.1ms     482.9ms      27.7ms
wget2      HTTP/1.1            -       7.1ms       8.5ms       0.6ms
wget2      HTTP/2              -       7.7ms       9.2ms       5.0ms
xh         HTTP/1.1            -      24.6ms      28.7ms       2.0ms
xh         HTTP/2              -      29.1ms      32.7ms       3.2ms


Scenario: Throughput (100 iterations)
------------------------------------------------------------------------------
Tool       Protocol    Total med     Rate med        p95     stddev
------------------------------------------------------------------------------
curl       HTTP/1.1        17.2ms   607.9 MB/s      19.1ms       3.7ms
curl       HTTP/2          22.0ms   476.2 MB/s      26.1ms       6.1ms
httpie     HTTP/1.1       342.3ms        0 B/s     375.1ms      19.3ms
wget2      HTTP/1.1        27.6ms        0 B/s      30.1ms       1.3ms
wget2      HTTP/2          23.9ms        0 B/s      29.0ms      20.1ms
xh         HTTP/1.1        16.7ms        0 B/s      18.5ms       1.6ms
xh         HTTP/2          19.4ms        0 B/s      21.2ms       1.4ms

Local server stopped

```