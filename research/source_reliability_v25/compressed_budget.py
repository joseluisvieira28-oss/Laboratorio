"""Audit-only source GZIP budget guard. Frozen V2.4 files remain immutable.

A raw (uncompressed) byte count and the compressed file cursor have separate
limits. zlib can buffer output invisibly, so the guard conservatively accounts
for ALL raw input since the last gzip sync flush before allowing each write.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import BinaryIO

MIB = 1024 * 1024


@dataclass
class ByteBudget:
    max_compressed: int = 64 * MIB
    max_uncompressed: int = 256 * MIB
    reserve: int = 256 * 1024
    max_record: int = 2 * MIB + 8192
    final_record_reserve: int = 8192
    sync_interval_raw: int = 128 * 1024
    _raw_at_sync: int = field(default=0, init=False, repr=False)

    def decision(self, gzip_writer: BinaryIO, raw_written: int, next_line: bytes) -> str | None:
        """Return rejection reason *before* accepting another complete JSONL line.

        Expected caller contract: raw_written == total bytes already written
        to gzip_writer, with record sequence and hash advanced only AFTER
        decision is None. When rejecting, stop source streams and finalize
        a small terminal receipt within the reserved margin.
        """
        if not isinstance(next_line, bytes):
            raise TypeError("Expected serialized bytes")
        if len(next_line) > self.max_record:
            return "FRAME_SIZE_LIMIT"
        if raw_written + len(next_line) + self.final_record_reserve > self.max_uncompressed:
            return "UNCOMPRESSED_CAP"
        if raw_written < self._raw_at_sync:
            return "NONMONOTONIC_RAW_COUNTER"

        sink = getattr(gzip_writer, "fileobj", None)
        if sink is None or not hasattr(sink, "tell") or not hasattr(gzip_writer, "flush"):
            return "COMPRESSED_POSITION_UNAVAILABLE"
        try:
            if gzip_writer.tell() != raw_written:
                return "RAW_COUNTER_MISMATCH"
            # A bounded sync interval avoids the ~40% compressed-size
            # inflation observed in a synthetic flush-every-line benchmark.
            if raw_written - self._raw_at_sync >= self.sync_interval_raw:
                gzip_writer.flush()
                self._raw_at_sync = raw_written
            physically_written = sink.tell()
        except (OSError, ValueError, TypeError):
            return "COMPRESSED_POSITION_UNAVAILABLE"

        if physically_written < 0:
            return "COMPRESSED_POSITION_UNAVAILABLE"

        # Worst-case deflate bound for every byte pending in zlib plus the
        # next record. This cannot undercount unseen buffered input.
        pending_raw = raw_written - self._raw_at_sync
        future_raw = pending_raw + len(next_line)
        worst_case = future_raw + future_raw // 100 + 1024
        if physically_written + worst_case + self.reserve > self.max_compressed:
            # Reconcile pending compressed bytes before rejecting the record.
            try:
                gzip_writer.flush()
                self._raw_at_sync = raw_written
                physically_written = sink.tell()
            except (OSError, ValueError, TypeError):
                return "COMPRESSED_POSITION_UNAVAILABLE"
            candidate = len(next_line)
            if (physically_written + candidate + candidate // 100 + 1024
                    + self.reserve > self.max_compressed):
                return "COMPRESSED_CAP"
        return None


def gzip_positions(gzip_writer: BinaryIO) -> tuple[int, int]:
    """Diagnostic: logical uncompressed position versus compressed cursor."""
    return gzip_writer.tell(), gzip_writer.fileobj.tell()
