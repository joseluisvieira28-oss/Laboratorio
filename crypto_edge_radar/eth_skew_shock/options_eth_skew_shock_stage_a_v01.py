#!/usr/bin/env python3
"""Stage-A 2021-2023 back-validation for OPTIONS-ETH-SKEW-SHOCK-001 V0.1."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import sqlite3
import statistics
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
RV_WINDOW = 20
MIN_RV_HISTORY = 60
PRICE_START = dt.date(2020, 1, 1)
PRICE_END = dt.date(2023, 12, 31)
SIGNAL_START = dt.date(2021, 1, 1)
SIGNAL_END = dt.date(2023, 12, 31)
EXPECTED_MONTHS = [f"{y}-{m:02d}" for y in (2021, 2022, 2023) for m in range(1, 13)]


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-ETH-Skew-Shock-Backvalidation/0.1"})
    last: Exception | None = None
    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read()
            if not body:
                raise RuntimeError("empty price archive")
            return body
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, RuntimeError) as exc:
            last = exc
            if attempt < 5:
                time.sleep(min(8.0, 1.5 * attempt))
    raise RuntimeError(f"price source fetch failed: {last}")


def iter_months(start: dt.date, end: dt.date):
    cur = dt.date(start.year, start.month, 1)
    while cur <= end:
        yield cur.strftime("%Y-%m")
        cur = dt.date(cur.year + 1, 1, 1) if cur.month == 12 else dt.date(cur.year, cur.month + 1, 1)


def load_prices() -> tuple[dict[dt.date, dict[str, float]], list[dict[str, Any]]]:
    symbol = "ETHUSDT"
    daily: dict[dt.date, dict[str, float]] = {}
    manifest: list[dict[str, Any]] = []

    for ym in iter_months(PRICE_START, PRICE_END):
        url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"
        body = request_bytes(url)
        manifest.append(
            {
                "month": ym,
                "url": url,
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
            }
        )
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            members = [n for n in zf.namelist() if not n.endswith("/")]
            if len(members) != 1:
                raise RuntimeError(f"unexpected price ZIP members for {ym}")
            with zf.open(members[0]) as raw:
                for row in csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline="")):
                    if not row:
                        continue
                    try:
                        raw_ts = int(row[0])
                    except Exception:
                        continue
                    sec = raw_ts / 1_000_000.0 if raw_ts > 100_000_000_000_000 else raw_ts / 1000.0
                    day = dt.datetime.fromtimestamp(sec, tz=UTC).date()
                    op = float(row[1])
                    cl = float(row[4])
                    if not all(math.isfinite(v) and v > 0 for v in (op, cl)):
                        raise RuntimeError(f"invalid ETHUSDT OHLC on {day}")
                    if day in daily:
                        raise RuntimeError(f"duplicate ETHUSDT day {day}")
                    daily[day] = {"open": op, "close": cl}

    if any(day.year >= 2024 for day in daily):
        raise RuntimeError("calendar 2024+ price access blocked in Stage A")

    days = sorted(daily)
    if not days or days[0] > PRICE_START or days[-1] < PRICE_END:
        raise RuntimeError("price-history boundary incomplete")
    for i in range(1, len(days)):
        if (days[i] - days[i - 1]).days != 1:
            raise RuntimeError(f"ETHUSDT daily continuity failure {days[i-1]}->{days[i]}")

    return daily, manifest


def rv20_series(prices: dict[dt.date, dict[str, float]]) -> dict[dt.date, float]:
    days = sorted(prices)
    rets: list[tuple[dt.date, float]] = []
    for i in range(1, len(days)):
        rets.append((days[i], math.log(prices[days[i]]["close"] / prices[days[i - 1]]["close"])))

    out: dict[dt.date, float] = {}
    for i in range(RV_WINDOW - 1, len(rets)):
        vals = [rets[j][1] for j in range(i - RV_WINDOW + 1, i + 1)]
        rv = statistics.stdev(vals)
        if not math.isfinite(rv) or rv <= 0:
            raise RuntimeError(f"invalid RV20 on {rets[i][0]}")
        out[rets[i][0]] = float(rv)
    return out


def causal_weights(rv: dict[dt.date, float]) -> dict[dt.date, float]:
    out: dict[dt.date, float] = {}
    hist: list[float] = []
    for day in sorted(rv):
        x = rv[day]
        hist.append(x)
        if len(hist) < MIN_RV_HISTORY:
            continue
        med = float(statistics.median(hist))
        w = min(1.0, med / x)
        if not math.isfinite(w) or not (0 < w <= 1.0):
            raise RuntimeError(f"invalid causal weight {day}: {w}")
        out[day] = w
    return out


def max_drawdown(net_bps: list[float]) -> float:
    wealth = peak = 1.0
    mdd = 0.0
    for x in net_bps:
        wealth *= math.exp(x / 10000.0)
        peak = max(peak, wealth)
        mdd = min(mdd, wealth / peak - 1.0)
    return mdd


def metrics(rows: list[dict[str, Any]], cost_bps: float) -> dict[str, Any]:
    entered = [r for r in rows if r["position"] != 0 and r["weight"] > 0]
    gross = [r["aligned_unscaled_gross_bps"] * r["weight"] for r in entered]
    net = [g - cost_bps * r["weight"] for g, r in zip(gross, entered)]
    weights = [r["weight"] for r in entered]

    pos = sum(x for x in net if x > 0)
    neg = -sum(x for x in net if x < 0)
    pf = pos / neg if neg > 0 else (float("inf") if pos > 0 else 0.0)

    annual: dict[str, dict[str, Any]] = {}
    for year in (2021, 2022, 2023):
        rr = [r for r in entered if r["signal_date"].year == year]
        gv = [r["aligned_unscaled_gross_bps"] * r["weight"] for r in rr]
        nv = [g - cost_bps * r["weight"] for g, r in zip(gv, rr)]
        annual[str(year)] = {
            "n": len(rr),
            "gross_pnl_bps": sum(gv),
            "net_pnl_bps": sum(nv),
            "net_mean_bps": sum(nv) / len(nv) if nv else None,
            "mean_weight": sum(r["weight"] for r in rr) / len(rr) if rr else None,
        }

    positive_gross = {y: max(0.0, float(v["gross_pnl_bps"])) for y, v in annual.items()}
    total_positive = sum(positive_gross.values())
    concentration = max(positive_gross.values()) / total_positive if total_positive > 0 else 1.0

    return {
        "entered_scaled_trades": len(entered),
        "average_executed_notional": sum(weights) / len(weights) if weights else 0.0,
        "total_executed_notional_units": sum(weights),
        "long_count": sum(1 for r in entered if r["position"] > 0),
        "short_count": sum(1 for r in entered if r["position"] < 0),
        "gross_mean_bps_per_opportunity": sum(gross) / len(gross) if gross else None,
        "net_mean_bps_per_opportunity": sum(net) / len(net) if net else None,
        "profit_factor": pf,
        "cumulative_net_return": math.exp(sum(x / 10000.0 for x in net)) - 1.0 if net else 0.0,
        "max_drawdown": max_drawdown(net),
        "win_rate": sum(1 for x in net if x > 0) / len(net) if net else None,
        "annual": annual,
        "single_year_max_share_of_total_positive_gross_pnl": concentration,
    }


def sanitize(x: Any) -> Any:
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: sanitize(v) for k, v in x.items()}
    if isinstance(x, list):
        return [sanitize(v) for v in x]
    return x


def load_source(root: Path, scratch: Path) -> tuple[dict[dt.date, float], dict[str, Any]]:
    skews: dict[dt.date, float] = {}
    receipts = []
    db_path = scratch / "trade_ids.sqlite"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE ids (trade_id TEXT PRIMARY KEY)")
    global_dups = 0

    try:
        for month in EXPECTED_MONTHS:
            daily_files = list(root.rglob(f"eth_{month}_daily_skew.json"))
            receipt_files = list(root.rglob(f"eth_{month}_source_receipt.json"))
            id_files = list(root.rglob(f"eth_{month}_trade_ids.txt.gz"))
            if len(daily_files) != 1 or len(receipt_files) != 1 or len(id_files) != 1:
                raise RuntimeError(f"missing or duplicate Stage-A source artifact for {month}")

            rec = json.loads(receipt_files[0].read_text(encoding="utf-8"))
            if rec.get("status") != "PASS":
                raise RuntimeError(f"source shard not PASS for {month}: {rec.get('status')}")
            if rec.get("outcome_source_contacted") is not False:
                raise RuntimeError("source/outcome firewall violated")
            if rec.get("calendar_2024_accessed") is not False or rec.get("year_2026_accessed") is not False:
                raise RuntimeError("protected-period source firewall violated")
            receipts.append(rec)

            daily_obj = json.loads(daily_files[0].read_text(encoding="utf-8"))
            for row in daily_obj.get("daily", []):
                if not row.get("valid"):
                    continue
                day = dt.date.fromisoformat(row["date"])
                if not (SIGNAL_START <= day <= SIGNAL_END):
                    raise RuntimeError(f"daily skew outside Stage-A window: {day}")
                if day in skews:
                    raise RuntimeError(f"duplicate daily skew {day}")
                skew = float(row["skew"])
                if not math.isfinite(skew):
                    raise RuntimeError(f"invalid daily skew {day}")
                skews[day] = skew

            with gzip.open(id_files[0], "rt", encoding="utf-8") as fh:
                batch = []
                for line in fh:
                    tid = line.strip()
                    if not tid:
                        continue
                    batch.append((tid,))
                    if len(batch) >= 5000:
                        for item in batch:
                            try:
                                con.execute("INSERT INTO ids(trade_id) VALUES(?)", item)
                            except sqlite3.IntegrityError:
                                global_dups += 1
                        con.commit()
                        batch.clear()
                for item in batch:
                    try:
                        con.execute("INSERT INTO ids(trade_id) VALUES(?)", item)
                    except sqlite3.IntegrityError:
                        global_dups += 1
                con.commit()

        unique_ids = int(con.execute("SELECT COUNT(*) FROM ids").fetchone()[0])
    finally:
        con.close()

    audit = {
        "months": EXPECTED_MONTHS,
        "source_rows": sum(int(r.get("source_rows", 0)) for r in receipts),
        "target_rows": sum(int(r.get("target_rows", 0)) for r in receipts),
        "eligible_rows": sum(int(r.get("eligible_rows", 0)) for r in receipts),
        "invalid_iv": sum(int(r.get("invalid_iv", 0)) for r in receipts),
        "invalid_index": sum(int(r.get("invalid_index", 0)) for r in receipts),
        "parse_failures": sum(int(r.get("parse_failures", 0)) for r in receipts),
        "within_month_duplicates": sum(int(r.get("duplicate_trade_ids", 0)) for r in receipts),
        "global_duplicate_trade_ids": global_dups,
        "global_unique_trade_ids": unique_ids,
        "valid_daily_skew_days": len(skews),
    }
    if audit["parse_failures"] != 0 or audit["within_month_duplicates"] != 0 or global_dups != 0:
        raise RuntimeError(f"source structural audit failed: {audit}")

    return skews, audit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root)
    freeze_path = repo / "crypto_edge_radar/eth_skew_shock/OPTIONS_ETH_SKEW_SHOCK_001_PRE_OUTCOME_FREEZE_V0.1.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_PRE_OUTCOME":
        raise RuntimeError("skew-shock freeze not active")
    if freeze.get("calendar_2024_for_promotion") is not False:
        raise RuntimeError("2024 promotion firewall drift")
    if freeze.get("protected_2025", {}).get("locked_until_stage_a_pass") is not True:
        raise RuntimeError("2025 lock drift")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch = out_dir / "_scratch"
    scratch.mkdir(parents=True, exist_ok=True)

    skews, source_audit = load_source(Path(args.source_root), scratch)
    prices, price_manifest = load_prices()
    rv = rv20_series(prices)
    weights = causal_weights(rv)

    rows = []
    unresolved = []
    for day in sorted(skews):
        prev = day - dt.timedelta(days=1)
        if prev not in skews:
            unresolved.append({"signal_date": day.isoformat(), "reason": "PREVIOUS_CALENDAR_DAY_SKEW_INVALID_OR_OUTSIDE_WINDOW"})
            continue

        shock = skews[day] - skews[prev]
        position = 1 if shock > 0 else (-1 if shock < 0 else 0)
        entry = day + dt.timedelta(days=1)
        exit_ = day + dt.timedelta(days=2)

        if entry > SIGNAL_END or exit_ > SIGNAL_END:
            unresolved.append({"signal_date": day.isoformat(), "reason": "WOULD_REQUIRE_2024_OUTCOME"})
            continue
        if entry not in prices or exit_ not in prices:
            raise RuntimeError(f"missing ETHUSDT Stage-A price for {day}")

        fwd = math.log(prices[exit_]["open"] / prices[entry]["open"])
        weight = float(weights.get(day, 0.0))
        rows.append(
            {
                "signal_date": day,
                "skew": skews[day],
                "previous_skew": skews[prev],
                "shock": shock,
                "position": position,
                "forward_log_return": fwd,
                "aligned_unscaled_gross_bps": position * fwd * 10000.0,
                "rv20": rv.get(day),
                "weight": weight,
            }
        )

    base = metrics(rows, BASE_COST_BPS)
    stress = metrics(rows, STRESS_COST_BPS)

    nonnegative_years = sum(
        1
        for v in base["annual"].values()
        if v["n"] > 0 and v["net_mean_bps"] is not None and v["net_mean_bps"] >= 0
    )

    gates = {
        "A_provenance_source_leakage_pass": True,
        "B_entered_scaled_trades_ge_300": base["entered_scaled_trades"] >= 300,
        "C_average_executed_notional_ge_0_40": base["average_executed_notional"] >= 0.40,
        "D_base10_net_mean_positive": (base["net_mean_bps_per_opportunity"] if base["net_mean_bps_per_opportunity"] is not None else -1e99) > 0,
        "E_base10_profit_factor_gt_1": base["profit_factor"] > 1.0,
        "F_base10_cumulative_net_return_positive": base["cumulative_net_return"] > 0,
        "G_at_least_2_of_3_years_nonnegative": nonnegative_years >= 2,
        "H_single_year_positive_gross_share_lte_0_60": base["single_year_max_share_of_total_positive_gross_pnl"] <= 0.60,
        "I_exact_identity_unchanged": True,
    }
    survives = all(gates.values())
    classification = (
        "BACKVALIDATION_SURVIVES__2025_OOS_UNLOCKED"
        if survives
        else "BACKVALIDATION_REJECTED__2025_REMAINS_LOCKED"
    )

    result = {
        "candidate_id": "OPTIONS-ETH-SKEW-SHOCK-001-V0.1",
        "classification": classification,
        "stage_a_window": {"start": SIGNAL_START.isoformat(), "end": SIGNAL_END.isoformat()},
        "calendar_2024_used_for_promotion": False,
        "source_audit": source_audit,
        "valid_daily_skew_days": len(skews),
        "evaluable_rows": len(rows),
        "unresolved_signals": unresolved,
        "price_source": {
            "provider": "Binance Vision Spot monthly klines",
            "symbol": "ETHUSDT",
            "archives": price_manifest,
        },
        "base_10bps": base,
        "stress_20bps": stress,
        "nonnegative_years": nonnegative_years,
        "gates": gates,
        "high_risk_fragility": base["max_drawdown"] < -0.50,
        "holdout_2025_accessed": False,
        "calendar_2024_outcome_accessed_by_this_runner": False,
        "year_2026_accessed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "main_merge_authorized": False,
        "no_post_outcome_rescue": True,
    }

    closeout = out_dir / "OPTIONS_ETH_SKEW_SHOCK_001_STAGE_A_CLOSEOUT_V0.1.json"
    closeout.write_text(json.dumps(sanitize(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with (out_dir / "OPTIONS_ETH_SKEW_SHOCK_001_STAGE_A_LEDGER_V0.1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "signal_date",
                "skew",
                "previous_skew",
                "shock",
                "position",
                "forward_log_return",
                "aligned_unscaled_gross_bps",
                "rv20",
                "weight",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r["signal_date"].isoformat(),
                    r["skew"],
                    r["previous_skew"],
                    r["shock"],
                    r["position"],
                    r["forward_log_return"],
                    r["aligned_unscaled_gross_bps"],
                    r["rv20"],
                    r["weight"],
                ]
            )

    # Remove large scratch DB from uploaded evidence.
    try:
        (scratch / "trade_ids.sqlite").unlink()
        scratch.rmdir()
    except OSError:
        pass

    print(json.dumps(sanitize({
        "classification": classification,
        "base_10bps": base,
        "stress_20bps": stress,
        "nonnegative_years": nonnegative_years,
        "gates": gates,
        "holdout_2025_accessed": False,
        "calendar_2024_outcome_accessed_by_this_runner": False,
        "year_2026_accessed": False,
    }), indent=2, sort_keys=True))

    return 0 if survives else 3


if __name__ == "__main__":
    raise SystemExit(main())
