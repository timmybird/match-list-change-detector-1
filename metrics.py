#!/usr/bin/env python3
"""
Prometheus metrics for the match list change detector.

Provides classes and functions to record and expose metrics.
"""

import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple

from prometheus_client import Counter, Gauge, Histogram, start_http_server


# Define StartResponse type for WSGI
class StartResponse(Protocol):
    """Protocol for WSGI start_response callable."""

    def __call__(
        self, status: str, headers: List[Tuple[str, str]], exc_info: Optional[Any] = None
    ) -> None:
        """Call the start_response function."""
        ...


# Define metrics
class Metrics:
    """Prometheus metrics for the Match List Change Detector."""

    def __init__(self, port: int = 8000):
        """
        Initialize metrics.

        Args:
            port: Port to expose metrics on
        """
        # Counters
        self.matches_total = Counter(
            "match_list_change_detector_matches_total", "Total number of matches processed"
        )

        self.changes_total = Counter(
            "match_list_change_detector_changes_total",
            "Total number of changes detected",
            ["type"],  # new, removed, changed
        )

        self.errors_total = Counter(
            "match_list_change_detector_errors_total", "Total number of errors"
        )

        self.fetch_failures_total = Counter(
            "match_list_change_detector_fetch_failures_total",
            "Total number of match list fetch failures",
        )

        self.orchestrator_triggers_total = Counter(
            "match_list_change_detector_orchestrator_triggers_total",
            "Total number of orchestrator triggers",
        )

        self.orchestrator_failures_total = Counter(
            "match_list_change_detector_orchestrator_failures_total",
            "Total number of orchestrator trigger failures",
        )

        # Gauges
        self.processing_time_seconds = Gauge(
            "match_list_change_detector_processing_time_seconds", "Time taken to process match list"
        )

        self.last_run_timestamp = Gauge(
            "match_list_change_detector_last_run_timestamp", "Timestamp of last run"
        )

        self.up = Gauge(
            "match_list_change_detector_up",
            "Whether the Match List Change Detector is up (1) or down (0)",
        )

        # Histograms
        self.api_response_time_seconds = Histogram(
            "match_list_change_detector_api_response_time_seconds",
            "API response time in seconds",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
        )

        # Start metrics server in a separate thread
        self.server_thread = threading.Thread(target=self._start_server, args=(port,))
        self.server_thread.daemon = True
        self.server_thread.start()

        # Set up as running
        self.up.set(1)

    def _start_server(self, port: int) -> None:
        """
        Start the metrics server.

        Args:
            port: Port to expose metrics on
        """
        start_http_server(port)

    def record_matches(self, count: int) -> None:
        """
        Record the number of matches processed.

        Args:
            count: Number of matches
        """
        self.matches_total.inc(count)

    def record_changes(self, new: int = 0, removed: int = 0, changed: int = 0) -> None:
        """
        Record the number of changes detected.

        Args:
            new: Number of new matches
            removed: Number of removed matches
            changed: Number of changed matches
        """
        self.changes_total.labels(type="new").inc(new)
        self.changes_total.labels(type="removed").inc(removed)
        self.changes_total.labels(type="changed").inc(changed)

    def record_error(self) -> None:
        """Record an error."""
        self.errors_total.inc()

    def record_fetch_failure(self) -> None:
        """Record a match list fetch failure."""
        self.fetch_failures_total.inc()

    def record_orchestrator_trigger(self) -> None:
        """Record an orchestrator trigger."""
        self.orchestrator_triggers_total.inc()

    def record_orchestrator_failure(self) -> None:
        """Record an orchestrator trigger failure."""
        self.orchestrator_failures_total.inc()

    def record_processing_time(self, seconds: float) -> None:
        """
        Record the time taken to process the match list.

        Args:
            seconds: Time in seconds
        """
        self.processing_time_seconds.set(seconds)

    def record_run(self) -> None:
        """Record a run of the Match List Change Detector."""
        self.last_run_timestamp.set(time.time())

    def time_api_request(self) -> "ApiRequestTimer":
        """
        Time an API request.

        Returns:
            Context manager for timing API requests
        """
        return ApiRequestTimer(self.api_response_time_seconds)


class ApiRequestTimer:
    """Context manager for timing API requests."""

    histogram: Histogram
    start: float

    def __init__(self, histogram: Histogram) -> None:
        """
        Initialize the timer.

        Args:
            histogram: Prometheus histogram to record time in
        """
        self.histogram = histogram

    def __enter__(self) -> "ApiRequestTimer":
        """Start the timer."""
        self.start = time.time()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Any) -> None:
        """
        Stop the timer and record the time.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.histogram.observe(time.time() - self.start)


# Create a global metrics instance
metrics = Metrics()


# Health check endpoint handler
def health_check_handler(environ: Dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
    """
    Handle health check requests.

    Args:
        environ: WSGI environment
        start_response: WSGI start_response function

    Returns:
        Response body
    """
    status = "200 OK"
    headers = [("Content-type", "application/json")]
    start_response(status, headers)
    return [b'{"status":"ok"}']
