"""Bounded deterministic replay from canonical book batches to book metrics.

No source network access and no target/outcome logic.
"""

from __future__ import annotations

from typing import Sequence

from decision_boundary import epoch_ms_to_ns, rfc3339_to_ns
from order_book import DepthSpec, LocalOrderBook
from source_adapters import CanonicalBookUpdate
from state_reconstruction import TimedBookMetrics


def canonical_book_time_ns(update: CanonicalBookUpdate) -> int:
    if update.venue == "BINANCE_SPOT":
        return epoch_ms_to_ns(update.source_event_time)
    if update.venue == "COINBASE_ADVANCED_SPOT":
        return rfc3339_to_ns(update.source_event_time)
    raise ValueError(f"unsupported venue: {update.venue}")


def batch_time_ns(batch: Sequence[CanonicalBookUpdate]) -> int:
    if not batch:
        raise ValueError("book update batch is empty")
    times = {canonical_book_time_ns(row) for row in batch}
    if len(times) != 1:
        raise ValueError("book update batch has mixed source timestamps")
    return next(iter(times))


def initial_observation(
    *,
    book: LocalOrderBook,
    timestamp_ns: int,
    depth_spec: DepthSpec,
) -> TimedBookMetrics:
    return TimedBookMetrics(
        timestamp_ns=int(timestamp_ns),
        metrics=book.metrics(depth_spec),
    )


def replay_incremental_batches(
    *,
    book: LocalOrderBook,
    batches: Sequence[Sequence[CanonicalBookUpdate]],
    depth_spec: DepthSpec,
    decision_ns: int,
) -> tuple[TimedBookMetrics, ...]:
    observations: list[TimedBookMetrics] = []

    for batch in batches:
        timestamp_ns = batch_time_ns(batch)
        if timestamp_ns > decision_ns:
            raise ValueError(
                "future book batch supplied to feature replay: "
                f"batch_time={timestamp_ns}, decision={decision_ns}"
            )

        result = book.apply_updates(batch)
        if result.status == "APPLIED":
            observations.append(
                TimedBookMetrics(
                    timestamp_ns=timestamp_ns,
                    metrics=book.metrics(depth_spec),
                )
            )

    return tuple(observations)
