#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001 V0.1 — frozen Discovery runner.

IMPORTANT:
- This file does NOT authorize Discovery.
- It refuses to run unless a canonical Source/Data Gate receipt says SOURCE_AUDIT_PASS.
- It reads only already-acquired 2021-04-01..2024-12-31 raw Deribit and BTCUSDT data.
- It never requests network data and never opens 2025 or 2026.
- Rules are copied from canonical Drive authority SHA256
  138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

LAB_ID = "OPTIONS-SPOTPERP-001"
VERSION = "V0.1"
AUTHORITY_SHA256 = "138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa"
START = dt.date(2021, 4, 1)
END = dt.date(2024, 12, 31)
MIN_DTE, MAX_DTE = 30, 120
CALL_MIN, CALL_MAX = 1.05, 1.20
PUT_MIN, PUT_MAX = 0.80, 0.95
MIN_SIDE = 5
MIN_VALID = 500
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
HAC_LAGS = 7
UTC = dt.timezone.utc


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def median(xs: list[float]) -> float:
    return float(statistics.median(xs))


def parse_instrument(name: str) -> tuple[dt.date, float, str]:
    p = name.split("-")
    if len(p) != 4 or p[0] != "BTC" or p[3] not in {"C", "P"}:
        raise ValueError(name)
    expiry = dt.datetime.strptime(p[1].upper(), "%d%b%y").date()
    strike = float(p[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(name)
    return expiry, strike, p[3]


def load_and_bind_receipt(root: Path) -> dict[str, Any]:
    receipt_path = root / "source_gate_calendar_day_reconciled_receipt.json"
    if not receipt_path.exists():
        raise RuntimeError("DISCOVERY_BLOCKED: canonical source-gate receipt missing")
    r = json.loads(receipt_path.read_text(encoding="utf-8"))
    if r.get("status") != "SOURCE_AUDIT_PASS":
        raise RuntimeError(f"DISCOVERY_BLOCKED: source status={r.get('status')!r}")
    auth = r.get("authority", {})
    if auth.get("authority_sha256") != AUTHORITY_SHA256 or auth.get("pass") is not True:
        raise RuntimeError("DISCOVERY_BLOCKED: authority binding mismatch")
    for k in ("skew_values_computed", "signals_computed", "forward_returns_computed", "pnl_computed"):
        if r.get(k) is not False:
            raise RuntimeError(f"DISCOVERY_BLOCKED: source receipt outcome flag {k}")
    if r.get("holdout_2025_accessed") is not False or r.get("year_2026_accessed") is not False:
        raise RuntimeError("DISCOVERY_BLOCKED: protected-period flag")
    cov = r.get("calendar_day_coverage_audit", {})
    if cov.get("coverage_pass") is not True or int(cov.get("valid_signal_coverage_days", 0)) < MIN_VALID:
        raise RuntimeError("DISCOVERY_BLOCKED: canonical coverage gate not passed")
    btc = r.get("btc_price_audit", {})
    if btc.get("exact_discovery_cutoff_verified") is not True:
        raise RuntimeError("DISCOVERY_BLOCKED: BTC cutoff not verified")
    return r


def load_source_manifest(root: Path) -> dict[str, Any]:
    p = root / "source_manifest.json"
    if not p.exists():
        raise RuntimeError("missing source_manifest.json")
    m = json.loads(p.read_text(encoding="utf-8"))
    if m.get("source_fetch_complete") is not True or m.get("probe_mode") is not False:
        raise RuntimeError("source manifest is not a complete full acquisition")
    if m.get("holdout_accessed") is not False or m.get("locked_2026_accessed") is not False:
        raise RuntimeError("protected-period source manifest flag")
    return m


def build_signal(root: Path, manifest: dict[str, Any]) -> tuple[dict[dt.date, float], dict[str, Any]]:
    inst_ivs: dict[dt.date, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    inst_side: dict[str, str] = {}
    raw_rows = 0
    eligible_rows = 0
    rejected_iv = rejected_index = rejected_dte = rejected_moneyness = 0

    for e in manifest.get("raw_pages", []):
        path = root / "raw" / e["page"]
        if not path.exists() or sha256_file(path) != e.get("sha256"):
            raise RuntimeError(f"raw-page integrity failure: {e.get('page')}")
        obj = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
        rows = obj.get("result", {}).get("trades")
        if not isinstance(rows, list):
            raise RuntimeError(f"invalid raw payload: {path.name}")
        for row in rows:
            raw_rows += 1
            ts = int(row["timestamp"])
            t = dt.datetime.fromtimestamp(ts / 1000, tz=UTC)
            day = t.date()
            if day < START or day > END:
                raise RuntimeError(f"raw trade outside frozen Discovery window: {t.isoformat()}")
            name = str(row["instrument_name"])
            expiry, strike, side = parse_instrument(name)
            try:
                iv = float(row["iv"])
                if not math.isfinite(iv) or iv <= 0:
                    raise ValueError
            except Exception:
                rejected_iv += 1
                continue
            try:
                index = float(row["index_price"])
                if not math.isfinite(index) or index <= 0:
                    raise ValueError
            except Exception:
                rejected_index += 1
                continue
            dte = (expiry - day).days
            if not (MIN_DTE <= dte <= MAX_DTE):
                rejected_dte += 1
                continue
            m = strike / index
            ok = (side == "C" and CALL_MIN <= m <= CALL_MAX) or (side == "P" and PUT_MIN <= m <= PUT_MAX)
            if not ok:
                rejected_moneyness += 1
                continue
            inst_ivs[day][name].append(iv)
            inst_side[name] = side
            eligible_rows += 1

    signal: dict[dt.date, float] = {}
    coverage_rows: list[dict[str, Any]] = []
    day = START
    while day <= END:
        calls: list[float] = []
        puts: list[float] = []
        for name, vals in inst_ivs.get(day, {}).items():
            x = median(vals)
            if inst_side[name] == "C": calls.append(x)
            else: puts.append(x)
        valid = len(calls) >= MIN_SIDE and len(puts) >= MIN_SIDE
        coverage_rows.append({"date": day.isoformat(), "calls": len(calls), "puts": len(puts), "valid": valid})
        if valid:
            signal[day] = median(calls) - median(puts)
        day += dt.timedelta(days=1)

    # Cross-check daily coverage artifact produced by canonical source gate when present.
    audit_cov = root / "source_gate_calendar_day_daily_coverage.json"
    if audit_cov.exists():
        a = json.loads(audit_cov.read_text(encoding="utf-8"))
        amap = {row["date"]: (int(row["distinct_eligible_calls"]), int(row["distinct_eligible_puts"]), bool(row["valid_min_5_each_side"])) for row in a.get("rows", [])}
        for row in coverage_rows:
            got = (row["calls"], row["puts"], row["valid"])
            exp = amap.get(row["date"])
            if exp != got:
                raise RuntimeError(f"DISCOVERY_BLOCKED: source/discovery eligibility drift on {row['date']}: {got} != {exp}")

    return signal, {
        "raw_rows": raw_rows,
        "eligible_trade_rows": eligible_rows,
        "iv_rejected": rejected_iv,
        "index_price_rejected": rejected_index,
        "dte_rejected": rejected_dte,
        "moneyness_rejected": rejected_moneyness,
        "valid_signal_days_source_window": len(signal),
    }


def load_btc_opens(root: Path, receipt: dict[str, Any]) -> dict[dt.date, float]:
    out: dict[dt.date, float] = {}
    entries = receipt.get("btc_price_raw_archives", [])
    if len(entries) != 45:
        raise RuntimeError(f"expected 45 BTC monthly archives, got {len(entries)}")
    bdir = root / "raw_binance_btcusdt_1d"
    for e in entries:
        name = str(e["file"])
        if name.startswith("BTCUSDT-1d-2025") or name.startswith("BTCUSDT-1d-2026"):
            raise RuntimeError("protected BTC archive referenced")
        p = bdir / name
        if not p.exists() or sha256_file(p) != e.get("sha256"):
            raise RuntimeError(f"BTC archive integrity failure: {name}")
        with zipfile.ZipFile(p) as zf:
            members = [n for n in zf.namelist() if not n.endswith("/")]
            if len(members) != 1:
                raise RuntimeError(f"unexpected BTC ZIP members: {name}")
            with zf.open(members[0]) as raw:
                for row in csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline="")):
                    if not row: continue
                    ms = int(row[0])
                    x = dt.datetime.fromtimestamp(ms / 1000, tz=UTC)
                    day = x.date()
                    if day < START or day > END:
                        raise RuntimeError(f"BTC row outside frozen window: {day}")
                    op = float(row[1])
                    if not math.isfinite(op) or op <= 0:
                        raise RuntimeError(f"invalid BTC open on {day}")
                    if day in out:
                        raise RuntimeError(f"duplicate BTC day {day}")
                    out[day] = op
    return out


def invert_2x2(a00: float, a01: float, a11: float) -> tuple[float, float, float]:
    det = a00 * a11 - a01 * a01
    if det <= 0 or not math.isfinite(det):
        raise RuntimeError("singular regression design")
    return a11/det, -a01/det, a00/det


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ols_hac7(xs: list[float], ys: list[float]) -> dict[str, float]:
    n = len(xs)
    if n < 20 or n != len(ys):
        raise RuntimeError("insufficient regression observations")
    sx = sum(xs); sy = sum(ys); sxx = sum(x*x for x in xs); sxy = sum(x*y for x,y in zip(xs,ys))
    inv00, inv01, inv11 = invert_2x2(float(n), sx, sxx)
    alpha = inv00*sy + inv01*sxy
    beta = inv01*sy + inv11*sxy
    u = [y - alpha - beta*x for x,y in zip(xs,ys)]

    # Newey-West covariance: (X'X)^-1 S (X'X)^-1, Bartlett kernel, frozen 7 lags.
    s00 = s01 = s11 = 0.0
    for t in range(n):
        z0, z1 = u[t], u[t]*xs[t]
        s00 += z0*z0; s01 += z0*z1; s11 += z1*z1
    L = min(HAC_LAGS, n-1)
    for lag in range(1, L+1):
        w = 1.0 - lag/(L+1.0)
        g00 = g01a = g01b = g11 = 0.0
        for t in range(lag, n):
            ut, ul = u[t], u[t-lag]
            xt, xl = xs[t], xs[t-lag]
            g00 += ut*ul
            g01a += ut*ul*xl
            g01b += ut*xt*ul
            g11 += ut*xt*ul*xl
        s00 += w*(g00+g00)
        s01 += w*(g01a+g01b)
        s11 += w*(g11+g11)

    # Compute beta-beta element of A*S*A with A symmetric inverse.
    var_beta = inv01*inv01*s00 + 2*inv01*inv11*s01 + inv11*inv11*s11
    if var_beta < 0 and abs(var_beta) < 1e-18: var_beta = 0.0
    se = math.sqrt(var_beta) if var_beta >= 0 else float("nan")
    if not math.isfinite(se) or se <= 0:
        raise RuntimeError("invalid HAC beta standard error")
    z = beta/se
    p_one = 1.0 - normal_cdf(z)
    return {"n": n, "alpha": alpha, "beta": beta, "hac_lags": L, "beta_hac_se": se, "z": z, "one_sided_p_beta_gt_0": p_one}


def max_drawdown_from_net_logs(net_logs: list[float]) -> float:
    wealth = peak = 1.0
    mdd = 0.0
    for r in net_logs:
        wealth *= math.exp(r)
        peak = max(peak, wealth)
        dd = wealth/peak - 1.0
        mdd = min(mdd, dd)
    return mdd


def strategy_metrics(rows: list[dict[str, Any]], cost_bps: float) -> dict[str, Any]:
    entered = [r for r in rows if r["position"] != 0]
    net_bps = [r["aligned_gross_bps"] - cost_bps for r in entered]
    gross_bps = [r["aligned_gross_bps"] for r in entered]
    pos = sum(x for x in net_bps if x > 0)
    neg = -sum(x for x in net_bps if x < 0)
    pf = (pos/neg) if neg > 0 else (float("inf") if pos > 0 else 0.0)
    net_logs = [(x/10000.0) for x in net_bps]
    cumulative = math.exp(sum(net_logs)) - 1.0 if net_logs else 0.0
    annual: dict[str, dict[str, float|int]] = {}
    for y in (2021,2022,2023,2024):
        rr = [r for r in entered if r["signal_date"].year == y]
        vals = [r["aligned_gross_bps"] - cost_bps for r in rr]
        gross_vals = [r["aligned_gross_bps"] for r in rr]
        annual[str(y)] = {
            "n": len(rr),
            "net_mean_bps": (sum(vals)/len(vals)) if vals else float("nan"),
            "gross_pnl_bps": sum(gross_vals),
            "net_pnl_bps": sum(vals),
        }
    positive_gross_year_pnl = {y:max(0.0,float(v["gross_pnl_bps"])) for y,v in annual.items()}
    total_positive = sum(positive_gross_year_pnl.values())
    max_positive_share = (max(positive_gross_year_pnl.values())/total_positive) if total_positive > 0 else 1.0
    return {
        "entered_trades": len(entered),
        "long_count": sum(1 for r in entered if r["position"] > 0),
        "short_count": sum(1 for r in entered if r["position"] < 0),
        "gross_mean_bps_per_trade": (sum(gross_bps)/len(gross_bps)) if gross_bps else float("nan"),
        "net_mean_bps_per_trade": (sum(net_bps)/len(net_bps)) if net_bps else float("nan"),
        "cumulative_net_return": cumulative,
        "profit_factor": pf,
        "win_rate": (sum(1 for x in net_bps if x > 0)/len(net_bps)) if net_bps else float("nan"),
        "max_drawdown": max_drawdown_from_net_logs(net_logs),
        "annual": annual,
        "single_year_max_share_of_total_positive_gross_pnl": max_positive_share,
    }


def sanitize_json(x: Any) -> Any:
    if isinstance(x, float) and not math.isfinite(x): return None
    if isinstance(x, dict): return {k:sanitize_json(v) for k,v in x.items()}
    if isinstance(x, list): return [sanitize_json(v) for v in x]
    return x


def run(root: Path, output: Path) -> dict[str, Any]:
    receipt = load_and_bind_receipt(root)
    manifest = load_source_manifest(root)
    signal, signal_audit = build_signal(root, manifest)
    btc = load_btc_opens(root, receipt)

    rows: list[dict[str, Any]] = []
    for day in sorted(signal):
        entry_day = day + dt.timedelta(days=1)
        exit_day = day + dt.timedelta(days=2)
        # Firewall: never cross the frozen Discovery cutoff to complete an outcome.
        if entry_day > END or exit_day > END:
            continue
        if entry_day not in btc or exit_day not in btc:
            raise RuntimeError(f"missing BTC outcome price inside frozen window for signal {day}")
        r = math.log(btc[exit_day]/btc[entry_day])
        skew = signal[day]
        pos = 1 if skew > 0 else (-1 if skew < 0 else 0)
        rows.append({
            "signal_date": day,
            "skew": skew,
            "forward_log_return": r,
            "position": pos,
            "aligned_gross_bps": pos*r*10000.0,
        })

    if len(rows) < MIN_VALID:
        # This criterion is based on evaluable valid signal days, not merely source coverage.
        criterion_a = False
    else:
        criterion_a = True
    reg = ols_hac7([r["skew"] for r in rows], [r["forward_log_return"] for r in rows])
    base = strategy_metrics(rows, BASE_COST_BPS)
    stress = strategy_metrics(rows, STRESS_COST_BPS)

    years_nonnegative = sum(1 for y,v in base["annual"].items() if v["n"] > 0 and float(v["net_mean_bps"]) >= 0)
    gates = {
        "A_valid_signal_days_ge_500": criterion_a,
        "B_beta_positive_and_one_sided_hac_p_le_0_10": reg["beta"] > 0 and reg["one_sided_p_beta_gt_0"] <= 0.10,
        "C_net_mean_10bps_positive": base["net_mean_bps_per_trade"] > 0,
        "D_profit_factor_10bps_gt_1": base["profit_factor"] > 1.0,
        "E_at_least_3_of_4_years_nonnegative_net_mean": years_nonnegative >= 3,
        "F_no_single_year_gt_60pct_positive_gross_pnl": base["single_year_max_share_of_total_positive_gross_pnl"] <= 0.60,
        "G_provenance_timestamp_leakage_coverage_pass": True,
    }
    passed = all(gates.values())
    result = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "authority_sha256": AUTHORITY_SHA256,
        "classification": "MVE0_PASS" if passed else "DISCOVERY_FAIL_NO_PROMOTION",
        "discovery_window": {"start": START.isoformat(), "end": END.isoformat()},
        "evaluable_valid_signal_days": len(rows),
        "source_signal_audit": signal_audit,
        "regression": reg,
        "base_10bps": base,
        "stress_20bps": stress,
        "years_nonnegative_net_mean_10bps": years_nonnegative,
        "gates": gates,
        "mve0_pass": passed,
        "holdout_2025_accessed": False,
        "year_2026_accessed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "notes": [
            "No 2025 price is used to complete 2024-12-30 or 2024-12-31 outcomes; such signal days are not evaluable under V0.1.",
            "20 bps stress is mandatory diagnostic only and is not a pass criterion.",
            "No post-outcome parameter rescue is authorized."
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    out_json = output / "OPTIONS_SPOTPERP_001_DISCOVERY_CLOSEOUT_V01.json"
    out_json.write_text(json.dumps(sanitize_json(result), indent=2, sort_keys=True), encoding="utf-8")
    # Ledger is machine-readable but contains Discovery outcomes; only written when execution is authorized.
    ledger = output / "OPTIONS_SPOTPERP_001_DISCOVERY_LEDGER_V01.csv"
    with ledger.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["signal_date","skew","forward_log_return","position","aligned_gross_bps"])
        for r in rows:
            w.writerow([r["signal_date"].isoformat(), f"{r['skew']:.12g}", f"{r['forward_log_return']:.12g}", r["position"], f"{r['aligned_gross_bps']:.12g}"])
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    result = run(Path(args.source_root).resolve(), Path(args.output).resolve())
    print(result["classification"])
    print(json.dumps({"gates": result["gates"], "holdout_2025_accessed": False, "year_2026_accessed": False}, sort_keys=True))
    return 0 if result["mve0_pass"] else 3

if __name__ == "__main__":
    raise SystemExit(main())
