#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import random
import statistics
import zipfile
from pathlib import Path
from typing import Any

LAB_ID = "NFP-SURPRISE-V2-REPLICATION-01"
VERSION = "2025-OOS-V0.1"
AUTHORITY_COMMIT = "0bbd3ae2c6e406b1f86aaf1dde19f78c7bf3dc7d"
BASE_COST_BPS = 10.0
BOOTSTRAP_SEED = 20260917
BOOTSTRAP_REPS = 10_000
SIGNALS = {
    "2025-01-10": "HOTTER",
    "2025-02-07": "HOTTER",
    "2025-03-07": "COOLER",
    "2025-06-06": "HOTTER",
    "2025-07-03": "HOTTER",
    "2025-08-01": "COOLER",
    "2025-09-05": "COOLER",
    "2025-11-20": "COOLER",
    "2025-12-16": "COOLER",
}
SYMBOLS = ("BTCUSDT", "ETHUSDT")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def to_ms(raw: int) -> int:
    if 1_000_000_000_000 <= raw < 10_000_000_000_000:
        return raw
    if 1_000_000_000_000_000 <= raw < 10_000_000_000_000_000:
        return raw // 1000
    raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: unexpected timestamp magnitude {raw}")


def load_manifest(root: Path) -> dict[str, Any]:
    p = root / "source_manifest_2025.json"
    if not p.exists():
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: source manifest missing")
    m = json.loads(p.read_text(encoding="utf-8"))
    if m.get("status") != "SOURCE_AUDIT_PASS":
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: source gate not PASS")
    if m.get("authority_commit") != AUTHORITY_COMMIT:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: authority mismatch")
    if m.get("year_2026_accessed") is not False or m.get("outcomes_computed") is not False:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: source firewall violation")
    if sorted(m.get("directional_dates", [])) != sorted(SIGNALS):
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: directional corpus mismatch")
    if sorted(m.get("symbols", [])) != sorted(SYMBOLS):
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: symbol family mismatch")
    return m


def read_required_opens(source_root: Path, rec: dict[str, Any]) -> tuple[float, float]:
    p = source_root / rec["file"]
    if not p.exists() or sha256_file(p) != rec.get("sha256"):
        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: archive integrity failure {rec.get('file')}")
    entry_ms = int(rec["entry_0831_ny_ms"])
    exit_ms = int(rec["exit_0845_ny_ms"])
    if dt.datetime.fromtimestamp(entry_ms / 1000, tz=dt.timezone.utc).year >= 2026:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: protected 2026 entry")
    if dt.datetime.fromtimestamp(exit_ms / 1000, tz=dt.timezone.utc).year >= 2026:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: protected 2026 exit")
    found: dict[int, float] = {}
    with zipfile.ZipFile(p) as zf:
        members = [n for n in zf.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise RuntimeError("SOURCE_OR_DATA_BLOCKED: zip member drift")
        with zf.open(members[0]) as fh:
            for row in csv.reader(io.TextIOWrapper(fh, encoding="utf-8", newline="")):
                if not row:
                    continue
                ms = to_ms(int(row[0]))
                if ms not in (entry_ms, exit_ms):
                    continue
                op = float(row[1])
                if not math.isfinite(op) or op <= 0:
                    raise RuntimeError("SOURCE_OR_DATA_BLOCKED: invalid open price")
                if ms in found:
                    raise RuntimeError("SOURCE_OR_DATA_BLOCKED: duplicate required bar")
                found[ms] = op
    if set(found) != {entry_ms, exit_ms}:
        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: required outcome bars missing {rec['symbol']} {rec['date']}")
    return found[entry_ms], found[exit_ms]


def max_drawdown(net_bps: list[float]) -> float:
    wealth = peak = 1.0
    mdd = 0.0
    for bps in net_bps:
        wealth *= math.exp(bps / 10000.0)
        peak = max(peak, wealth)
        mdd = min(mdd, wealth / peak - 1.0)
    return mdd


def metrics(rows: list[dict[str, Any]], symbol: str) -> dict[str, Any]:
    rr = [r for r in rows if r["symbol"] == symbol]
    gross = [float(r["aligned_gross_bps"]) for r in rr]
    net = [float(r["net10_bps"]) for r in rr]
    pos = sum(x for x in net if x > 0)
    neg = -sum(x for x in net if x < 0)
    pf = pos / neg if neg > 0 else (float("inf") if pos > 0 else 0.0)
    return {
        "n": len(rr),
        "gross_mean_bps": statistics.mean(gross),
        "gross_median_bps": statistics.median(gross),
        "net10_mean_bps": statistics.mean(net),
        "net10_median_bps": statistics.median(net),
        "positive_event_fraction_net10": sum(1 for x in net if x > 0) / len(net),
        "profit_factor_net10": pf,
        "cumulative_net_return": math.exp(sum(x / 10000.0 for x in net)) - 1.0,
        "max_drawdown": max_drawdown(net),
    }


def bootstrap_family(values: list[float]) -> dict[str, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(values)
    means = []
    for _ in range(BOOTSTRAP_REPS):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    def q(p: float) -> float:
        idx = (len(means) - 1) * p
        lo = int(math.floor(idx)); hi = int(math.ceil(idx))
        if lo == hi:
            return means[lo]
        w = idx - lo
        return means[lo] * (1 - w) + means[hi] * w
    return {"seed": BOOTSTRAP_SEED, "reps": BOOTSTRAP_REPS, "p2_5": q(0.025), "p50": q(0.50), "p97_5": q(0.975)}


def sanitize(x: Any) -> Any:
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: sanitize(v) for k, v in x.items()}
    if isinstance(x, list):
        return [sanitize(v) for v in x]
    return x


def run(source_root: Path, output: Path) -> int:
    manifest = load_manifest(source_root)
    by_key = {(r["symbol"], r["date"]): r for r in manifest.get("records", [])}
    rows: list[dict[str, Any]] = []
    for date_s, label in SIGNALS.items():
        direction = -1 if label == "HOTTER" else 1
        for symbol in SYMBOLS:
            rec = by_key.get((symbol, date_s))
            if rec is None:
                raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: missing manifest record {symbol} {date_s}")
            entry, exit_ = read_required_opens(source_root, rec)
            raw_log_return = math.log(exit_ / entry)
            aligned_gross_bps = direction * raw_log_return * 10000.0
            rows.append({
                "date": date_s,
                "label": label,
                "symbol": symbol,
                "entry_open": entry,
                "exit_open": exit_,
                "raw_log_return": raw_log_return,
                "aligned_gross_bps": aligned_gross_bps,
                "net10_bps": aligned_gross_bps - BASE_COST_BPS,
            })

    if len(rows) != 18:
        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: expected 18 asset-event rows, got {len(rows)}")

    asset = {s: metrics(rows, s) for s in SYMBOLS}
    family_events = []
    for date_s in SIGNALS:
        rr = [r for r in rows if r["date"] == date_s]
        if len(rr) != 2:
            raise RuntimeError("SOURCE_OR_DATA_BLOCKED: family event pairing failure")
        gross = statistics.mean([r["aligned_gross_bps"] for r in rr])
        net = statistics.mean([r["net10_bps"] for r in rr])
        family_events.append({"date": date_s, "label": SIGNALS[date_s], "family_gross_bps": gross, "family_net10_bps": net})

    family_net = [x["family_net10_bps"] for x in family_events]
    family_gross = [x["family_gross_bps"] for x in family_events]
    positive_family_count = sum(1 for x in family_net if x > 0)
    pos_gross = [max(0.0, x) for x in family_gross]
    total_pos_gross = sum(pos_gross)
    concentration = max(pos_gross) / total_pos_gross if total_pos_gross > 0 else 1.0
    loo_means = []
    for i in range(len(family_net)):
        vals = family_net[:i] + family_net[i+1:]
        loo_means.append({"omitted_date": family_events[i]["date"], "family_net10_mean_bps": statistics.mean(vals)})
    loo_min = min(x["family_net10_mean_bps"] for x in loo_means)
    bootstrap = bootstrap_family(family_net)

    gates = {
        "A_provenance_timestamp_leakage_pass": True,
        "B_no_event_deletion_or_asset_selection": True,
        "C_btc_net10_mean_positive": asset["BTCUSDT"]["net10_mean_bps"] > 0,
        "D_eth_net10_mean_positive": asset["ETHUSDT"]["net10_mean_bps"] > 0,
        "E_btc_pf_net10_ge_1": asset["BTCUSDT"]["profit_factor_net10"] >= 1.0,
        "F_eth_pf_net10_ge_1": asset["ETHUSDT"]["profit_factor_net10"] >= 1.0,
        "G_at_least_5_of_9_family_net10_positive": positive_family_count >= 5,
        "H_single_event_positive_family_gross_share_le_50pct": concentration <= 0.50,
        "I_2026_not_accessed": True,
    }
    all_pass = all(gates.values())
    materially_failed = (
        asset["BTCUSDT"]["net10_mean_bps"] <= 0
        or asset["ETHUSDT"]["net10_mean_bps"] <= 0
        or asset["BTCUSDT"]["profit_factor_net10"] < 1.0
        or asset["ETHUSDT"]["profit_factor_net10"] < 1.0
    )
    if all_pass:
        classification = "TIER2_PROMOTED_CANDIDATE__QUASE_DIAMANTE"
        rc = 0
    elif materially_failed:
        classification = "TIER4_REJECTED"
        rc = 3
    else:
        classification = "TIER3_POSITIVE_OR_MIXED"
        rc = 4

    result = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "authority_commit": AUTHORITY_COMMIT,
        "classification": classification,
        "directional_events": len(SIGNALS),
        "neutral_events_excluded_by_frozen_formula": ["2025-04-04", "2025-05-02"],
        "asset_metrics": asset,
        "family": {
            "mean_net10_bps": statistics.mean(family_net),
            "median_net10_bps": statistics.median(family_net),
            "positive_family_events": positive_family_count,
            "positive_family_fraction": positive_family_count / len(family_net),
            "largest_single_event_share_positive_gross_pnl": concentration,
            "leave_one_event_out": loo_means,
            "leave_one_event_out_min_net10_mean_bps": loo_min,
            "bootstrap_mean_net10_bps": bootstrap,
            "events": family_events,
        },
        "gates": gates,
        "year_2026_accessed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "tier1_automatic": False,
        "notes": [
            "Historical V1 parent NO_EDGE_STOP remains immutable.",
            "This 2025 result adjudicates only the exact frozen V2 replication path under V3.",
            "No post-outcome rescue, source substitution, event deletion, asset selection, window change or cost change is authorized.",
        ],
    }

    output.mkdir(parents=True, exist_ok=True)
    (output / "NFP_SURPRISE_V2_2025_OOS_CLOSEOUT_V01.json").write_text(json.dumps(sanitize(result), indent=2, sort_keys=True), encoding="utf-8")
    with (output / "NFP_SURPRISE_V2_2025_OOS_LEDGER_V01.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "label", "symbol", "entry_open", "exit_open", "raw_log_return", "aligned_gross_bps", "net10_bps"])
        for r in rows:
            w.writerow([r[k] for k in ("date", "label", "symbol", "entry_open", "exit_open", "raw_log_return", "aligned_gross_bps", "net10_bps")])

    print(classification)
    print(json.dumps(sanitize({"asset_metrics": asset, "family": result["family"], "gates": gates}), sort_keys=True))
    print("2026_LOCKED=true / LIVE_TRADING=false / EXCHANGE_MUTATION=false")
    return rc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    raise SystemExit(run(Path(args.source_root).resolve(), Path(args.output).resolve()))
