#!/usr/bin/env python3
"""
CLASSIC INDICATORS GAP LAB V0.1
CIGL-VWAP-01 — Daily UTC VWAP reclaim/loss continuation

Research-only runner. It reads only 2022-01 through 2024-12 members from the
previously verified H180 normalized Binance USD-M 1m packages. It never opens
2025 or 2026 market members. Discovery (2022-2023) is evaluated first; 2024 is
opened only when the frozen Discovery gate passes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

LAB = "CLASSIC_INDICATORS_GAP_LAB_V0.1"
EXPERIMENT = "CIGL-VWAP-01"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
DISCOVERY_START = pd.Timestamp("2022-01-01T00:00:00Z")
DISCOVERY_END = pd.Timestamp("2023-12-31T23:59:59Z")
VALIDATION_START = pd.Timestamp("2024-01-01T00:00:00Z")
VALIDATION_END = pd.Timestamp("2024-12-31T23:59:59Z")
FORBIDDEN_START = pd.Timestamp("2025-01-01T00:00:00Z")
DISCOVERY_MONTHS = [f"{y}-{m:02d}" for y in range(2022, 2024) for m in range(1, 13)]
VALIDATION_MONTHS = [f"2024-{m:02d}" for m in range(1, 13)]
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 14.0
HOLD_BARS = 4
DISCOVERY_MIN_TRADES = 300
VALIDATION_MIN_TRADES = 150
CONCENTRATION_MAX_SHARE = 0.70
BOOT_REPS = 5000
SEED = 20260913
SOURCE_CANONICAL_FP = "51952d966395e34a0390e1da3063b999c4de68d00a3e0e965e27f6ee58ed01f3"
SOURCE_RAW_FP = "e62523e28ab87da27e1aa0f992e94d1b4be461a00ef1d7a1ce807a3740348e8a"
EXPECTED_PACKAGES = {
    "BTCUSDT": "H180-0001_NORMALIZED_BTCUSDT.zip",
    "ETHUSDT": "H180-0001_NORMALIZED_ETHUSDT.zip",
    "SOLUSDT": "H180-0001_NORMALIZED_SOLUSDT.zip",
    "BNBUSDT": "H180-0001_NORMALIZED_BNBUSDT.zip",
    "XRPUSDT": "H180-0001_NORMALIZED_XRPUSDT.zip",
    "DOGEUSDT": "H180-0001_NORMALIZED_DOGEUSDT.zip",
}


@dataclass
class LoadAudit:
    symbol: str
    months_read: int
    rows: int
    first_ts: str | None
    last_ts: str | None
    duplicate_timestamps: int
    invalid_numeric_rows: int
    forbidden_members_opened: int = 0


def expected_member(symbol: str, ym: str) -> str:
    return f"{symbol}/1m/{symbol}-1m-{ym}.normalized.csv.zst"


def _read_member(z: zipfile.ZipFile, member: str) -> pd.DataFrame:
    try:
        import zstandard as zstd
    except ImportError as exc:
        raise RuntimeError(
            "The research runner requires the Python package 'zstandard' to read the verified H180 normalized members. "
            "Install it in the isolated research environment; do not modify production runtime dependencies solely for this lab."
        ) from exc
    usecols = ["open_time", "open", "high", "low", "close", "volume"]
    with z.open(member) as raw, zstd.ZstdDecompressor().stream_reader(raw) as zr:
        df = pd.read_csv(io.TextIOWrapper(zr, encoding="utf-8", newline=""), usecols=usecols)
    return df


def load_symbol(
    normalized_dir: Path,
    symbol: str,
    months: list[str],
    protected_start: pd.Timestamp,
) -> tuple[pd.DataFrame, LoadAudit]:
    path = normalized_dir / EXPECTED_PACKAGES[symbol]
    if not path.exists():
        raise FileNotFoundError(f"Missing normalized package: {path}")

    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if any("2026" in n for n in names):
            raise RuntimeError(f"Forbidden 2026 member present in {path.name}; stop closed")
        for ym in months:
            member = expected_member(symbol, ym)
            if member not in names:
                raise RuntimeError(f"Missing required member {member}")
            frames.append(_read_member(z, member))

    df = pd.concat(frames, ignore_index=True)
    for c in ["open_time", "open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    invalid = int(df[["open_time", "open", "high", "low", "close", "volume"]].isna().any(axis=1).sum())
    if invalid:
        raise RuntimeError(f"{symbol}: {invalid} invalid numeric rows; no repair authorized")

    df["open_time"] = df["open_time"].astype("int64")
    df["ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    if (df["ts"] >= protected_start).any():
        raise RuntimeError(f"{symbol}: protected market row parsed at/after {protected_start}; firewall violation")
    df.sort_values("ts", inplace=True)
    dup = int(df["ts"].duplicated().sum())
    if dup:
        raise RuntimeError(f"{symbol}: {dup} duplicate timestamps; no silent dedupe authorized")

    audit = LoadAudit(
        symbol=symbol,
        months_read=len(months),
        rows=int(len(df)),
        first_ts=str(df["ts"].iloc[0]) if len(df) else None,
        last_ts=str(df["ts"].iloc[-1]) if len(df) else None,
        duplicate_timestamps=dup,
        invalid_numeric_rows=invalid,
    )
    return df[["ts", "open", "high", "low", "close", "volume"]].copy(), audit


def minute_vwap_and_hourly(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy().set_index("ts").sort_index()
    day = d.index.floor("D")
    minute_of_day = d.index.hour * 60 + d.index.minute

    counts = pd.Series(1, index=d.index).groupby(day).cumsum().to_numpy()
    expected = minute_of_day.to_numpy() + 1
    sequential = counts == expected
    vol_ok = np.isfinite(d["volume"].to_numpy()) & (d["volume"].to_numpy() > 0)
    local_ok = sequential & vol_ok
    session_ok = pd.Series(local_ok, index=d.index).groupby(day).cummin().astype(bool)

    tp = (d["high"] + d["low"] + d["close"]) / 3.0
    pv = tp * d["volume"]
    cum_pv = pv.groupby(day).cumsum()
    cum_vol = d["volume"].groupby(day).cumsum()
    d["vwap"] = (cum_pv / cum_vol).where(session_ok)
    d["session_ok"] = session_ok

    h = d.resample("1h", label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        minute_count=("close", "count"),
        vwap=("vwap", "last"),
        session_ok=("session_ok", "last"),
    )
    h["hour_ok"] = (h["minute_count"] == 60) & h["session_ok"].fillna(False) & h[["open", "close", "vwap"]].notna().all(axis=1)
    return h


def make_vwap_trades(hourly: pd.DataFrame, symbol: str) -> pd.DataFrame:
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
        entry_t = idx[entry_pos]
        exit_t = idx[exit_pos]
        if entry_t >= FORBIDDEN_START or exit_t >= FORBIDDEN_START:
            continue
        entry_px = h["open"].iloc[entry_pos]
        exit_px = h["open"].iloc[exit_pos]
        if not (np.isfinite(entry_px) and np.isfinite(exit_px) and entry_px > 0 and exit_px > 0):
            continue
        gross = float(sig * math.log(exit_px / entry_px) * 10000.0)
        rows.append({
            "symbol": symbol,
            "signal_time": idx[signal_pos],
            "entry_time": entry_t,
            "exit_time": exit_t,
            "direction": int(sig),
            "entry_price": float(entry_px),
            "exit_price": float(exit_px),
            "signal_close": float(h["close"].iloc[signal_pos]),
            "signal_vwap": float(h["vwap"].iloc[signal_pos]),
            "gross_bps": gross,
            "net10_bps": gross - BASE_COST_BPS,
            "net14_bps": gross - STRESS_COST_BPS,
        })
        next_free_entry_pos = exit_pos - 1
    return pd.DataFrame(rows)


def profit_factor(x: pd.Series) -> float | None:
    pos = float(x[x > 0].sum())
    neg = float(-x[x < 0].sum())
    if neg == 0:
        return None if pos == 0 else float("inf")
    return pos / neg


def max_cum_drawdown(x: pd.Series) -> float | None:
    if len(x) == 0:
        return None
    eq = x.cumsum()
    dd = eq - eq.cummax()
    return float(dd.min())


def concentration_shares(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"max_asset_positive_pnl_share": None, "max_quarter_positive_pnl_share": None}
    t = trades.copy()
    t["positive_net10"] = t["net10_bps"].clip(lower=0)
    total = float(t["positive_net10"].sum())
    if total <= 0:
        return {"max_asset_positive_pnl_share": None, "max_quarter_positive_pnl_share": None}
    by_asset = t.groupby("symbol")["positive_net10"].sum()
    q = t["entry_time"].dt.to_period("Q").astype(str)
    by_q = t.assign(quarter=q).groupby("quarter")["positive_net10"].sum()
    return {
        "max_asset_positive_pnl_share": float(by_asset.max() / total),
        "max_quarter_positive_pnl_share": float(by_q.max() / total),
    }


def bootstrap_day_mean(trades: pd.DataFrame, reps: int = BOOT_REPS, seed: int = SEED) -> dict | None:
    if trades.empty:
        return None
    d = trades.copy()
    d["day"] = d["entry_time"].dt.floor("D")
    agg = d.groupby("day")["net10_bps"].agg(["sum", "count"])
    if len(agg) < 2:
        return None
    arr = agg[["sum", "count"]].to_numpy(float)
    rng = np.random.default_rng(seed)
    vals = np.empty(reps, dtype=float)
    for i in range(reps):
        sample = arr[rng.integers(0, len(arr), size=len(arr))].sum(axis=0)
        vals[i] = sample[0] / sample[1]
    return {
        "reps": reps,
        "mean_bps": float(vals.mean()),
        "ci95_low_bps": float(np.quantile(vals, 0.025)),
        "ci95_high_bps": float(np.quantile(vals, 0.975)),
    }


def summarize(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"n": 0}
    t = trades.sort_values(["entry_time", "symbol"]).copy()
    conc = concentration_shares(t)
    per_asset = {}
    for s, g in t.groupby("symbol"):
        per_asset[s] = {
            "n": int(len(g)),
            "gross_mean_bps": float(g["gross_bps"].mean()),
            "net10_mean_bps": float(g["net10_bps"].mean()),
            "pf_net10": profit_factor(g["net10_bps"]),
        }
    q = t["entry_time"].dt.to_period("Q").astype(str)
    quarterly = {k: {"n": int(len(g)), "net10_mean_bps": float(g["net10_bps"].mean())} for k, g in t.assign(quarter=q).groupby("quarter")}
    loo = {}
    for s in SYMBOLS:
        g = t[t["symbol"] != s]
        if len(g):
            loo[s] = float(g["net10_bps"].mean())
    return {
        "n": int(len(t)),
        "gross_mean_bps": float(t["gross_bps"].mean()),
        "gross_median_bps": float(t["gross_bps"].median()),
        "net10_mean_bps": float(t["net10_bps"].mean()),
        "net10_median_bps": float(t["net10_bps"].median()),
        "net14_mean_bps": float(t["net14_bps"].mean()),
        "win_rate_net10": float((t["net10_bps"] > 0).mean()),
        "pf_net10": profit_factor(t["net10_bps"]),
        "max_cumulative_drawdown_bps": max_cum_drawdown(t["net10_bps"]),
        "per_asset": per_asset,
        "quarterly": quarterly,
        "leave_one_asset_out_net10_mean_bps": loo,
        "bootstrap_day_net10_mean": bootstrap_day_mean(t),
        **conc,
    }


def discovery_gate(m: dict) -> dict:
    pf = m.get("pf_net10")
    checks = {
        "n_ge_300": m.get("n", 0) >= DISCOVERY_MIN_TRADES,
        "net10_mean_gt_0": m.get("net10_mean_bps", -math.inf) > 0,
        "pf_net10_gt_1": pf is not None and pf > 1.0,
    }
    return {"checks": checks, "pass": all(checks.values())}


def validation_gate(m: dict) -> dict:
    pf = m.get("pf_net10")
    a = m.get("max_asset_positive_pnl_share")
    q = m.get("max_quarter_positive_pnl_share")
    checks = {
        "n_ge_150": m.get("n", 0) >= VALIDATION_MIN_TRADES,
        "net10_mean_gt_0": m.get("net10_mean_bps", -math.inf) > 0,
        "pf_net10_gt_1": pf is not None and pf > 1.0,
        "max_asset_positive_pnl_share_le_0_70": a is not None and a <= CONCENTRATION_MAX_SHARE,
        "max_quarter_positive_pnl_share_le_0_70": q is not None and q <= CONCENTRATION_MAX_SHARE,
    }
    return {"checks": checks, "pass": all(checks.values())}


def split_trades(trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    return trades[(trades["entry_time"] >= start) & (trades["entry_time"] <= end)].copy()


def write_json(path: Path, obj: dict) -> str:
    text = json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return hashlib.sha256(text.encode()).hexdigest()


def run_phase(
    normalized_dir: Path,
    months: list[str],
    protected_start: pd.Timestamp,
    phase_name: str,
) -> tuple[pd.DataFrame, list[dict]]:
    audits: list[dict] = []
    all_trades: list[pd.DataFrame] = []
    for symbol in SYMBOLS:
        minute, audit = load_symbol(normalized_dir, symbol, months, protected_start)
        hourly = minute_vwap_and_hourly(minute)
        tr = make_vwap_trades(hourly, symbol)
        audits.append(audit.__dict__)
        all_trades.append(tr)
        print(f"{phase_name} {symbol}: minute_rows={len(minute):,} trades={len(tr):,}", flush=True)
    trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    if len(trades):
        for c in ["signal_time", "entry_time", "exit_time"]:
            trades[c] = pd.to_datetime(trades[c], utc=True)
        trades.sort_values(["entry_time", "symbol"], inplace=True)
    return trades, audits


def execute(normalized_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    discovery_all, disc_audits = run_phase(
        normalized_dir, DISCOVERY_MONTHS, VALIDATION_START, "DISCOVERY"
    )
    discovery = split_trades(discovery_all, DISCOVERY_START, DISCOVERY_END)
    disc_metrics = summarize(discovery)
    dgate = discovery_gate(disc_metrics)
    discovery.to_csv(out_dir / f"{EXPERIMENT}_DISCOVERY_TRADES.csv", index=False)

    validation_opened = bool(dgate["pass"])
    if validation_opened:
        validation_all, val_audits = run_phase(
            normalized_dir, VALIDATION_MONTHS, FORBIDDEN_START, "VALIDATION_2024"
        )
        validation = split_trades(validation_all, VALIDATION_START, VALIDATION_END)
        val_metrics = summarize(validation)
        vgate = validation_gate(val_metrics)
        validation.to_csv(out_dir / f"{EXPERIMENT}_VALIDATION_2024_TRADES.csv", index=False)
    else:
        val_audits = []
        val_metrics = {"status": "NOT_OPENED_DUE_DISCOVERY_GATE"}
        vgate = {"checks": {}, "pass": False, "status": "NOT_OPENED"}

    if not dgate["pass"]:
        verdict = "DISCOVERY_FAIL_NO_VALIDATION_ACCESS"
    elif vgate["pass"]:
        verdict = "MVE_1_REPLICATION_READY"
    else:
        verdict = "VALIDATION_FAIL_NO_EDGE_STOP"

    receipt = {
        "lab": LAB,
        "experiment": EXPERIMENT,
        "status": verdict,
        "source": {
            "provider": "Binance",
            "market": "USD-M Futures",
            "interval": "1m",
            "reuse_authority": "H180-0001 normalized canonical layer",
            "canonical_fingerprint": SOURCE_CANONICAL_FP,
            "raw_monthly_fingerprint": SOURCE_RAW_FP,
            "discovery_months_opened": [DISCOVERY_MONTHS[0], DISCOVERY_MONTHS[-1]],
            "validation_2024_members_opened": validation_opened,
            "2025_market_members_opened": False,
            "2026_market_members_opened": False,
            "discovery_load_audits": disc_audits,
            "validation_load_audits": val_audits,
        },
        "frozen_rule": {
            "indicator": "daily_utc_causal_vwap",
            "typical_price": "(high+low+close)/3",
            "weight": "base_volume",
            "session_reset": "00:00 UTC",
            "timeframe": "1H",
            "entry": "next_hour_open",
            "hold_bars": HOLD_BARS,
            "base_cost_bps": BASE_COST_BPS,
            "stress_cost_bps": STRESS_COST_BPS,
            "direction": "reclaim/loss continuation",
        },
        "phase_gates": {
            "discovery_min_trades": DISCOVERY_MIN_TRADES,
            "validation_min_trades": VALIDATION_MIN_TRADES,
            "concentration_max_share": CONCENTRATION_MAX_SHARE,
        },
        "discovery": {
            "range": [str(DISCOVERY_START), str(DISCOVERY_END)],
            "metrics": disc_metrics,
            "gate": dgate,
        },
        "validation_2024_opened": validation_opened,
        "validation_2024": {
            "range": [str(VALIDATION_START), str(VALIDATION_END)],
            "metrics": val_metrics,
            "gate": vgate,
        },
        "protected": {"2025": "UNOPENED", "2026": "LOCKED_UNOPENED"},
        "next_authorized_family_after_closeout": "CIGL-ADX-01",
    }
    result_sha = write_json(out_dir / f"{EXPERIMENT}_RESULT.json", receipt)
    receipt["result_json_sha256"] = result_sha
    write_json(out_dir / f"{EXPERIMENT}_RECEIPT.json", receipt)
    return receipt


def self_test() -> None:
    idx = pd.date_range("2022-01-01", periods=60 * 72, freq="1min", tz="UTC")
    base = 100 + np.sin(np.arange(len(idx)) / 120) * 2 + np.arange(len(idx)) * 0.0005
    df = pd.DataFrame({
        "ts": idx,
        "open": base,
        "high": base + 0.2,
        "low": base - 0.2,
        "close": base + np.sin(np.arange(len(idx)) / 17) * 0.1,
        "volume": np.ones(len(idx)) * 10,
    })
    h = minute_vwap_and_hourly(df)
    tr = make_vwap_trades(h, "TESTUSDT")
    assert len(h) == 72
    assert h["hour_ok"].all()
    assert not ((tr.get("entry_time", pd.Series([], dtype="datetime64[ns, UTC]")) >= FORBIDDEN_START).any())
    print(json.dumps({"self_test": "PASS", "hours": len(h), "trades": len(tr)}, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized-dir", type=Path, help="Directory containing H180 normalized symbol ZIP packages")
    ap.add_argument("--out", type=Path, default=Path("outputs/CLASSIC_INDICATORS_GAP_LAB_V01/CIGL-VWAP-01"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.normalized_dir is None:
        raise SystemExit("--normalized-dir is required unless --self-test is used")
    result = execute(args.normalized_dir, args.out)
    print(json.dumps({"experiment": EXPERIMENT, "status": result["status"], "validation_2024_opened": result["validation_2024_opened"]}, indent=2))


if __name__ == "__main__":
    main()
