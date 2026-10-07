#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

from websockets.sync.client import connect as ws_connect

import mexc_globalasset_intraday_overshoot_shadow_v022 as base

R = base.R
B = base.B
NOTIONALS = base.NOTIONALS
FEES = base.FEES
SESSION_START = base.SESSION_START
SESSION_END = base.SESSION_END
ENTRY_MAX_DELAY_SEC = base.ENTRY_MAX_DELAY_SEC
EXIT_MAX_DELAY_SEC = base.EXIT_MAX_DELAY_SEC
MAX_WORKERS = base.MAX_WORKERS

MEXC_WS = "wss://contract.mexc.com/edge"
BITGET_WS = "wss://ws.bitget.com/v3/ws/public"
V024_FREEZE_TS = datetime.fromisoformat("2026-10-07T14:16:49+00:00").timestamp()


class ClosedKlineCache:
    def __init__(self, symbols):
        self.symbols = sorted(set(symbols))
        self.data = {s.upper(): {} for s in self.symbols}
        self.pending = {s.upper(): {} for s in self.symbols}
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.connection_errors = []
        self.connected = False

    def start(self):
        if self.thread is not None:
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=4)

    def _store_update(self, symbol, start_sec, close, evidence, received_epoch):
        symbol = symbol.upper()
        if symbol not in self.data:
            return
        obs = int(start_sec) + 60
        row = {"close": float(close), "evidence": evidence}
        with self.lock:
            p = self.pending[symbol]
            # A later candle proves every earlier minute is closed.
            for old_start in [x for x in p if x < int(start_sec)]:
                old = p.pop(old_start)
                self.data[symbol][old_start + 60] = old
            if received_epoch >= obs:
                self.data[symbol][obs] = row
                p.pop(int(start_sec), None)
            else:
                p[int(start_sec)] = row
            cutoff = int(start_sec) - 7200
            self.data[symbol] = {t: v for t, v in self.data[symbol].items() if t >= cutoff}
            self.pending[symbol] = {t: v for t, v in p.items() if t >= cutoff}

    def pair(self, symbol, t0, t, wait_sec=8):
        symbol = symbol.upper()
        deadline = time.time() + wait_sec
        while time.time() <= deadline:
            with self.lock:
                d = self.data.get(symbol, {})
                a = d.get(t0)
                b = d.get(t)
            if a is not None and b is not None:
                return {
                    t0: a["close"],
                    t: b["close"],
                }, {
                    "transport": self.transport_name,
                    "t0": a["evidence"],
                    "t": b["evidence"],
                }
            time.sleep(0.1)
        raise RuntimeError(f"{self.transport_name}_EXACT_POINTS_MISSING:{symbol}:{t0}:{t}")


class MexcKlineCache(ClosedKlineCache):
    transport_name = "MEXC_PUBLIC_CONTRACT_WEBSOCKET_KLINE"

    def __init__(self, candidates):
        super().__init__([x["target"] for x in candidates])
        self.thread = None
        self.pongs = 0
        self.subscriptions_sent = 0

    def _run(self):
        while not self.stop_event.is_set():
            try:
                with ws_connect(MEXC_WS, open_timeout=10, close_timeout=3, max_size=2**22) as ws:
                    for i, symbol in enumerate(self.symbols):
                        ws.send(json.dumps({
                            "method": "sub.kline",
                            "param": {"symbol": symbol, "interval": "Min1"},
                        }))
                        self.subscriptions_sent += 1
                        if i and i % 8 == 0:
                            ws.send(json.dumps({"method": "ping"}))
                        time.sleep(0.05)
                    self.connected = True
                    next_ping = time.time() + 15
                    while not self.stop_event.is_set():
                        if time.time() >= next_ping:
                            ws.send(json.dumps({"method": "ping"}))
                            next_ping = time.time() + 15
                        try:
                            raw = ws.recv(timeout=3)
                        except TimeoutError:
                            continue
                        received = datetime.now(timezone.utc)
                        j = json.loads(raw)
                        if j.get("channel") == "pong":
                            self.pongs += 1
                            continue
                        if j.get("channel") != "push.kline":
                            continue
                        d = j.get("data") or {}
                        symbol = str(j.get("symbol") or d.get("symbol") or "").upper()
                        if symbol not in self.data:
                            continue
                        if d.get("interval") != "Min1":
                            continue
                        start_sec = int(d["t"])
                        ev = {
                            "received_at_utc": received.isoformat(),
                            "exchange_ts_ms": j.get("ts"),
                            "raw_body": raw,
                            "body_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                            "body_bytes": len(raw.encode("utf-8")),
                            "channel": "push.kline",
                        }
                        self._store_update(symbol, start_sec, float(d["c"]), ev, received.timestamp())
            except Exception as exc:
                self.connected = False
                self.connection_errors.append({
                    "at_utc": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                })
                time.sleep(1)


class BitgetKlineCache(ClosedKlineCache):
    transport_name = "BITGET_PUBLIC_V3_WEBSOCKET_KLINE"

    def __init__(self, candidates):
        super().__init__([x["external_bitget"] for x in candidates])
        self.subscription_events = []
        self.subscriptions_sent = 0

    @staticmethod
    def _start_seconds(value):
        x = int(value)
        return x // 1000 if x > 10_000_000_000 else x

    def _run(self):
        while not self.stop_event.is_set():
            try:
                with ws_connect(BITGET_WS, open_timeout=10, close_timeout=3, max_size=2**22) as ws:
                    args = [
                        {
                            "instType": "usdt-futures",
                            "topic": "kline",
                            "symbol": symbol,
                            "interval": "1m",
                        }
                        for symbol in self.symbols
                    ]
                    ws.send(json.dumps({"op": "subscribe", "args": args}))
                    self.subscriptions_sent += len(args)
                    self.connected = True
                    next_ping = time.time() + 20
                    while not self.stop_event.is_set():
                        if time.time() >= next_ping:
                            ws.send("ping")
                            next_ping = time.time() + 20
                        try:
                            raw = ws.recv(timeout=3)
                        except TimeoutError:
                            continue
                        received = datetime.now(timezone.utc)
                        if raw == "pong":
                            continue
                        j = json.loads(raw)
                        if j.get("event"):
                            self.subscription_events.append({
                                "at_utc": received.isoformat(),
                                "event": j.get("event"),
                                "code": j.get("code"),
                                "msg": j.get("msg"),
                                "arg": j.get("arg"),
                            })
                            if j.get("event") == "error" or (
                                j.get("code") not in (None, "", "0", "00000")
                            ):
                                raise RuntimeError("BITGET_SUBSCRIBE_ERROR:" + json.dumps(j, sort_keys=True))
                            continue
                        arg = j.get("arg") or {}
                        if arg.get("topic") != "kline" or arg.get("interval") != "1m":
                            continue
                        symbol = str(arg.get("symbol") or "").upper()
                        if symbol not in self.data:
                            continue
                        rows = j.get("data") or []
                        for row in rows:
                            if not isinstance(row, dict) or "start" not in row or "close" not in row:
                                continue
                            start_sec = self._start_seconds(row["start"])
                            ev = {
                                "received_at_utc": received.isoformat(),
                                "exchange_ts_ms": j.get("ts"),
                                "raw_body": raw,
                                "body_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                                "body_bytes": len(raw.encode("utf-8")),
                                "topic": "kline",
                            }
                            self._store_update(symbol, start_sec, float(row["close"]), ev, received.timestamp())
            except Exception as exc:
                self.connected = False
                self.connection_errors.append({
                    "at_utc": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                })
                time.sleep(1)


def validate_args(a):
    start = base.parse_hm(a.date, a.start)
    end = base.parse_hm(a.date, a.end)
    if start.date().weekday() >= 5:
        raise SystemExit("FAIL_CLOSED_WEEKEND")
    if not base.minute_in_session(start) or not base.minute_in_session(end) or start > end:
        raise SystemExit("FAIL_CLOSED_SESSION_BOUNDARY")
    if start.timestamp() <= V024_FREEZE_TS:
        raise SystemExit("FAIL_CLOSED_PRE_V024_FREEZE_TIMESTAMP")
    return start, end


def signal_for(candidate, t, binance_cache, mexc_cache, bitget_cache):
    t0 = t - 5 * 60
    m, mev = mexc_cache.pair(candidate["target"], t0, t)
    b, bev = binance_cache.pair(candidate["external_binance"], t0, t)
    g, gev = bitget_cache.pair(candidate["external_bitget"], t0, t)
    rb = 10000 * (b[t] / b[t0] - 1)
    rg = 10000 * (g[t] / g[t0] - 1)
    ext = (rb + rg) / 2
    rm = 10000 * (m[t] / m[t0] - 1)
    exc = rm - ext
    trig = (
        abs(rb - rg) <= R["trigger"]["max_external_leader_dispersion_bps"]
        and abs(rm) >= R["trigger"]["abs_mexc_5m_return_gte_bps"]
        and abs(exc) >= R["trigger"]["abs_mexc_excess_gte_bps"]
        and base.sgn(exc) == base.sgn(rm)
    )
    if not trig:
        return None, {"exact_points": True}
    dt = datetime.fromtimestamp(t, timezone.utc)
    return {
        "target": candidate["target"],
        "external_binance": candidate["external_binance"],
        "external_bitget": candidate["external_bitget"],
        "timestamp": t,
        "signal_utc": dt.isoformat(),
        "binance_5m_bps": rb,
        "bitget_5m_bps": rg,
        "external_5m_bps": ext,
        "mexc_5m_bps": rm,
        "mexc_excess_bps": exc,
        "side": -base.sgn(exc),
        "source_evidence": {"mexc": mev, "binance": bev, "bitget": gev},
    }, {"exact_points": True}


def scan_signals(t, binance_cache, mexc_cache, bitget_cache):
    triggers = []
    errors = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {
            pool.submit(signal_for, c, t, binance_cache, mexc_cache, bitget_cache): c
            for c in B["candidates"]
        }
        for fut in as_completed(futs):
            c = futs[fut]
            try:
                sig, meta = fut.result()
                if not meta.get("exact_points"):
                    errors.append({"target": c["target"], "error": "SOURCE_EXACT_POINTS_MISSING"})
                if sig:
                    triggers.append(sig)
            except Exception as exc:
                errors.append({"target": c["target"], "error": str(exc)})
    return sorted(triggers, key=lambda x: x["target"]), errors


def receipt_obj(a, events, pending, errors, detail_evidence, started_utc, caches):
    return {
        "family_id": R["family_id"],
        "shadow_version": "0.2.4",
        "epoch": "V0.2.4_CLEAN_PROSPECTIVE",
        "v024_freeze_commit": "9a28a6f17bc52ada6ce1e7d73e6ef669ac9e1599",
        "v024_freeze_timestamp_utc": "2026-10-07T14:16:49Z",
        "date": a.date,
        "segment": a.segment,
        "start_utc": a.start,
        "end_utc": a.end,
        "started_utc": started_utc,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "events": events,
        "pending_events": [x["event"] for x in pending],
        "errors": errors,
        "contract_detail_source_evidence": detail_evidence,
        "transport": {
            "binance": "BINANCE_OFFICIAL_USDM_MARKET_WEBSOCKET",
            "mexc": "MEXC_PUBLIC_CONTRACT_WEBSOCKET_KLINE",
            "bitget": "BITGET_PUBLIC_V3_WEBSOCKET_KLINE",
            "mexc_connection_errors": caches["mexc"].connection_errors,
            "bitget_connection_errors": caches["bitget"].connection_errors,
            "binance_connection_errors": caches["binance"].connection_errors,
        },
        "notionals_usdt": NOTIONALS,
        "fee_scenarios_rt_bps": FEES,
        "entry_max_delay_sec": ENTRY_MAX_DELAY_SEC,
        "exit_max_delay_sec": EXIT_MAX_DELAY_SEC,
        "cooldown_applied_online": False,
        "cooldown_policy": "apply deterministic frozen 10m global cooldown in final aggregator across all segments",
        "orders": False,
        "account_reads": False,
        "private_endpoints_used": False,
        "exchange_mutation": False,
        "live_trading": False,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--segment", required=True)
    a = ap.parse_args()
    start, end = validate_args(a)

    outdir = Path("artifacts/mexc_global_assets/intraday_overshoot_shadow_v024") / a.date / a.segment
    outdir.mkdir(parents=True, exist_ok=True)
    receipt_path = outdir / f"shadow_{a.date}_{a.segment}.json"

    meta, detail_evidence = base.contract_meta()
    missing = sorted(c["target"] for c in B["candidates"] if c["target"] not in meta)
    if missing:
        raise SystemExit("FAIL_CLOSED_CONTRACT_METADATA:" + ",".join(missing))

    events = []
    pending = []
    errors = []
    started_utc = datetime.now(timezone.utc).isoformat()

    binance_cache = base.BinanceKlineCache(B["candidates"])
    mexc_cache = MexcKlineCache(B["candidates"])
    bitget_cache = BitgetKlineCache(B["candidates"])
    caches = {"binance": binance_cache, "mexc": mexc_cache, "bitget": bitget_cache}
    for cache in caches.values():
        cache.start()

    try:
        # Caches start before the frozen scan start to accumulate the exact 5m lookback.
        base.wait_until(start + timedelta(seconds=2))
        minute = start
        while minute <= end:
            base.wait_until(minute + timedelta(seconds=2))

            due_now = [x for x in pending if x["due"] <= datetime.now(timezone.utc)]
            pending = [x for x in pending if x not in due_now]
            for p in due_now:
                due_ts = p["due"].timestamp()
                with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(p["event"]["assets"])))) as pool:
                    futs = [pool.submit(base.capture_exit, x, due_ts) for x in p["event"]["assets"]]
                    for fut in as_completed(futs):
                        fut.result()
                events.append(p["event"])

            now = datetime.now(timezone.utc)
            lag = (now - minute).total_seconds()
            if lag > ENTRY_MAX_DELAY_SEC:
                errors.append({
                    "minute": minute.isoformat(),
                    "error": "LATE_SCAN_FAIL_CLOSED",
                    "observed_at": now.isoformat(),
                    "delay_sec": lag,
                })
                base.atomic_json(receipt_path, receipt_obj(a, events, pending, errors, detail_evidence, started_utc, caches))
                minute += timedelta(minutes=1)
                continue

            t = int(minute.timestamp())
            triggers, scan_errors = scan_signals(t, binance_cache, mexc_cache, bitget_cache)
            for e in scan_errors:
                errors.append({"minute": minute.isoformat(), **e})

            if triggers:
                event = {
                    "timestamp": t,
                    "signal_utc": minute.isoformat(),
                    "triggered_assets": len(triggers),
                    "assets": base.capture_entries(triggers, t, meta),
                }
                pending.append({"due": minute + timedelta(minutes=5), "event": event})

            base.atomic_json(receipt_path, receipt_obj(a, events, pending, errors, detail_evidence, started_utc, caches))
            minute += timedelta(minutes=1)

        for p in sorted(pending, key=lambda z: z["due"]):
            base.wait_until(p["due"] + timedelta(seconds=2))
            due_ts = p["due"].timestamp()
            with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(p["event"]["assets"])))) as pool:
                futs = [pool.submit(base.capture_exit, x, due_ts) for x in p["event"]["assets"]]
                for fut in as_completed(futs):
                    fut.result()
            events.append(p["event"])
            base.atomic_json(receipt_path, receipt_obj(a, events, [], errors, detail_evidence, started_utc, caches))
    finally:
        for cache in caches.values():
            cache.stop()

    errors.extend({"minute": None, "target": "MEXC_WS", **x} for x in mexc_cache.connection_errors)
    errors.extend({"minute": None, "target": "BITGET_WS", **x} for x in bitget_cache.connection_errors)
    errors.extend({"minute": None, "target": "BINANCE_WS", **x} for x in binance_cache.connection_errors)
    final = receipt_obj(a, events, [], errors, detail_evidence, started_utc, caches)
    base.atomic_json(receipt_path, final)
    print(json.dumps({
        "date": a.date,
        "segment": a.segment,
        "events": len(events),
        "errors": len(errors),
        "path": str(receipt_path),
        "shadow_version": "0.2.4",
        "orders": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
