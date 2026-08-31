"""In-memory operational metrics collector (TASK 12).

Thread-safe, zero-dependency metrics store for API and ML inference telemetry.
Deliberately lightweight — no Prometheus/StatsD required.  The /api/v1/metrics
endpoint serialises the current snapshot via `get_metrics_snapshot()`.

Metrics tracked
---------------
API-level
    api_requests_total          – every incoming HTTP request
    api_errors_total            – any HTTP >= 400 response
    api_latency_ms_total        – sum of all request durations (for avg calc)

Prediction-level
    prediction_requests_total   – POST /predict or GET /predict/{id} calls
    prediction_errors_total     – failed prediction attempts
    prediction_latency_ms_total – cumulative inference duration

Data quality
    data_quality_failures_total – records that failed DQ gate

Monitoring
    drift_alerts_total          – drift scans that returned WARNING or CRITICAL
    model_load_total            – model registry look-ups / loads

Usage::

    from backend.app.core.metrics import metrics_collector
    metrics_collector.inc("prediction_requests_total")
    metrics_collector.observe("prediction_latency_ms", 14.2)
    snapshot = metrics_collector.get_snapshot()
"""

import threading
import time
from datetime import datetime, timezone
from typing import Any


class _MetricsCollector:
    """Minimal thread-safe counters + gauge store."""

    _COUNTER_KEYS = (
        "api_requests_total",
        "api_errors_total",
        "prediction_requests_total",
        "prediction_errors_total",
        "data_quality_failures_total",
        "drift_alerts_total",
        "model_load_total",
        "model_integrity_failures_total",
    )

    _LATENCY_KEYS = (
        "api_latency_ms",
        "prediction_latency_ms",
    )

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start_time = time.time()

        # Counters
        self._counters: dict[str, int] = {k: 0 for k in self._COUNTER_KEYS}

        # Latency accumulators: {key: [sum, count, min, max]}
        self._latency: dict[str, list[float]] = {
            k: [0.0, 0, float("inf"), 0.0] for k in self._LATENCY_KEYS
        }

        # Endpoint-level counters: {path: {total, errors}}
        self._endpoint_stats: dict[str, dict[str, int]] = {}

    # ------------------------------------------------------------------
    # Public mutators
    # ------------------------------------------------------------------

    def inc(self, key: str, amount: int = 1) -> None:
        """Increment a named counter."""
        with self._lock:
            if key in self._counters:
                self._counters[key] += amount

    def inc_endpoint(self, path: str, is_error: bool = False) -> None:
        """Track per-endpoint hit / error count."""
        with self._lock:
            if path not in self._endpoint_stats:
                self._endpoint_stats[path] = {"total": 0, "errors": 0}
            self._endpoint_stats[path]["total"] += 1
            if is_error:
                self._endpoint_stats[path]["errors"] += 1

    def observe(self, key: str, value_ms: float) -> None:
        """Record a latency sample in milliseconds."""
        with self._lock:
            if key not in self._latency:
                return
            bucket = self._latency[key]
            bucket[0] += value_ms          # sum
            bucket[1] += 1                  # count
            bucket[2] = min(bucket[2], value_ms)  # min
            bucket[3] = max(bucket[3], value_ms)  # max

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def get_snapshot(self) -> dict[str, Any]:
        """Return a safe, serialisable metrics snapshot (no secrets, no PII)."""
        with self._lock:
            uptime_s = round(time.time() - self._start_time)

            def _latency_summary(key: str) -> dict[str, float]:
                s, n, mn, mx = self._latency[key]
                avg = round(s / n, 2) if n > 0 else 0.0
                return {
                    "avg_ms": avg,
                    "min_ms": round(mn, 2) if n > 0 else 0.0,
                    "max_ms": round(mx, 2) if n > 0 else 0.0,
                    "count": n,
                }

            api_total = self._counters["api_requests_total"]
            api_errors = self._counters["api_errors_total"]
            error_rate = round(api_errors / api_total, 4) if api_total > 0 else 0.0

            return {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime_s,
                "api": {
                    "requests_total": api_total,
                    "errors_total": api_errors,
                    "error_rate": error_rate,
                    "latency": _latency_summary("api_latency_ms"),
                },
                "predictions": {
                    "requests_total": self._counters["prediction_requests_total"],
                    "errors_total": self._counters["prediction_errors_total"],
                    "latency": _latency_summary("prediction_latency_ms"),
                },
                "data_quality": {
                    "failures_total": self._counters["data_quality_failures_total"],
                },
                "model": {
                    "load_total": self._counters["model_load_total"],
                    "integrity_failures_total": self._counters["model_integrity_failures_total"],
                },
                "monitoring": {
                    "drift_alerts_total": self._counters["drift_alerts_total"],
                },
                "endpoints": dict(self._endpoint_stats),
            }

    def reset(self) -> None:
        """Reset all counters (used in tests only)."""
        with self._lock:
            for k in self._counters:
                self._counters[k] = 0
            for k in self._latency:
                self._latency[k] = [0.0, 0, float("inf"), 0.0]
            self._endpoint_stats.clear()
            self._start_time = time.time()


# Singleton — import this everywhere
metrics_collector = _MetricsCollector()
