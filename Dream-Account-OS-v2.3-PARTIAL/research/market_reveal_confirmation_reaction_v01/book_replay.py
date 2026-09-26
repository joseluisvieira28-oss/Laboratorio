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

    venues = {row.venue for row in batch}
    symbols = {row.native_symbol for row in batch}
    sequences = {(row.sequence_first, row.sequence_last) for row in batch}
    if len(venues) != 1:
        raise ValueError("book update batch has mixed venues")
    if len(symbols) != 1:
        raise ValueError("book update batch has mixed symbols")
    if len(sequences) != 1:
        raise ValueError("book update batch has mixed sequence identifiers")

    times = [canonical_book_time_ns(row) for row in batch]
    venue = batch[0].venue

    if venue == "BINANCE_SPOT":
        if len(set(times)) != 1:
            raise ValueError("Binance depth event has mixed source timestamps")
        return times[0]

    if venue == "COINBASE_ADVANCED_SPOT":
        # One level2 message can carry multiple price-level updates. The resulting
        # post-batch book state cannot exist before the latest engine timestamp
        # represented inside that message.
        return max(times)

    raise ValueError(f"unsupported venue: {venue}")


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
