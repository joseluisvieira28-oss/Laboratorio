from __future__ import annotations

"""Frozen Discovery runner for TFG-VWAP-30M-001.

Research only. Reads only the prospectively frozen 2022-01..2023-12 normalized
Discovery packages. It never opens 2024/2025/2026 market members, never sends
orders, and stops immediately after the frozen Discovery classification.
"""

import argparse
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

LAB_ID = "TFG-VWAP-30M-001"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
MONTHS = tuple(f"{y}-{m:02d}" for y in (2022, 2023) for m in range(1, 13))
DISCOVERY_START = pd.Timestamp("2022-01-01T00:00:00Z")
DISCOVERY_END_EXCLUSIVE = pd.Timestamp("2024-01-01T00:00:00Z")
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 14.0
HOLD_BARS = 8
MIN_TRADES = 300
BOOT_REPS = 5000
BOOT_SEED = 20260913
FROZEN_SOURCE_MEMBER_FP = "aa6083e8302fde760a1b78340d8b15f34d3e469f0726b4418d8d1a95b75b6b24"
EXPECTED_PACKAGE_SHA256 = {
    "BTCUSDT": "cd7c6b0e1bbc913932bdcb8ed402403bb35f7f273c0755fb45a0593302569584",
    "ETHUSDT": "1aff6f2741506a3be790fbe711c25d376f09db7f95bd029c1b64a862c5a0c5a9",
    "SOLUSDT": "ac951d9f885cf8d21db9b51f431de77e3f3699cc8a7bce5c392646adf8572e61",
    "BNBUSDT": "815b386f02f7b6ce7a599054b36a5313141b3d76a82fefa939b43f2bc9ff413c",
    "XRPUSDT": "4d777fae365a16fc5f238e2203b464c4ea60bc3b9c203cec99867adcc63cd71a",
    "DOGEUSDT": "b900653fa9a72b4ac830ab0e6ab0abe3d7d883d37c293005c75c47f26cee0929",
}
EXPECTED_ROWS = {
    "BTCUSDT": 1051200,
    "ETHUSDT": 1051200,
    "SOLUSDT": 1044000,
    "BNBUSDT": 1051200,
    "XRPUSDT": 1044000,
    "DOGEUSDT": 1051200,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def expected_member(symbol: str, ym: str) -> str:
    return f"{symbol}/1m/{symbol}-1m-{ym}.normalized.csv.zst"


def load_authority(binding_path: Path) -> dict:
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    if binding.get("experiment_id") != LAB_ID:
        raise RuntimeError("SOURCE_BINDING_EXPERIMENT_MISMATCH")
    if binding.get("status") != "FROZEN_BEFORE_ANY_VWAP_30M_OUTCOME_EVALUATION":
        raise RuntimeError("SOURCE_BINDING_STATUS_MISMATCH")
    if binding.get("frozen_discovery_source_member_fingerprint") != FROZEN_SOURCE_MEMBER_FP:
        raise RuntimeError("SOURCE_BINDING_FINGERPRINT_MISMATCH")
    if binding.get("internal_oos_2024_remains_locked") is not True:
        raise RuntimeError("2024_FIREWALL_NOT_LOCKED")
    if binding.get("protected_2025_remains_locked") is not True:
        raise RuntimeError("2025_FIREWALL_NOT_LOCKED")
    if binding.get("locked_2026_onward_remains_locked") is not True:
        raise RuntimeError("2026_FIREWALL_NOT_LOCKED")
    if binding.get("normalized_package_sha256_discovery_only", {}) != EXPECTED_PACKAGE_SHA256:
        raise RuntimeError("FROZEN_PACKAGE_HASH_MAP_MISMATCH")
    return binding


def load_symbol(normalized_dir: Path, symbol: str) -> tuple[pd.DataFrame, dict]:
    package = normalized_dir / f"H180-0001_NORMALIZED_{symbol}.zip"
    if not package.is_file():
        raise RuntimeError(f"MISSING_FROZEN_PACKAGE:{package.name}")
    actual_sha = sha256_file(package)
    if actual_sha != EXPECTED_PACKAGE_SHA256[symbol]:
        raise RuntimeError(f"PACKAGE_SHA256_MISMATCH:{symbol}:{actual_sha}")

    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(package, "r") as archive:
        names = set(archive.namelist())
        forbidden = [n for n in names if any(f"-{y}-" in n or f"/{y}-" in n for y in (2024, 2025, 2026, 2027, 2028, 2029))]
        if forbidden:
            raise RuntimeError(f"FORBIDDEN_YEAR_MEMBER_PRESENT:{symbol}:{forbidden[0]}")
        required = [expected_member(symbol, ym) for ym in MONTHS]
        missing = [m for m in required if m not in names]
        if missing:
            raise RuntimeError(f"MISSING_DISCOVERY_MEMBER:{symbol}:{missing[0]}")
        unexpected = [n for n in names if n.endswith(".normalized.csv.zst") and n not in required]
        if unexpected:
            raise RuntimeError(f"UNEXPECTED_NORMALIZED_MEMBER:{symbol}:{unexpected[0]}")

        try:
            import zstandard as zstd
        except ImportError as exc:
            raise RuntimeError("ZSTANDARD_DEPENDENCY_MISSING") from exc

        for ym, member in zip(MONTHS, required):
            with archive.open(member, "r") as raw, zstd.ZstdDecompressor().stream_reader(raw) as zr:
                df = pd.read_csv(
                    io.TextIOWrapper(zr, encoding="utf-8", newline=""),
                    usecols=["open_time", "open", "high", "low", "close", "volume"],
                )
            frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    cols = ["open_time", "open", "high", "low", "close", "volume"]
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    invalid = int(df[cols].isna().any(axis=1).sum())
    if invalid:
        raise RuntimeError(f"INVALID_NUMERIC_ROWS:{symbol}:{invalid}")
    df["open_time"] = df["open_time"].astype("int64")
    df["ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df.sort_values("ts", inplace=True)
    duplicates = int(df["ts"].duplicated().sum())
    if duplicates:
        raise RuntimeError(f"DUPLICATE_TIMESTAMPS:{symbol}:{duplicates}")
    if len(df) != EXPECTED_ROWS[symbol]:
        raise RuntimeError(f"ROW_COUNT_MISMATCH:{symbol}:{len(df)}")
    if (df["ts"] < DISCOVERY_START).any() or (df["ts"] >= DISCOVERY_END_EXCLUSIVE).any():
        raise RuntimeError(f"DISCOVERY_RANGE_VIOLATION:{symbol}")

    audit = {
        "symbol": symbol,
        "package": package.name,
        "package_sha256": actual_sha,
        "rows": int(len(df)),
        "expected_rows": EXPECTED_ROWS[symbol],
        "first_ts": str(df["ts"].iloc[0]),
        "last_ts": str(df["ts"].iloc[-1]),
        "duplicates": duplicates,
        "invalid_numeric_rows": invalid,
        "months_opened": [MONTHS[0], MONTHS[-1]],
        "2024_members_opened": False,
        "2025_members_opened": False,
        "2026_members_opened": False,
    }
    return df[["ts", "open", "high", "low", "close", "volume"]].copy(), audit


def minute_vwap_and_30m(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy().set_index("ts").sort_index()
    day = d.index.floor("D")
    minute_of_day = d.index.hour * 60 + d.index.minute

    counts = pd.Series(1, index=d.index).groupby(day).cumsum().to_numpy()
    expected = minute_of_day.to_numpy() + 1
    sequential = counts == expected
    vol = d["volume"].to_numpy(float)
    vol_ok = np.isfinite(vol) & (vol > 0)
    local_ok = sequential & vol_ok
    session_ok = pd.Series(local_ok, index=d.index).groupby(day).cummin().astype(bool)

    tp = (d["high"] + d["low"] + d["close"]) / 3.0
    pv = tp * d["volume"]
    cum_pv = pv.groupby(day).cumsum()
    cum_vol = d["volume"].groupby(day).cumsum()
    d["vwap"] = (cum_pv / cum_vol).where(session_ok)
    d["session_ok"] = session_ok

    q = d.resample("30min", label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        minute_count=("close", "count"),
        vwap=("vwap", "last"),
        session_ok=("session_ok", "last"),
    )
    q["bar_ok"] = (
        q["minute_count"].eq(30)
        & q["session_ok"].fillna(False).astype(bool)
        & q[["open", "close", "vwap"]].notna().all(axis=1)
    )
    return q


def make_trades(bars: pd.DataFrame, symbol: str) -> tuple[pd.DataFrame, dict]:
    b = bars.copy()
    prev_ok = b["bar_ok"].shift(1).eq(True)
    cur_ok = b["bar_ok"].fillna(False).astype(bool)
    long_sig = prev_ok & cur_ok & (b["close"].shift(1) <= b["vwap"].shift(1)) & (b["close"] > b["vwap"])
    short_sig = prev_ok & cur_ok & (b["close"].shift(1) >= b["vwap"].shift(1)) & (b["close"] < b["vwap"])
    direction = pd.Series(0, index=b.index, dtype="int8")
    direction[long_sig] = 1
    direction[short_sig] = -1

    rows: list[dict] = []
    next_free_entry_pos = -1
    signal_count = int((direction != 0).sum())
    overlap_skipped = 0
    boundary_skipped = 0
    invalid_price_skipped = 0
    idx = b.index
    for signal_pos, sig in enumerate(direction.to_numpy()):
        if sig == 0:
            continue
        entry_pos = signal_pos + 1
        exit_pos = entry_pos + HOLD_BARS
        if entry_pos <= next_free_entry_pos:
            overlap_skipped += 1
            continue
        if exit_pos >= len(b):
            boundary_skipped += 1
            continue
        entry_t = idx[entry_pos]
        exit_t = idx[exit_pos]
        if entry_t >= DISCOVERY_END_EXCLUSIVE or exit_t >= DISCOVERY_END_EXCLUSIVE:
            boundary_skipped += 1
            continue
        entry_px = b["open"].iloc[entry_pos]
        exit_px = b["open"].iloc[exit_pos]
        if not (np.isfinite(entry_px) and np.isfinite(exit_px) and entry_px > 0 and exit_px > 0):
            invalid_price_skipped += 1
            continue
        gross = float(sig * math.log(float(exit_px) / float(entry_px)) * 10000.0)
        rows.append({
            "symbol": symbol,
            "signal_time": idx[signal_pos],
            "entry_time": entry_t,
            "exit_time": exit_t,
            "direction": int(sig),
            "entry_price": float(entry_px),
            "exit_price": float(exit_px),
            "signal_close": float(b["close"].iloc[signal_pos]),
            "signal_vwap": float(b["vwap"].iloc[signal_pos]),
            "gross_bps": gross,
            "net10_bps": gross - BASE_COST_BPS,
            "net14_bps": gross - STRESS_COST_BPS,
        })
        next_free_entry_pos = exit_pos - 1
    return pd.DataFrame(rows), {
        "raw_signal_count": signal_count,
        "selected_trade_count": len(rows),
        "overlap_skipped_count": overlap_skipped,
        "boundary_skipped_count": boundary_skipped,
        "invalid_price_skipped_count": invalid_price_skipped,
    }


def profit_factor(values: pd.Series) -> float | None:
    pos = float(values[values > 0].sum())
    neg = float(-values[values < 0].sum())
    if neg == 0:
        return None if pos == 0 else float("inf")
    return pos / neg


def bootstrap_day_mean(trades: pd.DataFrame) -> dict | None:
    if trades.empty:
        return None
    d = trades.copy()
    d["day"] = d["entry_time"].dt.floor("D")
    agg = d.groupby("day")["net10_bps"].agg(["sum", "count"])
    if len(agg) < 2:
        return None
    arr = agg[["sum", "count"]].to_numpy(float)
    rng = np.random.default_rng(BOOT_SEED)
    vals = np.empty(BOOT_REPS, dtype=float)
    for i in range(BOOT_REPS):
        s = arr[rng.integers(0, len(arr), size=len(arr))].sum(axis=0)
        vals[i] = s[0] / s[1]
    return {
        "method": "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP_DIAGNOSTIC_ONLY",
        "repetitions": BOOT_REPS,
        "seed": BOOT_SEED,
        "mean_bps": float(vals.mean()),
        "ci95_low_bps": float(np.quantile(vals, 0.025)),
        "ci95_high_bps": float(np.quantile(vals, 0.975)),
        "gate_use": False,
    }


def summarize(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"n": 0}
    t = trades.sort_values(["entry_time", "symbol"]).copy()
    per_asset = {}
    for symbol, g in t.groupby("symbol"):
        per_asset[symbol] = {
            "n": int(len(g)),
            "gross_mean_bps": float(g["gross_bps"].mean()),
            "net10_mean_bps": float(g["net10_bps"].mean()),
            "net14_mean_bps": float(g["net14_bps"].mean()),
            "pf_net10": profit_factor(g["net10_bps"]),
            "pf_net14": profit_factor(g["net14_bps"]),
        }
    quarter = t["entry_time"].dt.to_period("Q").astype(str)
    quarterly = {
        q: {"n": int(len(g)), "net10_mean_bps": float(g["net10_bps"].mean())}
        for q, g in t.assign(quarter=quarter).groupby("quarter")
    }
    return {
        "n": int(len(t)),
        "gross_mean_bps": float(t["gross_bps"].mean()),
        "gross_median_bps": float(t["gross_bps"].median()),
        "net10_mean_bps": float(t["net10_bps"].mean()),
        "net10_median_bps": float(t["net10_bps"].median()),
        "net14_mean_bps": float(t["net14_bps"].mean()),
        "net14_median_bps": float(t["net14_bps"].median()),
        "win_rate_net10": float((t["net10_bps"] > 0).mean()),
        "profit_factor_net10": profit_factor(t["net10_bps"]),
        "profit_factor_net14": profit_factor(t["net14_bps"]),
        "per_asset": per_asset,
        "quarterly": quarterly,
        "bootstrap_day_net10_mean": bootstrap_day_mean(t),
    }


def classify(metrics: dict) -> dict:
    n = int(metrics.get("n", 0))
    net = float(metrics.get("net10_mean_bps", float("-inf"))) if n else float("-inf")
    pf = metrics.get("profit_factor_net10")
    checks = {
        "n_ge_300": n >= MIN_TRADES,
        "net10_mean_bps_gt_0": n > 0 and net > 0,
        "profit_factor_net10_gt_1": pf is not None and pf > 1.0,
    }
    if not checks["n_ge_300"]:
        classification = "INSUFFICIENT_SAMPLE"
    elif all(checks.values()):
        classification = "SURVIVES_DISCOVERY"
    else:
        classification = "NO_EDGE"
    return {
        "classification": classification,
        "checks": checks,
        "minimum_required_trades": MIN_TRADES,
        "internal_oos_2024_unlock_eligible": classification == "SURVIVES_DISCOVERY",
        "internal_oos_2024_opened": False,
    }


def execute(normalized_dir: Path, binding_path: Path, output_dir: Path) -> dict:
    binding = load_authority(binding_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_audits = []
    signal_audits = {}
    all_trades = []

    for symbol in SYMBOLS:
        minute, source_audit = load_symbol(normalized_dir, symbol)
        bars = minute_vwap_and_30m(minute)
        trades, signal_audit = make_trades(bars, symbol)
        source_audits.append(source_audit)
        signal_audits[symbol] = {
            **signal_audit,
            "derived_30m_bar_count": int(len(bars)),
            "valid_30m_bar_count": int(bars["bar_ok"].sum()),
        }
        all_trades.append(trades)
        print(f"DISCOVERY {symbol}: minute_rows={len(minute):,} valid_30m={int(bars['bar_ok'].sum()):,} trades={len(trades):,}", flush=True)

    trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    if len(trades):
        for c in ("signal_time", "entry_time", "exit_time"):
            trades[c] = pd.to_datetime(trades[c], utc=True)
        trades.sort_values(["entry_time", "symbol"], inplace=True)
        if (trades["entry_time"] >= DISCOVERY_END_EXCLUSIVE).any() or (trades["exit_time"] >= DISCOVERY_END_EXCLUSIVE).any():
            raise RuntimeError("TRADE_RANGE_FIREWALL_VIOLATION")

    metrics = summarize(trades)
    decision = classify(metrics)
    trades_path = output_dir / "TFG_VWAP_30M_001_DISCOVERY_TRADES_V0.1.csv"
    trades.to_csv(trades_path, index=False)
    receipt = {
        "status": "TFG_VWAP_30M_DISCOVERY_COMPLETE",
        "lab_id": LAB_ID,
        "stage": "DISCOVERY",
        "source_binding_status": binding["status"],
        "frozen_discovery_source_member_fingerprint": FROZEN_SOURCE_MEMBER_FP,
        "source_package_audits": source_audits,
        "signal_audits": signal_audits,
        "frozen_rule": {
            "signal_timeframe": "30m",
            "daily_vwap_reset": "00:00 UTC",
            "typical_price": "(high+low+close)/3",
            "weight": "base_volume",
            "orientation": "continuation_reclaim_loss",
            "entry": "NEXT_30M_BAR_OPEN",
            "hold_bars": HOLD_BARS,
            "holding_horizon": "4h",
            "base_roundtrip_cost_bps": BASE_COST_BPS,
            "stress_roundtrip_cost_bps": STRESS_COST_BPS,
            "filters": None,
            "one_position_per_asset": True,
            "pyramiding": False,
        },
        "discovery_range": [str(DISCOVERY_START), str(DISCOVERY_END_EXCLUSIVE)],
        "metrics": metrics,
        "decision": decision,
        "outcome_evaluation_performed": True,
        "internal_oos_2024_access_performed": False,
        "protected_2025_access_performed": False,
        "locked_2026_access_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
        "live_trading_authorized": False,
        "merge_to_main_authorized": False,
        "render_deploy_authorized": False,
        "post_outcome_tuning_authorized": False,
        "stop_rule": "STOP_AFTER_DISCOVERY_CLASSIFICATION_NO_2024_ACCESS",
    }
    (output_dir / "TFG_VWAP_30M_001_DISCOVERY_RECEIPT_V0.1.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return receipt


def self_test() -> None:
    idx = pd.date_range("2022-01-01", periods=60 * 24 * 4, freq="1min", tz="UTC")
    x = np.arange(len(idx), dtype=float)
    base = 100.0 + np.sin(x / 120.0) * 2.0 + x * 0.0002
    df = pd.DataFrame({
        "ts": idx,
        "open": base,
        "high": base + 0.2,
        "low": base - 0.2,
        "close": base + np.sin(x / 17.0) * 0.15,
        "volume": np.full(len(idx), 10.0),
    })
    bars = minute_vwap_and_30m(df)
    assert len(bars) == 24 * 2 * 4
    assert bool(bars["bar_ok"].all())
    trades, audit = make_trades(bars, "TESTUSDT")
    if len(trades):
        delta = trades["exit_time"] - trades["entry_time"]
        assert (delta == pd.Timedelta(hours=4)).all()
    print(json.dumps({"self_test": "PASS", "bars": len(bars), "trades": len(trades), "audit": audit}, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen TFG-VWAP-30M-001 Discovery runner")
    parser.add_argument("--normalized-dir", type=Path)
    parser.add_argument("--binding", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.normalized_dir is None or args.binding is None or args.output_dir is None:
        raise SystemExit("--normalized-dir, --binding, and --output-dir are required")
    try:
        receipt = execute(args.normalized_dir, args.binding, args.output_dir)
        print(json.dumps({
            "status": receipt["status"],
            "classification": receipt["decision"]["classification"],
            "n": receipt["metrics"].get("n", 0),
            "net10_mean_bps": receipt["metrics"].get("net10_mean_bps"),
            "profit_factor_net10": receipt["metrics"].get("profit_factor_net10"),
            "net14_mean_bps": receipt["metrics"].get("net14_mean_bps"),
            "internal_oos_2024_access_performed": False,
        }, indent=2))
        return 0
    except Exception as exc:
        if args.output_dir is not None:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            blocked = {
                "status": "BLOCKED_PRE_OR_DURING_DISCOVERY_TECHNICAL_OR_DATA_GATE",
                "lab_id": LAB_ID,
                "reason": f"{type(exc).__name__}:{exc}",
                "outcome_classification_emitted": False,
                "internal_oos_2024_access_performed": False,
                "protected_2025_access_performed": False,
                "locked_2026_access_performed": False,
                "exchange_mutation_performed": False,
                "orders_submitted": False,
            }
            (args.output_dir / "TFG_VWAP_30M_001_DISCOVERY_BLOCKED_V0.1.json").write_text(
                json.dumps(blocked, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(blocked, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
