#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_RULE_V1.0.json").read_text())
B = json.loads((HERE / "MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SOURCE_BINDING_V1.0.json").read_text())

UA = "CryptoLab-Overshoot-Shadow/0.2.1"
MEXC = "https://api.mexc.com/api/v1/contract"
BINANCE = "https://fapi.binance.com/fapi/v1/klines"
BITGET = "https://api.bitget.com/api/v2/mix/market/history-candles"

NOTIONALS = [10.0, 25.0, 50.0, 100.0]
FEES = [12.0, 14.0, 16.0, 20.0]
SESSION_START = "13:35"
SESSION_END = "19:55"
ENTRY_MAX_DELAY_SEC = 30.0
EXIT_MAX_DELAY_SEC = 30.0
MAX_WORKERS = 18
FREEZE_TS = datetime.fromisoformat("2026-10-05T08:28:00+00:00").timestamp()


def atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def req(url, params=None, timeout=12, retries=3):
    last = None
    for i in range(retries):
        started = datetime.now(timezone.utc)
        t0 = time.perf_counter()
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=timeout)
            latency_ms = (time.perf_counter() - t0) * 1000
            completed = datetime.now(timezone.utc)
            body = r.content
            evidence = {
                "request_started_utc": started.isoformat(),
                "request_completed_utc": completed.isoformat(),
                "latency_ms": latency_ms,
                "status_code": r.status_code,
                "url": r.url,
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "body_bytes": len(body),
            }
            if r.status_code == 200:
                return r, evidence
            last = RuntimeError(f"HTTP_{r.status_code}:{r.url}")
        except Exception as exc:
            last = exc
        time.sleep(0.2 * (i + 1))
    raise last


def sgn(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def parse_hm(day, hm):
    h, m = map(int, hm.split(":"))
    d = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return d.replace(hour=h, minute=m, second=0, microsecond=0)


def minute_in_session(dt: datetime) -> bool:
    hm = dt.strftime("%H:%M")
    return SESSION_START <= hm <= SESSION_END


def parse_mexc_closes(symbol, decision_dt):
    start = int((decision_dt - timedelta(minutes=8)).timestamp())
    end = int((decision_dt + timedelta(minutes=1)).timestamp())
    r, ev = req(f"{MEXC}/kline/{symbol}", {"interval": "Min1", "start": str(start), "end": str(end)})
    raw_text = r.text
    j = r.json()
    z = j.get("data") or {}
    if j.get("success") is not True:
        raise RuntimeError("MEXC_SUCCESS_FALSE")
    out = {}
    for t, p in zip(z.get("time") or [], z.get("close") or []):
        out[int(t) + 60] = float(p)
    ev["raw_body"] = raw_text
    return out, ev


def parse_binance_closes(symbol, decision_dt):
    st = int((decision_dt - timedelta(minutes=8)).timestamp() * 1000)
    r, ev = req(BINANCE, {"symbol": symbol, "interval": "1m", "startTime": st, "limit": "12"})
    raw_text = r.text
    out = {}
    for row in r.json() or []:
        out[int(row[0]) // 1000 + 60] = float(row[4])
    ev["raw_body"] = raw_text
    return out, ev


def parse_bitget_closes(symbol, decision_dt):
    st = int((decision_dt - timedelta(minutes=8)).timestamp() * 1000)
    en = int((decision_dt + timedelta(minutes=1)).timestamp() * 1000)
    r, ev = req(
        BITGET,
        {
            "symbol": symbol,
            "productType": "USDT-FUTURES",
            "granularity": "1m",
            "startTime": str(st),
            "endTime": str(en),
            "limit": "12",
        },
    )
    raw_text = r.text
    j = r.json()
    if j.get("code") != "00000":
        raise RuntimeError("BITGET_" + str(j.get("code")))
    out = {}
    for row in j.get("data") or []:
        out[int(row[0]) // 1000 + 60] = float(row[4])
    ev["raw_body"] = raw_text
    return out, ev


def level(x):
    if isinstance(x, (list, tuple)) and len(x) >= 2:
        return float(x[0]), float(x[1])
    if isinstance(x, dict):
        p = x.get("price", x.get("p"))
        v = x.get("vol", x.get("v", x.get("quantity", x.get("q"))))
        return float(p), float(v)
    raise ValueError("BAD_LEVEL")


def depth(symbol):
    r, ev = req(f"{MEXC}/depth/{symbol}")
    j = r.json()
    d = j.get("data") or {}
    if j.get("success") is not True:
        raise RuntimeError("DEPTH_SUCCESS_FALSE")
    bids = sorted([level(x) for x in (d.get("bids") or [])], key=lambda x: x[0], reverse=True)
    asks = sorted([level(x) for x in (d.get("asks") or [])], key=lambda x: x[0])
    if not bids or not asks:
        raise RuntimeError("EMPTY_BOOK")
    captured = datetime.now(timezone.utc)
    ev["raw_body"] = r.text
    return {
        "captured_at_utc": captured.isoformat(),
        "captured_at_epoch": captured.timestamp(),
        "source_evidence": ev,
        "bids": bids,
        "asks": asks,
    }


def contract_meta():
    r, ev = req(f"{MEXC}/detail")
    j = r.json()
    if j.get("success") is not True:
        raise RuntimeError("DETAIL_SUCCESS_FALSE")
    out = {}
    for x in j.get("data") or []:
        if not isinstance(x, dict) or not x.get("symbol"):
            continue
        try:
            cs = float(x["contractSize"])
            vu = float(x["volUnit"])
            mv = float(x["minVol"])
            maxv = float(x.get("maxVol") or float("inf"))
            if not (cs > 0 and vu > 0 and mv > 0 and maxv > 0):
                raise ValueError
            out[x["symbol"]] = {
                "contract_size": cs,
                "vol_unit": vu,
                "min_vol": mv,
                "max_vol": maxv,
            }
        except Exception:
            continue
    return out, ev


def quantized_contracts(target_notional, top_price, meta):
    raw = target_notional / (top_price * meta["contract_size"])
    units = math.ceil(raw / meta["vol_unit"] - 1e-12)
    qty = max(meta["min_vol"], units * meta["vol_unit"])
    if qty > meta["max_vol"]:
        raise ValueError("QTY_EXCEEDS_MAX_VOL")
    return qty


def fill_contracts(book, action, contracts, contract_size):
    levels = book["asks"] if action == "BUY" else book["bids"]
    remain = contracts
    quote = 0.0
    used = 0
    for price, avail_contracts in levels:
        take = min(remain, max(0.0, avail_contracts))
        if take <= 0:
            continue
        quote += price * take * contract_size
        remain -= take
        used += 1
        if remain <= 1e-12:
            break
    if remain > 1e-9:
        return {
            "fillable": False,
            "requested_contracts": contracts,
            "unfilled_contracts": remain,
            "levels_used": used,
        }
    base_qty = contracts * contract_size
    avg = quote / base_qty if base_qty > 0 else None
    top = levels[0][0]
    slip = (avg / top - 1) * 10000 if action == "BUY" else (top / avg - 1) * 10000
    return {
        "fillable": True,
        "contracts": contracts,
        "base_qty": base_qty,
        "quote_notional": quote,
        "avg_price": avg,
        "top_price": top,
        "book_slippage_bps": slip,
        "levels_used": used,
    }


def entry_fill(book, action, target_notional, meta):
    top = (book["asks"] if action == "BUY" else book["bids"])[0][0]
    contracts = quantized_contracts(target_notional, top, meta)
    result = fill_contracts(book, action, contracts, meta["contract_size"])
    result["target_notional_usdt"] = target_notional
    result["contract_meta"] = meta
    return result


def signal_for(candidate, t):
    dt = datetime.fromtimestamp(t, timezone.utc)
    m, mev = parse_mexc_closes(candidate["target"], dt)
    b, bev = parse_binance_closes(candidate["external_binance"], dt)
    g, gev = parse_bitget_closes(candidate["external_bitget"], dt)
    t0 = t - 5 * 60
    exact = all(x in m for x in (t0, t)) and all(x in b for x in (t0, t)) and all(x in g for x in (t0, t))
    meta = {"exact_points": exact}
    if not exact:
        return None, meta
    rb = 10000 * (b[t] / b[t0] - 1)
    rg = 10000 * (g[t] / g[t0] - 1)
    ext = (rb + rg) / 2
    rm = 10000 * (m[t] / m[t0] - 1)
    exc = rm - ext
    trig = (
        abs(rb - rg) <= R["trigger"]["max_external_leader_dispersion_bps"]
        and abs(rm) >= R["trigger"]["abs_mexc_5m_return_gte_bps"]
        and abs(exc) >= R["trigger"]["abs_mexc_excess_gte_bps"]
        and sgn(exc) == sgn(rm)
    )
    if not trig:
        return None, meta
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
        "side": -sgn(exc),
        "source_evidence": {"mexc": mev, "binance": bev, "bitget": gev},
    }, meta


def wait_until(dt):
    while True:
        seconds = (dt - datetime.now(timezone.utc)).total_seconds()
        if seconds <= 0:
            return
        time.sleep(min(seconds, 5))


def scan_signals(t):
    triggers = []
    errors = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(signal_for, c, t): c for c in B["candidates"]}
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


def capture_entries(triggers, signal_ts, meta):
    assets = []
    def one(sig):
        target = sig["target"]
        cm = meta.get(target)
        if cm is None:
            return {**sig, "entry_error": "INVALID_OR_MISSING_CONTRACT_METADATA"}
        try:
            book = depth(target)
            lag = book["captured_at_epoch"] - signal_ts
            action = "BUY" if sig["side"] > 0 else "SELL"
            fills = {}
            for n in NOTIONALS:
                fills[str(int(n))] = entry_fill(book, action, n, cm)
            return {
                **sig,
                "entry_book": book,
                "entry_action": action,
                "entry_capture_delay_sec": lag,
                "entry_timing_valid": 0 <= lag <= ENTRY_MAX_DELAY_SEC,
                "entry_fills": fills,
            }
        except Exception as exc:
            return {**sig, "entry_error": str(exc)}
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(triggers)))) as pool:
        futs = [pool.submit(one, s) for s in triggers]
        for fut in as_completed(futs):
            assets.append(fut.result())
    return sorted(assets, key=lambda x: x["target"])


def capture_exit(asset, due_ts):
    if "entry_book" not in asset:
        return
    try:
        book = depth(asset["target"])
        lag = book["captured_at_epoch"] - due_ts
        action = "SELL" if asset["side"] > 0 else "BUY"
        fills = {}
        for n in NOTIONALS:
            key = str(int(n))
            ef = asset["entry_fills"].get(key) or {}
            if not ef.get("fillable"):
                fills[key] = {"fillable": False, "reason": "ENTRY_UNFILLABLE"}
                continue
            fills[key] = fill_contracts(
                book,
                action,
                float(ef["contracts"]),
                float(ef["contract_meta"]["contract_size"]),
            )
        asset["exit_book"] = book
        asset["exit_action"] = action
        asset["exit_capture_delay_sec"] = lag
        asset["exit_timing_valid"] = 0 <= lag <= EXIT_MAX_DELAY_SEC
        asset["exit_fills"] = fills
    except Exception as exc:
        asset["exit_error"] = str(exc)


def receipt_obj(a, events, pending, errors, detail_evidence, started_utc):
    return {
        "family_id": R["family_id"],
        "shadow_version": "0.2.1",
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


def validate_args(a):
    start = parse_hm(a.date, a.start)
    end = parse_hm(a.date, a.end)
    if start.date().weekday() >= 5:
        raise SystemExit("FAIL_CLOSED_WEEKEND")
    if not minute_in_session(start) or not minute_in_session(end) or start > end:
        raise SystemExit("FAIL_CLOSED_SESSION_BOUNDARY")
    if start.timestamp() <= FREEZE_TS:
        raise SystemExit("FAIL_CLOSED_PRE_FREEZE_TIMESTAMP")
    return start, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--segment", required=True)
    a = ap.parse_args()
    start, end = validate_args(a)

    outdir = Path("artifacts/mexc_global_assets/intraday_overshoot_shadow_v021") / a.date / a.segment
    outdir.mkdir(parents=True, exist_ok=True)
    receipt_path = outdir / f"shadow_{a.date}_{a.segment}.json"

    meta, detail_evidence = contract_meta()
    missing = sorted(c["target"] for c in B["candidates"] if c["target"] not in meta)
    if missing:
        raise SystemExit("FAIL_CLOSED_CONTRACT_METADATA:" + ",".join(missing))

    events = []
    pending = []
    errors = []
    started_utc = datetime.now(timezone.utc).isoformat()

    wait_until(start + timedelta(seconds=2))
    minute = start
    while minute <= end:
        wait_until(minute + timedelta(seconds=2))

        # Complete due exits before starting the new minute scan.
        due_now = [x for x in pending if x["due"] <= datetime.now(timezone.utc)]
        pending = [x for x in pending if x not in due_now]
        for p in due_now:
            due_ts = p["due"].timestamp()
            with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(p["event"]["assets"])))) as pool:
                futs = [pool.submit(capture_exit, x, due_ts) for x in p["event"]["assets"]]
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
            atomic_json(receipt_path, receipt_obj(a, events, pending, errors, detail_evidence, started_utc))
            minute += timedelta(minutes=1)
            continue

        t = int(minute.timestamp())
        triggers, scan_errors = scan_signals(t)
        for e in scan_errors:
            errors.append({"minute": minute.isoformat(), **e})

        if triggers:
            event = {
                "timestamp": t,
                "signal_utc": minute.isoformat(),
                "triggered_assets": len(triggers),
                "assets": capture_entries(triggers, t, meta),
            }
            pending.append({"due": minute + timedelta(minutes=5), "event": event})

        atomic_json(receipt_path, receipt_obj(a, events, pending, errors, detail_evidence, started_utc))
        minute += timedelta(minutes=1)

    for p in sorted(pending, key=lambda z: z["due"]):
        wait_until(p["due"] + timedelta(seconds=2))
        due_ts = p["due"].timestamp()
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(p["event"]["assets"])))) as pool:
            futs = [pool.submit(capture_exit, x, due_ts) for x in p["event"]["assets"]]
            for fut in as_completed(futs):
                fut.result()
        events.append(p["event"])
        atomic_json(receipt_path, receipt_obj(a, events, [], errors, detail_evidence, started_utc))

    final = receipt_obj(a, events, [], errors, detail_evidence, started_utc)
    atomic_json(receipt_path, final)
    print(json.dumps({
        "date": a.date,
        "segment": a.segment,
        "events": len(events),
        "errors": len(errors),
        "path": str(receipt_path),
        "orders": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
