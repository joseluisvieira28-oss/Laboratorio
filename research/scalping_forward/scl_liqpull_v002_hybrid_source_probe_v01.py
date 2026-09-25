#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

import aiohttp
import websockets

LAB_ID = "SCL-LIQPULL-TOXICITY-FWD-002"
VERSION = "0.1"
INFO_URL = "https://api.hyperliquid.xyz/info"
WS_URL = "wss://api.hyperliquid.xyz/ws"
COIN = "BTC"
POLL_HZ = 4.0
DEFAULT_DURATION = 120
TARGET_POLLS = int(DEFAULT_DURATION * POLL_HZ)


def utc_ms() -> int:
    return time.time_ns() // 1_000_000


def mono_ns() -> int:
    return time.monotonic_ns()


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pct(values: list[float], p: float) -> float | None:
    vals = sorted(v for v in values if math.isfinite(v))
    if not vals:
        return None
    k = (len(vals) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return float(vals[lo])
    return float(vals[lo] * (hi - k) + vals[hi] * (k - lo))


def valid_book(obj: Any) -> tuple[bool, int | None]:
    if not isinstance(obj, dict):
        return False, None
    if obj.get("coin") != COIN:
        return False, None
    levels = obj.get("levels")
    if not isinstance(levels, list) or len(levels) != 2:
        return False, None
    if not levels[0] or not levels[1]:
        return False, None
    try:
        t = int(obj["time"])
        for side in levels:
            for lv in side[:5]:
                px = float(lv["px"])
                sz = float(lv["sz"])
                _n = int(lv.get("n", 0))
                if not (math.isfinite(px) and px > 0 and math.isfinite(sz) and sz > 0):
                    return False, None
        if float(levels[0][0]["px"]) >= float(levels[1][0]["px"]):
            return False, None
    except Exception:
        return False, None
    return True, t


async def rest_probe(duration: int, raw_path: Path) -> dict:
    interval = 1.0 / POLL_HZ
    target = int(duration * POLL_HZ)
    send_ms: list[int] = []
    recv_ms: list[int] = []
    provider_ms: list[int] = []
    success = 0
    http_errors = 0
    transport_errors = 0
    schema_errors = 0
    status_counts: dict[str, int] = {}

    timeout = aiohttp.ClientTimeout(total=3.0, connect=2.0, sock_read=2.0)
    connector = aiohttp.TCPConnector(limit=8, ttl_dns_cache=300)
    start = time.monotonic()

    with raw_path.open("w", encoding="utf-8", buffering=1) as fh:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            for i in range(target):
                due = start + i * interval
                delay = due - time.monotonic()
                if delay > 0:
                    await asyncio.sleep(delay)
                s_utc = utc_ms()
                s_mono = mono_ns()
                try:
                    async with session.post(
                        INFO_URL,
                        json={"type": "l2Book", "coin": COIN},
                        headers={"Content-Type": "application/json"},
                    ) as resp:
                        body = await resp.text()
                        r_utc = utc_ms()
                        r_mono = mono_ns()
                        status_counts[str(resp.status)] = status_counts.get(str(resp.status), 0) + 1
                        if resp.status != 200:
                            http_errors += 1
                            fh.write(canonical({
                                "kind": "rest_l2_error",
                                "send_utc_ms": s_utc,
                                "recv_utc_ms": r_utc,
                                "send_monotonic_ns": s_mono,
                                "recv_monotonic_ns": r_mono,
                                "status": resp.status,
                                "body_prefix": body[:300],
                            }) + "\n")
                            continue
                        try:
                            data = json.loads(body)
                        except Exception:
                            schema_errors += 1
                            continue
                        ok, pt = valid_book(data)
                        if not ok or pt is None:
                            schema_errors += 1
                            fh.write(canonical({
                                "kind": "rest_l2_schema_error",
                                "send_utc_ms": s_utc,
                                "recv_utc_ms": r_utc,
                                "provider_payload": data,
                            }) + "\n")
                            continue
                        success += 1
                        send_ms.append(s_utc)
                        recv_ms.append(r_utc)
                        provider_ms.append(pt)
                        fh.write(canonical({
                            "kind": "rest_l2",
                            "lab_id": LAB_ID,
                            "source_version": VERSION,
                            "send_utc_ms": s_utc,
                            "recv_utc_ms": r_utc,
                            "send_monotonic_ns": s_mono,
                            "recv_monotonic_ns": r_mono,
                            "provider_payload": data,
                        }) + "\n")
                except Exception as e:
                    transport_errors += 1
                    fh.write(canonical({
                        "kind": "rest_l2_transport_error",
                        "send_utc_ms": s_utc,
                        "error_type": type(e).__name__,
                        "error": str(e)[:300],
                    }) + "\n")

    gaps = [b - a for a, b in zip(recv_ms, recv_ms[1:])]
    stale = [abs(r - p) for r, p in zip(recv_ms, provider_ms)]
    monotonic_ok = all(b >= a for a, b in zip(provider_ms, provider_ms[1:]))
    total_errors = http_errors + transport_errors + schema_errors
    return {
        "target_polls": target,
        "successful_l2_responses": success,
        "http_errors": http_errors,
        "transport_errors": transport_errors,
        "schema_errors": schema_errors,
        "total_error_fraction": total_errors / target if target else 1.0,
        "http_status_counts": status_counts,
        "provider_timestamp_non_decreasing": monotonic_ok,
        "inter_response_gap_median_ms": statistics.median(gaps) if gaps else None,
        "inter_response_gap_p95_ms": pct([float(x) for x in gaps], 0.95),
        "provider_staleness_abs_p95_ms": pct([float(x) for x in stale], 0.95),
        "raw_sha256": sha256_file(raw_path),
    }


async def ws_probe(duration: int, raw_path: Path) -> dict:
    counts: dict[str, int] = {}
    subscription_acks: set[str] = set()
    parse_errors = 0
    reconnects = 0
    start = time.monotonic()

    with raw_path.open("w", encoding="utf-8", buffering=1) as fh:
        while time.monotonic() - start < duration:
            try:
                async with websockets.connect(
                    WS_URL,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                    max_size=8 * 1024 * 1024,
                ) as ws:
                    for typ in ("bbo", "trades"):
                        await ws.send(canonical({
                            "method": "subscribe",
                            "subscription": {"type": typ, "coin": COIN},
                        }))
                    while time.monotonic() - start < duration:
                        left = duration - (time.monotonic() - start)
                        if left <= 0:
                            break
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=min(30.0, left))
                        except asyncio.TimeoutError:
                            continue
                        r_utc = utc_ms()
                        r_mono = mono_ns()
                        try:
                            obj = json.loads(raw)
                        except Exception:
                            parse_errors += 1
                            continue
                        ch = str(obj.get("channel", "UNKNOWN"))
                        counts[ch] = counts.get(ch, 0) + 1
                        if ch == "subscriptionResponse":
                            data = obj.get("data")
                            if isinstance(data, dict):
                                sub = data.get("subscription")
                                if isinstance(sub, dict) and sub.get("coin") == COIN:
                                    typ = sub.get("type")
                                    if typ in {"bbo", "trades"}:
                                        subscription_acks.add(str(typ))
                        fh.write(canonical({
                            "kind": "ws",
                            "lab_id": LAB_ID,
                            "source_version": VERSION,
                            "recv_utc_ms": r_utc,
                            "recv_monotonic_ns": r_mono,
                            "provider_payload": obj,
                        }) + "\n")
                    break
            except Exception as e:
                reconnects += 1
                fh.write(canonical({
                    "kind": "ws_reconnect",
                    "recv_utc_ms": utc_ms(),
                    "error_type": type(e).__name__,
                    "error": str(e)[:300],
                }) + "\n")
                if time.monotonic() - start >= duration:
                    break
                await asyncio.sleep(1.0)

    return {
        "message_counts": counts,
        "subscription_acks": sorted(subscription_acks),
        "parse_errors": parse_errors,
        "reconnects": reconnects,
        "bbo_messages": counts.get("bbo", 0),
        "trade_messages": counts.get("trades", 0),
        "raw_sha256": sha256_file(raw_path),
    }


def adjudicate(rest: dict, ws: dict) -> dict:
    target = rest["target_polls"]
    required_success = math.ceil(target * 0.95)
    rest_gates = {
        "success_ge_95pct_target": rest["successful_l2_responses"] >= required_success,
        "error_fraction_le_1pct": rest["total_error_fraction"] <= 0.01,
        "schema_valid_all_success": rest["schema_errors"] == 0,
        "provider_timestamp_non_decreasing": bool(rest["provider_timestamp_non_decreasing"]),
        "median_gap_le_400ms": rest["inter_response_gap_median_ms"] is not None
            and rest["inter_response_gap_median_ms"] <= 400,
        "p95_gap_le_750ms": rest["inter_response_gap_p95_ms"] is not None
            and rest["inter_response_gap_p95_ms"] <= 750,
        "p95_staleness_le_1500ms": rest["provider_staleness_abs_p95_ms"] is not None
            and rest["provider_staleness_abs_p95_ms"] <= 1500,
    }
    ws_gates = {
        "bbo_ack": "bbo" in ws["subscription_acks"],
        "trades_ack": "trades" in ws["subscription_acks"],
        "parse_errors_zero": ws["parse_errors"] == 0,
        "reconnects_zero": ws["reconnects"] == 0,
        "bbo_present": ws["bbo_messages"] > 0,
        "trades_present": ws["trade_messages"] > 0,
    }
    passed = all(rest_gates.values()) and all(ws_gates.values())
    return {
        "lab_id": LAB_ID,
        "source_gate_version": VERSION,
        "classification": "SOURCE_DATA_PASS" if passed else "SOURCE_FEASIBILITY_BLOCKED",
        "rest": rest,
        "websocket": ws,
        "rest_gates": rest_gates,
        "websocket_gates": ws_gates,
        "prices_summarized": False,
        "sizes_summarized": False,
        "returns_computed": False,
        "markouts_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "authenticated_endpoint_used": False,
        "orders_sent": False,
        "exchange_mutation": False,
    }


async def amain(args: argparse.Namespace) -> int:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rest_raw = args.out_dir / "SCL_LIQPULL_FWD_002_REST_L2_RAW_V0_1.jsonl"
    ws_raw = args.out_dir / "SCL_LIQPULL_FWD_002_WS_BBO_TRADES_RAW_V0_1.jsonl"
    rest_task = asyncio.create_task(rest_probe(args.duration_seconds, rest_raw))
    ws_task = asyncio.create_task(ws_probe(args.duration_seconds, ws_raw))
    rest, ws = await asyncio.gather(rest_task, ws_task)
    report = adjudicate(rest, ws)
    report["duration_seconds"] = args.duration_seconds
    report["frozen_source_gate_commit"] = args.authority_commit
    out = args.out_dir / "SCL_LIQPULL_TOXICITY_FWD_002_SOURCE_GATE_RESULT_V0_1.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--duration-seconds", type=int, default=DEFAULT_DURATION)
    p.add_argument("--authority-commit", required=True)
    a = p.parse_args()
    if a.duration_seconds != DEFAULT_DURATION:
        raise SystemExit("Fail closed: canonical source probe duration is exactly 120 seconds")
    if len(a.authority_commit) < 7:
        raise SystemExit("Fail closed: authority commit required")
    return asyncio.run(amain(a))


if __name__ == "__main__":
    raise SystemExit(main())
