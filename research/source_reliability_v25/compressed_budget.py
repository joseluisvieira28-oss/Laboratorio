"""Source-only GZIP byte-budget guard for a proposed V2.5 collector.

This is deliberately NOT wired into the frozen V2.4 collector. The original
V2.4 experiment must retain its recorded resource-cap failure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

MIB = 1024 * 1024


@dataclass(frozen=True)
class ByteBudget:
    # Freeze from V2.4: stream-byte limits (not GitHub artifact ZIP bytes).
    max_compressed: int = 64 * MIB
    max_uncompressed: int = 256 * MIB
    # Conservative safety margin for pending deflate bytes and gzip footer.
    reserve: int = 256 * 1024
    max_record: int = 2 * MIB + 8192
    final_record_reserve: int = 8192

    def decision(self, gzip_writer: BinaryIO, raw_written: int, next_line: bytes) -> str | None:
        """Return terminal gate reason BEFORE accepting next raw record.

        gzip.GzipFile.tell() returns UNCOMPRESSED position. The underlying
        fileobj.tell() is the compressed cursor, but can lag because zlib
        buffers output. Mandatory flush() makes it current before the gate.
        This is an offline safety candidate; its per-record flush overhead
        must be benchmarked before any future capture integration.
        """
        if not isinstance(next_line, bytes):
            raise TypeError("Serialized raw record must be bytes")
        if len(next_line) > self.max_record:
            return "FRAME_SIZE_LIMIT"
        if raw_written + len(next_line) + self.final_record_reserve > self.max_uncompressed:
            return "UNCOMPRESSED_CAP"
        sink = getattr(gzip_writer, "fileobj", None)
        if sink is None or not hasattr(sink, "tell") or not hasattr(gzip_writer, "flush"):
            return "COMPRESSED_POSITION_UNAVAILABLE"
        try:
            # CRITICAL: without a sync flush the underlying cursor can lag
            # enough for the final gzip file to exceed the frozen bound.
            gzip_writer.flush()
            physically_written = sink.tell()
        except (OSError, ValueError, TypeError):
            return "COMPRESSED_POSITION_UNAVAILABLE"
        if physically_written < 0:
            return "COMPRESSED_POSITION_UNAVAILABLE"
        # Worst-case bound for the NEXT record plus conservative trailer and
        # final receipt reserve; no scientific outcome depends on this guard.
        next_worst_case = len(next_line) + (len(next_line) // 100) + 1024
        if physically_written + next_worst_case + self.reserve > self.max_compressed:
            return "COMPRESSED_CAP"
        return None


def gzip_positions(gzip_writer: BinaryIO) -> tuple[int, int]:
    """Diagnostic only: logical (raw) versus physical (compressed) positions."""
    return gzip_writer.tell(), gzip_writer.fileobj.tell()
