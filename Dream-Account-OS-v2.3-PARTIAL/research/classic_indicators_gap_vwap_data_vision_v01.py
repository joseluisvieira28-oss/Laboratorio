#!/usr/bin/env python3
"""CIGL-VWAP-01 official Binance Data Vision acquisition + frozen evaluation.

Research only. Discovery (2022-2023) is always evaluated first. Calendar year
2024 is not requested unless the frozen Discovery gate passes. 2025+ is never
requested by this program. Raw monthly ZIPs are checksum-verified against the
official Binance .CHECKSUM sidecars and discarded after parsing.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from classic_indicators_gap_v01 import (
    BASE_COST_BPS,
    STRESS_COST_BPS,
    HOLD_BARS,
    SYMBOLS,
    DISCOVERY_MONTHS,
    VALIDATION_MONTHS,
    FORBIDDEN_START,
    minute_vwap_and_hourly,
    summarize,
    discovery_gate,
    validation_gate,
)

BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
DISCOVERY_EXPECTED_ROWS = {
    "BTCUSDT": 1_051_200,
    "ETHUSDT": 1_051_200,
    "BNBUSDT": 1_051_200,
    "DOGEUSDT": 1_051_200,
    "SOLUSDT": 1_044_000,
    "XRPUSDT": 1_044_000,
}
COLS = ["open_time", "open", "high", "low", "close", "volume"]


def fetch_bytes(url: str, retries: int = 4) -> bytes:
    if any(f"/{year}-" in url for year in range(2025, 2031)):
        raise RuntimeError(f"Protected-period URL blocked: {url}")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CIGL-VWAP-01/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last}")


def parse_month(symbol: str, ym: str, provenance: list[dict]) -> pd.DataFrame:
    fname = f"{symbol}-1m-{ym}.zip"
    url = f"{BASE}/{symbol}/1m/{fname}"
    checksum_url = url + ".CHECKSUM"
    checksum_text = fetch_bytes(checksum_url).decode("utf-8", errors="strict").strip()
    expected_sha = checksum_text.split()[0].lower()
    if len(expected_sha) != 64:
        raise RuntimeError(f"Malformed official checksum for {fname}: {checksum_text!r}")
    payload = fetch_bytes(url)
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != expected_sha:
        raise RuntimeError(f"Checksum mismatch for {fname}: {actual_sha} != {expected_sha}")

    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        members = [n for n in z.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"{fname}: expected exactly one member, got {members}")
        raw = z.read(members[0])
    table = pd.read_csv(io.BytesIO(raw), header=None, dtype=str)
    if table.shape[1] < 6:
        raise RuntimeError(f"{fname}: fewer than 6 columns")
    table = table.iloc[:, :6].copy()
    table.columns = COLS
    first_numeric = pd.to_numeric(table["open_time"], errors="coerce")
    if pd.isna(first_numeric.iloc[0]):
        table = table.iloc[1:].copy()
    for c in COLS:
        table[c] = pd.to_numeric(table[c], errors="coerce")
    if table[COLS].isna().any(axis=None):
        bad = int(table[COLS].isna().any(axis=1).sum())
        raise RuntimeError(f"{fname}: {bad} invalid numeric rows; no repair authorized")
    table["open_time"] = table["open_time"].astype("int64")
    table["ts"] = pd.to_datetime(table["open_time"], unit="ms", utc=True)
    if table["ts"].duplicated().any():
        raise RuntimeError(f"{fname}: duplicate timestamps")
    if (table["ts"] >= FORBIDDEN_START).any():
        raise RuntimeError(f"{fname}: protected-period row encountered")
    table.sort_values("ts", inplace=True)

    provenance.append({
        "symbol": symbol,
        "month": ym,
        "url": url,
        "checksum_url": checksum_url,
        "official_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "bytes": len(payload),
        "rows": int(len(table)),
        "first_ts": str(table["ts"].iloc[0]),
        "last_ts": str(table["ts"].iloc[-1]),
    })
    return table[["ts", "open", "high", "low", "close", "volume"]]


def load_symbol_phase(symbol: str, months: list[str], phase: str, provenance: list[dict]) -> pd.DataFrame:
    frames = []
    for ym in months:
        print(f"[{phase}] {symbol} {ym}", flush=True)
        frames.append(parse_month(symbol, ym, provenance))
    d = pd.concat(frames, ignore_index=True).sort_values("ts")
    if d["ts"].duplicated().any():
        raise RuntimeError(f"{phase}/{symbol}: duplicate timestamp across monthly boundaries")
    if phase == "DISCOVERY":
        expected = DISCOVERY_EXPECTED_ROWS[symbol]
        if len(d) != expected:
            raise RuntimeError(f"{symbol}: Discovery row count {len(d)} != frozen H180 authority {expected}")
    return d


def make_trades_strict(hourly: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Frozen VWAP signal with complete four-bar holding path required."""
    h = hourly.copy()
    prev_ok = h["hour_ok"].shift(1).eq(True)
    cur_ok = h["hour_ok"].fillna(False).astype(bool)
    long_sig = prev_ok & cur_ok & (h["close"].shift(1) <= h["vwap"].shift(1)) & (h["close"] > h["vwap"])
    short_sig = prev_ok & cur_ok & (h["close"].shift(1) >= h["vwap"].shift(1)) & (h["close"] < h["vwap"])
    direction = pd.Series(0, index=h.index, dtype="int8")
    direction[long_sig] = 1
    direction[short_sig] = -1
    rows = []
    next_free_entry_pos = -1
    idx = h.index
    for signal_pos, sig in enumerate(direction.to_numpy()):
        if sig == 0:
            continue
        entry_pos = signal_pos + 1
        exit_pos = entry_pos + HOLD_BARS
        if entry_pos <= next_free_entry_pos or exit_pos >= len(h):
            continue
        if not bool(h["hour_ok"].iloc[entry_pos:exit_pos].fillna(False).all()):
            continue
        entry_t, exit_t = idx[entry_pos], idx[exit_pos]
        if exit_t >= FORBIDDEN_START:
            continue
        entry_px, exit_px = float(h["open"].iloc[entry_pos]), float(h["open"].iloc[exit_pos])
        if not (math.isfinite(entry_px) and math.isfinite(exit_px) and entry_px > 0 and exit_px > 0):
            continue
        gross = float(sig * math.log(exit_px / entry_px) * 10000.0)
        rows.append({
            "symbol": symbol,
            "signal_time": idx[signal_pos],
            "entry_time": entry_t,
            "exit_time": exit_t,
            "direction": int(sig),
            "entry_price": entry_px,
            "exit_price": exit_px,
            "signal_close": float(h["close"].iloc[signal_pos]),
            "signal_vwap": float(h["vwap"].iloc[signal_pos]),
            "gross_bps": gross,
            "net10_bps": gross - BASE_COST_BPS,
            "net14_bps": gross - STRESS_COST_BPS,
        })
        next_free_entry_pos = exit_pos - 1
    return pd.DataFrame(rows)


def evaluate_phase(months: list[str], phase: str, provenance: list[dict]) -> pd.DataFrame:
    trades = []
    for symbol in SYMBOLS:
        minute = load_symbol_phase(symbol, months, phase, provenance)
        hourly = minute_vwap_and_hourly(minute)
        t = make_trades_strict(hourly, symbol)
        print(f"[{phase}] {symbol}: rows={len(minute)} valid_hours={int(hourly['hour_ok'].sum())} trades={len(t)}", flush=True)
        if len(t):
            trades.append(t)
    if not trades:
        return pd.DataFrame()
    out = pd.concat(trades, ignore_index=True)
    for c in ["signal_time", "entry_time", "exit_time"]:
        out[c] = pd.to_datetime(out[c], utc=True)
    return out.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def json_safe(x):
    if isinstance(x, dict):
        return {k: json_safe(v) for k, v in x.items()}
    if isinstance(x, list):
        return [json_safe(v) for v in x]
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    return x


def write_summary(path: Path, closeout: dict) -> None:
    d = closeout["discovery_summary"]
    lines = [
        "# CIGL-VWAP-01 — CLOSEOUT", "",
        f"Status: **{closeout['status']}**", "",
        "## Discovery 2022–2023",
        f"- Trades: {d.get('n')}",
        f"- Gross mean: {d.get('gross_mean_bps')} bps",
        f"- NET10 mean: {d.get('net10_mean_bps')} bps",
        f"- NET14 mean: {d.get('net14_mean_bps')} bps",
        f"- PF NET10: {d.get('pf_net10')}",
        f"- Gate pass: {closeout['discovery_gate']['pass']}", "",
        f"2024 opened: **{closeout['opened_2024']}**",
        "2025 accessed: **False**",
        "2026 accessed: **False**",
    ]
    if closeout.get("validation_summary"):
        v = closeout["validation_summary"]
        lines += [
            "", "## 2024 Internal OOS",
            f"- Trades: {v.get('n')}",
            f"- NET10 mean: {v.get('net10_mean_bps')} bps",
            f"- NET14 mean: {v.get('net14_mean_bps')} bps",
            f"- PF NET10: {v.get('pf_net10')}",
            f"- Gate pass: {closeout['validation_gate']['pass']}",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def assert_protocol(protocol: dict) -> None:
    if protocol.get("lab") != "CLASSIC_INDICATORS_GAP_LAB_V0.1":
        raise RuntimeError("Protocol lab identity mismatch")
    if protocol.get("status") != "PRE_DISCOVERY_FROZEN":
        raise RuntimeError("Protocol is not PRE_DISCOVERY_FROZEN")
    if "CIGL-VWAP-01" not in protocol.get("families", []):
        raise RuntimeError("VWAP family missing from frozen protocol")
    if protocol.get("splits", {}).get("discovery") != "2022-01-01T00:00:00Z/2023-12-31T23:59:59Z":
        raise RuntimeError("Protocol Discovery window mismatch")
    common = protocol.get("common_execution", {})
    if common.get("primary_timeframe") != "1H" or common.get("holding_bars") != 4:
        raise RuntimeError("Frozen execution semantics mismatch")
    if common.get("base_roundtrip_cost_bps") != 10 or common.get("stress_roundtrip_cost_bps") != 14:
        raise RuntimeError("Frozen cost model mismatch")
    gate = protocol.get("phase_gates", {}).get("discovery", {})
    if gate.get("min_trades") != 300 or gate.get("net10_mean_bps_gt") != 0 or gate.get("profit_factor_gt") != 1.0:
        raise RuntimeError("Frozen Discovery gate mismatch")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    assert_protocol(protocol)

    provenance: list[dict] = []
    discovery_trades = evaluate_phase(DISCOVERY_MONTHS, "DISCOVERY", provenance)
    discovery_trades.to_csv(args.out / "CIGL_VWAP_01_DISCOVERY_TRADES.csv", index=False)
    dsum = summarize(discovery_trades)
    dgate = discovery_gate(dsum)
    opened_2024 = bool(dgate["pass"])
    vsum = None
    vgate = None

    if opened_2024:
        print("DISCOVERY GATE PASS — opening frozen 2024 internal OOS once", flush=True)
        validation_trades = evaluate_phase(VALIDATION_MONTHS, "VALIDATION_2024", provenance)
        validation_trades.to_csv(args.out / "CIGL_VWAP_01_VALIDATION_2024_TRADES.csv", index=False)
        vsum = summarize(validation_trades)
        vgate = validation_gate(vsum)
        status = "MVE_1_REPLICATION_READY" if vgate["pass"] else "OOS_FAIL_VWAP_CLOSED"
    else:
        print("DISCOVERY GATE FAIL — 2024 remains unopened", flush=True)
        status = "DISCOVERY_FAIL_VWAP_CLOSED"

    closeout = json_safe({
        "lab": "CLASSIC_INDICATORS_GAP_LAB_V0.1",
        "experiment_id": "CIGL-VWAP-01",
        "status": status,
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "data_source": "Binance Data Vision USD-M Futures monthly 1m klines",
        "discovery_summary": dsum,
        "discovery_gate": dgate,
        "opened_2024": opened_2024,
        "validation_summary": vsum,
        "validation_gate": vgate,
        "accessed_2025": False,
        "accessed_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
        "post_result_parameter_change": False,
    })
    (args.out / "CIGL_VWAP_01_CLOSEOUT.json").write_text(json.dumps(closeout, indent=2, sort_keys=True), encoding="utf-8")
    (args.out / "CIGL_VWAP_01_DATA_PROVENANCE.json").write_text(json.dumps(json_safe(provenance), indent=2, sort_keys=True), encoding="utf-8")
    write_summary(args.out / "CIGL_VWAP_01_SUMMARY.md", closeout)
    print(json.dumps(closeout, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
