from curl_perf.results import TimingResult, aggregate


def test_timing_result_creation():
    r = TimingResult(
        dns_ms=1.0, connect_ms=2.0, tls_ms=3.0, ttfb_ms=5.0,
        total_ms=10.0, bytes_transferred=1024, http_version_used="2",
    )
    assert r.dns_ms == 1.0
    assert r.total_ms == 10.0
    assert r.bytes_transferred == 1024


def test_timing_result_transfer_rate():
    r = TimingResult(dns_ms=0, connect_ms=0, tls_ms=0, ttfb_ms=0,
                     total_ms=1000.0, bytes_transferred=1_000_000, http_version_used="2")
    assert r.transfer_rate_bps == 1_000_000.0


def test_timing_result_transfer_rate_zero_time():
    r = TimingResult(dns_ms=0, connect_ms=0, tls_ms=0, ttfb_ms=0,
                     total_ms=0.0, bytes_transferred=1024, http_version_used="2")
    assert r.transfer_rate_bps == 0.0


def _tr(total_ms=10.0, bytes_transferred=0, ttfb_ms=None, dns_ms=None,
        connect_ms=None, tls_ms=None):
    return TimingResult(
        total_ms=total_ms, bytes_transferred=bytes_transferred,
        http_version_used="2", dns_ms=dns_ms, connect_ms=connect_ms,
        tls_ms=tls_ms, ttfb_ms=ttfb_ms,
    )


def test_aggregate_mean():
    results = [
        _tr(total_ms=10, bytes_transferred=100, dns_ms=1, connect_ms=2, tls_ms=3, ttfb_ms=5),
        _tr(total_ms=20, bytes_transferred=200, dns_ms=3, connect_ms=4, tls_ms=5, ttfb_ms=7),
    ]
    agg = aggregate(results)
    assert agg.mean.total_ms == 15.0
    assert agg.mean.ttfb_ms == 6.0
    assert agg.mean.bytes_transferred == 150


def test_aggregate_median_odd():
    results = [_tr(total_ms=10), _tr(total_ms=20), _tr(total_ms=30)]
    agg = aggregate(results)
    assert agg.median.total_ms == 20.0


def test_aggregate_median_even():
    results = [_tr(total_ms=10), _tr(total_ms=20)]
    agg = aggregate(results)
    assert agg.median.total_ms == 15.0


def test_aggregate_p95():
    results = [_tr(total_ms=float(i)) for i in range(1, 21)]
    agg = aggregate(results)
    assert agg.p95.total_ms == 20.0


def test_aggregate_stddev():
    results = [_tr(total_ms=10), _tr(total_ms=10)]
    agg = aggregate(results)
    assert agg.stddev.total_ms == 0.0


def test_aggregate_single_result():
    results = [_tr(total_ms=10, bytes_transferred=100, dns_ms=1, connect_ms=2, tls_ms=3, ttfb_ms=5)]
    agg = aggregate(results)
    assert agg.mean.total_ms == 10.0
    assert agg.median.total_ms == 10.0
    assert agg.p95.total_ms == 10.0
    assert agg.stddev.total_ms == 0.0
    assert agg.count == 1


def test_aggregate_none_fields_propagate():
    results = [_tr(total_ms=10), _tr(total_ms=20)]
    agg = aggregate(results)
    assert agg.median.ttfb_ms is None
    assert agg.median.dns_ms is None
    assert agg.median.total_ms == 15.0
