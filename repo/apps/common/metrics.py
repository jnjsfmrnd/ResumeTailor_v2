from __future__ import annotations

import logging
from contextlib import contextmanager
from time import perf_counter

logger = logging.getLogger("apps.metrics")


@contextmanager
def timed_operation(name: str, *, threshold_seconds: float | None = None):
    started_at = perf_counter()
    try:
        yield
    finally:
        elapsed = perf_counter() - started_at
        logger.info("metric=%s duration_seconds=%.3f", name, elapsed)
        if threshold_seconds is not None and elapsed > threshold_seconds:
            logger.warning(
                "metric=%s status=threshold_exceeded duration_seconds=%.3f threshold_seconds=%.3f",
                name,
                elapsed,
                threshold_seconds,
            )


def record_latency(
    name: str,
    elapsed_seconds: float,
    *,
    threshold_seconds: float | None = None,
) -> None:
    logger.info("metric=%s duration_seconds=%.3f", name, elapsed_seconds)
    if threshold_seconds is not None and elapsed_seconds > threshold_seconds:
        logger.warning(
            "metric=%s status=threshold_exceeded duration_seconds=%.3f threshold_seconds=%.3f",
            name,
            elapsed_seconds,
            threshold_seconds,
        )