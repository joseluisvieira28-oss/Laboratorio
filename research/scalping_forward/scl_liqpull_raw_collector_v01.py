#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LAB_ID = "SCL-LIQPULL-TOXICITY-FWD-001"
VERSION = "0.1"
WS_URL = "wss://api.hyperliquid.xyz/ws"
COIN = "BTC"
ALLOWED_CHANNELS = {"l2Book", "trades", "subscriptionResponse"}


def utc_ms() -> int:
    return time.time_ns() // 1_000_000


def monotonic_ns() -> int:
    return time.monotonic_ns()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def subscriptions() -> list[dict[str, Any]]:
    return [
        {"method": "subscribe", "subscription": {"type": "l2Book", "coin": COIN}},
        {"method": "subscribe", "subscription": {"type": "trades", "coin": COIN}},
    ]


def canonical_line(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass
class Stats:
    lines: int = 0
    parse_errors: int = 0
    reconnects: int = 0
    first_recv_ms: int | None = None
    last_recv_ms: int | None = None


class RawShardWriter:
    def __init__(self, out_dir: Path, protocol_commit: str):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.raw_path = self.out_dir / f"{LAB_ID}_{stamp}.jsonl"
        self.manifest_path = self.raw_path.with_suffix(".manifest.json")
        self.fh = self.raw_path.open("a", encoding="utf-8", buffering=1)
        self.stats = Stats()
        self.protocol_commit = protocol_commit
        self.started_utc_ms = utc_ms()

    def write(self, payload: Any, recv_mono_ns: int, recv_utc_ms: int) -> None:
        if not isinstance(payload, dict):
            self.stats.parse_errors += 1
            return
        channel = payload.get("channel")
        if channel not in ALLOWED_CHANNELS:
            channel = str(channel) if channel is not None else "UNKNOWN"
        row = {
            "lab_id": LAB_ID,
            "collector_version": VERSION,
            "protocol_commit": self.protocol_commit,
            "recv_monotonic_ns": recv_mono_ns,
            "recv_utc_ms": recv_utc_ms,
            "channel": channel,
            "provider_payload": payload,
        }
        self.fh.write(canonical_line(row) + "\n")
        self.stats.lines += 1
        if self.stats.first_recv_ms is None:
            self.stats.first_recv_ms = recv_utc_ms
        self.stats.last_recv_ms = recv_utc_ms

    def log_reconnect(self, reason: str) -> None:
        self.stats.reconnects += 1
        self.write(
            {"channel": "collectorBoundary", "data": {"event": "RECONNECT", "reason": reason[:500]}},
            monotonic_ns(),
            utc_ms(),
        )

    def close(self) -> None:
        if self.fh.closed:
            return
        self.fh.flush()
        os.fsync(self.fh.fileno())
        self.fh.close()
        manifest = {
            "schema_version": VERSION,
            "lab_id": LAB_ID,
            "protocol_commit": self.protocol_commit,
            "source": "Hyperliquid public mainnet WebSocket",
            "websocket": WS_URL,
            "coin": COIN,
            "subscriptions": [x["subscription"] for x in subscriptions()],
            "started_utc_ms": self.started_utc_ms,
            "closed_utc_ms": utc_ms(),
            "first_recv_utc_ms": self.stats.first_recv_ms,
            "last_recv_utc_ms": self.stats.last_recv_ms,
            "line_count": self.stats.lines,
            "parse_errors": self.stats.parse_errors,
            "reconnects": self.stats.reconnects,
            "raw_file": self.raw_path.name,
            "raw_sha256": sha256_file(self.raw_path),
            "outcomes_computed": False,
            "derived_features_computed": False,
            "authenticated_endpoint_used": False,
            "orders_sent": False,
            "exchange_mutation": False,
            "historical_backfill": False,
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


async def collect(duration_s: int, writer: RawShardWriter) -> None:
    try:
        import websockets
    except Exception as e:
        raise SystemExit("Missing dependency: pip install websockets") from e

    stop_at = time.monotonic() + duration_s
    backoff = 1.0
    while time.monotonic() < stop_at:
        try:
            async with websockets.connect(
                WS_URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_size=8 * 1024 * 1024,
            ) as ws:
                for sub in subscriptions():
                    await ws.send(canonical_line(sub))
                backoff = 1.0
                while time.monotonic() < stop_at:
                    timeout = min(30.0, max(0.1, stop_at - time.monotonic()))
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    recv_mono = monotonic_ns()
                    recv_utc = utc_ms()
                    try:
                        payload = json.loads(raw)
                    except Exception:
                        writer.stats.parse_errors += 1
                        continue
                    writer.write(payload, recv_mono, recv_utc)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            writer.log_reconnect(type(e).__name__ + ":" + str(e))
            if time.monotonic() >= stop_at:
                break
            await asyncio.sleep(min(backoff, max(0.0, stop_at - time.monotonic())))
            backoff = min(backoff * 2.0, 30.0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Raw public Hyperliquid BTC L2/trades forward collector. No outcomes or trading."
    )
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--duration-seconds", type=int, default=300)
    p.add_argument("--protocol-commit", default=os.environ.get("SCL_PROTOCOL_COMMIT", ""))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.protocol_commit or len(args.protocol_commit) < 7:
        raise SystemExit("Fail closed: --protocol-commit (or SCL_PROTOCOL_COMMIT) is required.")
    if args.duration_seconds < 10 or args.duration_seconds > 3600:
        raise SystemExit("Fail closed: duration must be between 10 and 3600 seconds per shard.")

    writer = RawShardWriter(args.out_dir, args.protocol_commit)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    stopped = False

    def _stop(*_):
        nonlocal stopped
        stopped = True
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except (NotImplementedError, RuntimeError):
            pass

    try:
        loop.run_until_complete(collect(args.duration_seconds, writer))
    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        loop.close()
    return 130 if stopped else 0


if __name__ == "__main__":
    raise SystemExit(main())
