import csv
import hashlib
import io
import json
import math
import random
import statistics
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTO = HERE / "FROZEN_PROTOCOL_V01.json"
SOURCE = HERE / "source_evidence" / "QBC_SOURCE_GATE_V01.json"
OUTDIR = HERE / "discovery_evidence"
OUT = OUTDIR / "QBC_DISCOVERY_RESULT_V02.json"
DV = "https://data.binance.vision"
UA = {"User-Agent": "Mozilla/5.0 QBC-BINANCE-USDM-7D-001-DISCOVERY/1.0"}
DISCOVERY_YEARS = {2021, 2022, 2023}

GUARDS = {
    "mode": "DISCOVERY_2021_2023_ONLY",
    "year_2024_price_fields_opened": False,
    "year_2025_market_data_requested": False,
    "year_2026_market_data_requested": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
}

class SourceBlocked(RuntimeError):
    pass

class DataFailure(RuntimeError):
    pass


def get(url, attempts=5):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                break
        except Exception as e:
            last = e
        time.sleep(min(8.0, 0.5 * (2 ** i)))
    raise SourceBlocked(f"GET_FAILED:{url}:{type(last).__name__}:{last}")


def iso_parse(x):
    return datetime.fromisoformat(x.replace("Z", "+00:00"))


def ts_sec(v):
    n = int(v)
    if n > 10**14:
        return int(n / 1_000_000)
    if n > 10**11:
        return int(n / 1000)
    return int(n)


def load_archive(path, expected_sha, allowed_year):
    if allowed_year == 2024:
        GUARDS["year_2024_price_fields_opened"] = True
        raise RuntimeError("PROTECTED_2024_PRICE_ACCESS_ATTEMPT")
    if allowed_year == 2025:
        GUARDS["year_2025_market_data_requested"] = True
        raise RuntimeError("PROTECTED_2025_ACCESS_ATTEMPT")
    if allowed_year == 2026:
        GUARDS["year_2026_market_data_requested"] = True
        raise RuntimeError("PROTECTED_2026_ACCESS_ATTEMPT")
    if allowed_year not in DISCOVERY_YEARS:
        raise RuntimeError("NON_DISCOVERY_PRICE_ACCESS_ATTEMPT")
    raw = get(f"{DV}/{path}")
    actual = hashlib.sha256(raw).hexdigest().lower()
    if actual != expected_sha.lower():
        raise DataFailure(f"SOURCE_SHA_MISMATCH:{path}")
    bars = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as zz:
        bad = zz.testzip()
        if bad is not None:
            raise DataFailure(f"ZIP_CRC_FAILURE:{path}:{bad}")
        names = [n for n in zz.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise DataFailure(f"ZIP_MEMBER_COUNT:{path}:{len(names)}")
        with zz.open(names[0]) as f:
            wrapper = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace", newline="")
            for row in csv.reader(wrapper):
                if not row:
                    continue
                first = str(row[0]).strip()
                if first.lower() in {"open_time", "opentime"}:
                    continue
                if len(row) < 5:
                    raise DataFailure(f"ROW_TOO_SHORT:{path}")
                t = ts_sec(first)
                o = float(row[1])
                c = float(row[4])
                if not (math.isfinite(o) and math.isfinite(c) and o > 0 and c > 0):
                    raise DataFailure(f"BAD_PRICE:{path}:{first}")
                bars[t] = (o, c)
    return bars


def require_contiguous(bars, start_ts, end_ts, label):
    # inclusive minute-open timestamps from start through end
    missing = []
    t = start_ts
    while t <= end_ts:
        if t not in bars:
            missing.append(t)
            if len(missing) >= 5:
                break
        t += 60
    if missing:
        raise DataFailure(f"MISSING_1M_BARS:{label}:{missing[:5]}")


def pf(vals):
    gp = sum(x for x in vals if x > 0)
    gl = -sum(x for x in vals if x < 0)
    if gl == 0:
        return None if gp == 0 else float("inf")
    return gp / gl


def metrics(trades, key="base_net_pair_return"):
    vals = [float(t[key]) for t in trades]
    return {
        "n": len(vals),
        "mean": statistics.fmean(vals) if vals else None,
        "median": statistics.median(vals) if vals else None,
        "profit_factor": pf(vals) if vals else None,
        "sum": sum(vals),
        "positive_fraction": (sum(x > 0 for x in vals) / len(vals)) if vals else None,
    }


def bootstrap_mean(trades):
    vals = [float(t["base_net_pair_return"]) for t in trades]
    rng = random.Random(20260916)
    means = []
    n = len(vals)
    for _ in range(10000):
        means.append(sum(vals[rng.randrange(n)] for __ in range(n)) / n)
    means.sort()
    lo = means[int(0.025 * (len(means) - 1))]
    hi = means[int(0.975 * (len(means) - 1))]
    return {"resamples": 10000, "seed": 20260916, "lower_95": lo, "upper_95": hi}


def concentration(trades):
    pos = [max(0.0, float(t["base_net_pair_return"])) for t in trades]
    total = sum(pos)
    if total <= 0:
        return 1.0
    return max(pos) / total


def loo_min_mean(trades):
    vals = [float(t["base_net_pair_return"]) for t in trades]
    if len(vals) <= 1:
        return None
    total = sum(vals)
    n = len(vals)
    return min((total - x) / (n - 1) for x in vals)


def simulate_route(route, spot, fut, p):
    strategy = p["strategy"]
    snapshot_dt = iso_parse(route["snapshot_utc"])
    entry_dt = iso_parse(route["entry_utc"])
    forced_dt = iso_parse(route["forced_exit_utc"])
    snapshot_ts = int(snapshot_dt.timestamp())
    entry_ts = int(entry_dt.timestamp())
    forced_ts = int(forced_dt.timestamp())

    # V0.2 implementation correction:
    # The frozen protocol requires execution-path integrity only for a selected trade.
    # First adjudicate the frozen signal from the required snapshot bar. Do not
    # require post-entry path continuity for a contract that never enters.
    if snapshot_ts not in spot or snapshot_ts not in fut:
        raise DataFailure(f"MISSING_SNAPSHOT_BAR:{route['contract']}:{snapshot_ts}")

    spot_snapshot = spot[snapshot_ts][1]
    fut_snapshot = fut[snapshot_ts][1]
    signal_basis = fut_snapshot / spot_snapshot - 1.0
    record = {
        "contract": route["contract"],
        "asset": route["asset"],
        "expiry_utc": route["expiry_utc"],
        "snapshot_utc": route["snapshot_utc"],
        "entry_utc": route["entry_utc"],
        "forced_exit_utc": route["forced_exit_utc"],
        "signal_basis": signal_basis,
        "minimum_entry_basis": strategy["minimum_entry_basis_fraction"],
    }
    if signal_basis < float(strategy["minimum_entry_basis_fraction"]):
        record["trade_selected"] = False
        record["selection_reason"] = "SIGNAL_BASIS_BELOW_FROZEN_THRESHOLD"
        return record, None

    if entry_ts not in spot or entry_ts not in fut:
        raise DataFailure(f"MISSING_ENTRY_OPEN:{route['contract']}:{entry_ts}")

    spot_entry = spot[entry_ts][0]
    fut_entry = fut[entry_ts][0]
    if spot_entry <= 0 or fut_entry <= 0:
        raise DataFailure(f"BAD_ENTRY_PRICE:{route['contract']}")

    stop_basis = signal_basis + float(strategy["basis_stop_additive_fraction"])
    target_basis = float(strategy["target_basis_fraction"])
    exit_ts = None
    exit_reason = None

    # A predicate is evaluated only after a minute bar is complete, then executed at next minute open.
    t = entry_ts
    while t < forced_ts:
        # Only the realized execution path of an actually selected trade must
        # be continuous. Missing bars after a completed exit are irrelevant.
        if t not in spot or t not in fut:
            raise DataFailure(f"MISSING_EXECUTION_PATH_BAR:{route['contract']}:{t}")
        spot_close = spot[t][1]
        fut_close = fut[t][1]
        close_basis = fut_close / spot_close - 1.0
        next_ts = t + 60
        stop_hit = close_basis >= stop_basis
        target_hit = close_basis <= target_basis
        if stop_hit or target_hit:
            if next_ts > forced_ts:
                break
            exit_ts = next_ts
            if stop_hit:
                exit_reason = "BASIS_STOP_NEXT_OPEN"
            else:
                exit_reason = "BASIS_TARGET_NEXT_OPEN"
            break
        t += 60

    if exit_ts is None:
        exit_ts = forced_ts
        exit_reason = "FORCED_EXIT_T_MINUS_15M"

    if exit_ts not in spot or exit_ts not in fut:
        raise DataFailure(f"MISSING_EXIT_OPEN:{route['contract']}:{exit_ts}")
    spot_exit = spot[exit_ts][0]
    fut_exit = fut[exit_ts][0]
    gross_spot = spot_exit / spot_entry - 1.0
    gross_future_short = (fut_entry - fut_exit) / fut_entry
    gross_pair = gross_spot + gross_future_short
    base_net = gross_pair - float(strategy["base_pair_round_trip_cost_fraction_of_single_leg_notional"])
    stress_net = gross_pair - float(strategy["stress_pair_round_trip_cost_fraction_of_single_leg_notional"])

    record.update({
        "trade_selected": True,
        "spot_entry": spot_entry,
        "future_entry": fut_entry,
        "spot_exit": spot_exit,
        "future_exit": fut_exit,
        "exit_utc": datetime.fromtimestamp(exit_ts, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "exit_reason": exit_reason,
        "stop_basis": stop_basis,
        "target_basis": target_basis,
        "gross_spot_return": gross_spot,
        "gross_future_short_return": gross_future_short,
        "gross_pair_return": gross_pair,
        "base_net_pair_return": base_net,
        "stress_net_pair_return": stress_net,
        "base_fully_collateralized_capital_return": base_net / 2.0,
        "stress_fully_collateralized_capital_return": stress_net / 2.0,
    })
    return record, record


def main():
    p = json.loads(PROTO.read_text(encoding="utf-8"))
    src = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_PRE_SOURCE_OUTCOME_BLIND"
    assert src["receipt"]["classification"] == "SOURCE_DATA_PASS"
    assert p["source"]["discovery_expiry_years"] == [2021, 2022, 2023]
    assert p["source"]["independent_validation_expiry_year"] == 2024
    assert p["strategy"]["minimum_entry_basis_fraction"] == 0.007
    assert p["strategy"]["target_basis_fraction"] == 0.001
    assert p["strategy"]["basis_stop_additive_fraction"] == 0.015

    routes = [r for r in src["qualified_routes"] if int(r["expiry_utc"][:4]) in DISCOVERY_YEARS]
    routes.sort(key=lambda x: (x["expiry_utc"], x["asset"]))
    if any(int(r["expiry_utc"][:4]) == 2024 for r in routes):
        raise RuntimeError("PROTECTED_2024_ROUTE_IN_DISCOVERY")

    cache = {}
    source_integrity_failures = []
    route_records = []
    trades = []
    try:
        for r in routes:
            year = int(r["expiry_utc"][:4])
            fp = r["futures_archive"]["path"]
            sp = r["spot_archive"]["path"]
            if fp not in cache:
                cache[fp] = load_archive(fp, r["futures_archive"]["sha256"], year)
            if sp not in cache:
                cache[sp] = load_archive(sp, r["spot_archive"]["sha256"], year)
            rec, trade = simulate_route(r, cache[sp], cache[fp], p)
            route_records.append(rec)
            if trade is not None:
                trades.append(trade)
    except SourceBlocked as e:
        doc = {"classification": "SOURCE_ACCESS_BLOCKED", "reason": str(e), "guards": GUARDS}
        write(doc)
        return
    except DataFailure as e:
        source_integrity_failures.append(str(e))
    except Exception as e:
        doc = {"classification": "TECHNICAL_FAILURE", "reason": f"{type(e).__name__}:{e}", "guards": GUARDS}
        write(doc)
        return

    if source_integrity_failures:
        doc = {
            "classification": "DATA_FAILURE",
            "reason": source_integrity_failures[0],
            "source_integrity_failures": source_integrity_failures,
            "guards": GUARDS,
            "route_records": route_records,
        }
        write(doc)
        return

    base = metrics(trades, "base_net_pair_return")
    stress = metrics(trades, "stress_net_pair_return")
    by_asset = {a: metrics([t for t in trades if t["asset"] == a], "base_net_pair_return") for a in ("BTC", "ETH")}
    by_year = {}
    for y in (2021, 2022, 2023):
        yt = [t for t in trades if t["expiry_utc"].startswith(str(y))]
        by_year[str(y)] = metrics(yt, "base_net_pair_return")
    traded_years = sum(by_year[str(y)]["n"] > 0 for y in (2021, 2022, 2023))
    positive_years = sum((by_year[str(y)]["mean"] is not None and by_year[str(y)]["mean"] > 0) for y in (2021, 2022, 2023))
    boot = bootstrap_mean(trades) if trades else None
    conc = concentration(trades) if trades else None
    loo = loo_min_mean(trades) if trades else None

    d = p["discovery"]
    insufficient = (
        base["n"] < int(d["sample_floor_resolved_trades"]) or
        by_asset["BTC"]["n"] < int(d["asset_trade_floor"]) or
        by_asset["ETH"]["n"] < int(d["asset_trade_floor"]) or
        traded_years < int(d["traded_years_min"])
    )

    gates = None
    if insufficient:
        classification = "INSUFFICIENT_EVALUABLE_SAMPLE"
        reason = "one or more prospectively frozen trade-count/breadth floors failed"
    else:
        gates = {
            "resolved_trades_gte": base["n"] >= 12,
            "btc_trades_gte": by_asset["BTC"]["n"] >= 4,
            "eth_trades_gte": by_asset["ETH"]["n"] >= 4,
            "traded_years_gte": traded_years >= 2,
            "positive_years_gte": positive_years >= 2,
            "base_mean_net_pair_return_gt": base["mean"] > 0,
            "base_profit_factor_gt": base["profit_factor"] is not None and base["profit_factor"] > 1.25,
            "bootstrap_95_lower_mean_net_pair_return_gt": boot["lower_95"] > 0,
            "stress_mean_net_pair_return_gt": stress["mean"] > 0,
            "stress_profit_factor_gt": stress["profit_factor"] is not None and stress["profit_factor"] > 1.0,
            "btc_mean_net_pair_return_gt": by_asset["BTC"]["mean"] > 0,
            "eth_mean_net_pair_return_gt": by_asset["ETH"]["mean"] > 0,
            "max_single_contract_share_positive_net_pnl_lte": conc <= 0.30,
            "minimum_leave_one_contract_out_mean_net_pair_return_gt": loo > 0,
            "execution_unresolved_eq": True,
            "source_integrity_failures_eq": True,
        }
        classification = "DISCOVERY_SURVIVES" if all(gates.values()) else "DISCOVERY_NO_EDGE"
        reason = "all frozen Discovery gates passed" if classification == "DISCOVERY_SURVIVES" else "one or more frozen Discovery gates failed"

    no_trade = len(route_records) - len(trades)
    doc = {
        "lab_id": p["lab_id"],
        "mve_id": p["mve_id"],
        "classification": classification,
        "reason": reason,
        "discovery_expiry_years": [2021, 2022, 2023],
        "qualified_source_routes_in_discovery": len(routes),
        "selected_trades": len(trades),
        "no_trade_contracts_below_basis_threshold": no_trade,
        "base_metrics": base,
        "stress_metrics": stress,
        "by_asset": by_asset,
        "by_year": by_year,
        "traded_years": traded_years,
        "positive_years": positive_years,
        "bootstrap": boot,
        "max_single_contract_share_positive_net_pnl": conc,
        "minimum_leave_one_contract_out_mean_net_pair_return": loo,
        "gates": gates,
        "guards": GUARDS,
        "route_records": route_records,
        "next_action": "Open 2024 independent validation only if DISCOVERY_SURVIVES. Otherwise close exact tested implementation without rescue. 2025/2026 remain locked."
    }
    write(doc)


def write(doc):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    summary = {k: v for k, v in doc.items() if k not in {"route_records"}}
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))

if __name__ == "__main__":
    main()
