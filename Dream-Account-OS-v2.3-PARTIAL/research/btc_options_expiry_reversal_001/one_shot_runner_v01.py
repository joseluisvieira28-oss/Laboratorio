import calendar
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
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTO = HERE / "FROZEN_PROTOCOL_V01.json"
OUTDIR = HERE / "evidence"
OUT = OUTDIR / "BOER_FINAL_RESULT_V01.json"
TMP = Path("/tmp/boer_binance")
DV = "https://data.binance.vision"
ROOT = "data/futures/um/monthly/klines/BTCUSDT/1m"
UA = {"User-Agent": "Mozilla/5.0 BOER-BINANCE-PERP-4H2H-001/1.0"}
ALLOWED_YEARS = {2021, 2022, 2023, 2024}
PROTECTED_YEARS = {2025, 2026}

GUARDS = {
    "mode": "SOURCE_GATE_THEN_DISCOVERY_THEN_CONDITIONAL_VALIDATION",
    "source_gate_market_price_values_parsed": False,
    "discovery_price_years_opened": [],
    "year_2024_price_fields_opened": False,
    "year_2025_market_data_requested": False,
    "year_2026_market_data_requested": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
    "alerts_or_webhooks": False,
    "merge_to_main": False,
    "render_deployment": False,
}

class SourceBlocked(RuntimeError):
    pass

class DataFailure(RuntimeError):
    pass


def get(url, attempts=5, allow_404=False):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code == 404:
                return None
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                break
        except Exception as e:
            last = e
        time.sleep(min(8.0, 0.5 * (2 ** i)))
    raise SourceBlocked(f"GET_FAILED:{url}:{type(last).__name__}:{last}")


def last_friday(year, month):
    last_day = calendar.monthrange(year, month)[1]
    d = datetime(year, month, last_day, 8, 0, tzinfo=timezone.utc)
    while d.weekday() != calendar.FRIDAY:
        d = d.replace(day=d.day - 1)
    return d


def normalize_ts(raw):
    v = int(str(raw).strip())
    if v > 10**14:
        return v // 1_000_000
    if v > 10**11:
        return v // 1000
    return v


def archive_path(year, month):
    if year in PROTECTED_YEARS:
        if year == 2025:
            GUARDS["year_2025_market_data_requested"] = True
        if year == 2026:
            GUARDS["year_2026_market_data_requested"] = True
        raise RuntimeError(f"PROTECTED_YEAR_PATH_ATTEMPT:{year}")
    if year not in ALLOWED_YEARS:
        raise RuntimeError(f"UNAUTHORIZED_YEAR_PATH_ATTEMPT:{year}")
    ym = f"{year:04d}-{month:02d}"
    return f"{ROOT}/BTCUSDT-1m-{ym}.zip"


def parse_checksum(raw, expected_name):
    parts = raw.decode("utf-8", "replace").strip().split()
    if not parts:
        raise DataFailure(f"EMPTY_CHECKSUM:{expected_name}")
    dg = parts[0].lower()
    if len(dg) != 64 or any(c not in "0123456789abcdef" for c in dg):
        raise DataFailure(f"BAD_CHECKSUM:{expected_name}")
    if len(parts) >= 2 and parts[-1].lstrip("*") != expected_name:
        raise DataFailure(f"CHECKSUM_FILENAME_MISMATCH:{expected_name}")
    return dg


def event_times(expiry):
    y, m, d = expiry.year, expiry.month, expiry.day
    return {
        "pre_start": int(datetime(y, m, d, 4, 0, tzinfo=timezone.utc).timestamp()),
        "pre_last": int(datetime(y, m, d, 7, 59, tzinfo=timezone.utc).timestamp()),
        "expiry": int(datetime(y, m, d, 8, 0, tzinfo=timezone.utc).timestamp()),
        "entry": int(datetime(y, m, d, 8, 5, tzinfo=timezone.utc).timestamp()),
        "exit": int(datetime(y, m, d, 10, 5, tzinfo=timezone.utc).timestamp()),
    }


def source_gate(p):
    TMP.mkdir(parents=True, exist_ok=True)
    events = []
    failures = []
    archives = []
    for year in p["source"]["allowed_market_years"]:
        for month in range(1, 13):
            expiry = last_friday(year, month)
            times = event_times(expiry)
            path = archive_path(year, month)
            name = path.rsplit("/", 1)[-1]
            checksum_raw = get(f"{DV}/{path}.CHECKSUM", allow_404=True)
            if checksum_raw is None:
                failures.append(f"MISSING_CHECKSUM:{path}")
                continue
            official = parse_checksum(checksum_raw, name)
            zb = get(f"{DV}/{path}")
            actual = hashlib.sha256(zb).hexdigest().lower()
            if actual != official:
                raise DataFailure(f"SHA256_MISMATCH:{path}")
            local = TMP / name
            local.write_bytes(zb)
            wanted = {times["pre_start"], times["pre_last"], times["entry"], times["exit"]}
            found = set()
            first = None
            last = None
            rows = 0
            with zipfile.ZipFile(io.BytesIO(zb)) as zz:
                bad = zz.testzip()
                if bad is not None:
                    raise DataFailure(f"ZIP_CRC_FAILURE:{path}:{bad}")
                members = [n for n in zz.namelist() if not n.endswith("/")]
                if len(members) != 1:
                    raise DataFailure(f"ZIP_MEMBER_COUNT:{path}:{len(members)}")
                with zz.open(members[0]) as f:
                    wrapper = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace", newline="")
                    for row in csv.reader(wrapper):
                        if not row:
                            continue
                        s = str(row[0]).strip()
                        if s.lower() in {"open_time", "opentime"}:
                            continue
                        if not s.isdigit():
                            raise DataFailure(f"FIRST_FIELD_NOT_TIMESTAMP:{path}")
                        ts = normalize_ts(s)
                        first = ts if first is None else first
                        last = ts
                        rows += 1
                        if ts in wanted:
                            found.add(ts)
            missing = sorted(wanted - found)
            if missing:
                failures.append(f"MISSING_REQUIRED_EVENT_BARS:{year}-{month:02d}:{missing}")
                continue
            archives.append({
                "year": year,
                "month": month,
                "path": path,
                "sha256": actual,
                "rows": rows,
                "first_open_time_utc": datetime.fromtimestamp(first, timezone.utc).isoformat().replace("+00:00", "Z"),
                "last_open_time_utc": datetime.fromtimestamp(last, timezone.utc).isoformat().replace("+00:00", "Z"),
            })
            events.append({
                "year": year,
                "month": month,
                "expiry_utc": expiry.isoformat().replace("+00:00", "Z"),
                "archive_path": path,
                "archive_sha256": actual,
                "times_epoch_s": times,
            })
    yc = Counter(e["year"] for e in events)
    expected = int(p["source_gate"]["expected_events"])
    if failures:
        cls = "DATA_FAILURE"
        reason = failures[0]
    elif len(events) != expected:
        cls = "DATA_FAILURE"
        reason = f"EXPECTED_{expected}_EVENTS_GOT_{len(events)}"
    elif any(yc.get(y, 0) != int(p["source_gate"]["required_events_per_year"]) for y in ALLOWED_YEARS):
        cls = "DATA_FAILURE"
        reason = f"YEAR_COUNTS:{dict(sorted(yc.items()))}"
    else:
        cls = "SOURCE_DATA_PASS"
        reason = "48/48 official monthly archives checksum-verified and all frozen event timestamps present"
    receipt = {
        "classification": cls,
        "reason": reason,
        "qualified_events": len(events),
        "qualified_year_counts": dict(sorted(yc.items())),
        "archive_count": len(archives),
        "failures": failures,
        "guards": dict(GUARDS),
    }
    return receipt, events, archives


def read_prices(event):
    year = int(event["year"])
    if year == 2024:
        GUARDS["year_2024_price_fields_opened"] = True
    if year not in GUARDS["discovery_price_years_opened"]:
        GUARDS["discovery_price_years_opened"].append(year)
        GUARDS["discovery_price_years_opened"].sort()
    path = event["archive_path"]
    name = path.rsplit("/", 1)[-1]
    local = TMP / name
    if not local.exists():
        raise DataFailure(f"LOCAL_ARCHIVE_MISSING:{name}")
    wanted = event["times_epoch_s"]
    out = {}
    with zipfile.ZipFile(local) as zz:
        members = [n for n in zz.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise DataFailure(f"ZIP_MEMBER_COUNT_PRICE_PARSE:{path}:{len(members)}")
        with zz.open(members[0]) as f:
            wrapper = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace", newline="")
            for row in csv.reader(wrapper):
                if not row:
                    continue
                s = str(row[0]).strip()
                if s.lower() in {"open_time", "opentime"}:
                    continue
                if not s.isdigit():
                    continue
                ts = normalize_ts(s)
                if ts == wanted["pre_start"]:
                    out["pre_start_open"] = float(row[1])
                elif ts == wanted["pre_last"]:
                    out["pre_last_close"] = float(row[4])
                elif ts == wanted["entry"]:
                    out["entry_open"] = float(row[1])
                elif ts == wanted["exit"]:
                    out["exit_open"] = float(row[1])
                if len(out) == 4:
                    break
    if len(out) != 4:
        raise DataFailure(f"PRICE_FIELDS_MISSING:{year}-{event['month']:02d}:{sorted(out)}")
    for k, v in out.items():
        if not math.isfinite(v) or v <= 0:
            raise DataFailure(f"NONPOSITIVE_OR_NONFINITE_PRICE:{k}:{v}")
    return out


def build_trade(event, p):
    px = read_prices(event)
    pre_ret = px["pre_last_close"] / px["pre_start_open"] - 1.0
    if pre_ret == 0.0:
        return {
            "year": event["year"],
            "month": event["month"],
            "expiry_utc": event["expiry_utc"],
            "resolved": False,
            "reason": "EXACT_ZERO_PRE_RETURN",
        }
    direction = -1 if pre_ret > 0 else 1
    post_ret = px["exit_open"] / px["entry_open"] - 1.0
    gross = direction * post_ret
    base = gross - float(p["strategy"]["base_round_trip_cost_fraction"])
    stress = gross - float(p["strategy"]["stress_round_trip_cost_fraction"])
    return {
        "year": event["year"],
        "month": event["month"],
        "expiry_utc": event["expiry_utc"],
        "resolved": True,
        "pre_return": pre_ret,
        "direction": "LONG" if direction == 1 else "SHORT",
        "entry_open": px["entry_open"],
        "exit_open": px["exit_open"],
        "post_market_return": post_ret,
        "gross_trade_return": gross,
        "base_net_return": base,
        "stress_net_return": stress,
        "base_win": base > 0,
        "stress_win": stress > 0,
    }


def bootstrap_ci(values, reps, seed):
    if not values:
        return [None, None]
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(reps):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[max(0, min(reps - 1, int(math.floor(0.025 * reps))))]
    hi = means[max(0, min(reps - 1, int(math.floor(0.975 * reps)) - 1))]
    return [lo, hi]


def summarize(trades, p, validation=False):
    resolved = [t for t in trades if t.get("resolved")]
    base = [t["base_net_return"] for t in resolved]
    stress = [t["stress_net_return"] for t in resolved]
    longs = sum(t["direction"] == "LONG" for t in resolved)
    shorts = sum(t["direction"] == "SHORT" for t in resolved)
    wins = sum(t["base_win"] for t in resolved)
    stress_wins = sum(t["stress_win"] for t in resolved)
    by_year = defaultdict(list)
    for t in resolved:
        by_year[int(t["year"])].append(t["base_net_return"])
    year_means = {str(y): sum(v) / len(v) for y, v in sorted(by_year.items())}
    positive_years = sum(v > 0 for v in year_means.values())
    s = {
        "scheduled_events": len(trades),
        "resolved_trades": len(resolved),
        "unresolved_trades": len(trades) - len(resolved),
        "long_trades": longs,
        "short_trades": shorts,
        "base_mean_net_return": sum(base) / len(base) if base else None,
        "base_median_net_return": statistics.median(base) if base else None,
        "stress_mean_net_return": sum(stress) / len(stress) if stress else None,
        "base_wins": wins,
        "stress_wins": stress_wins,
        "base_win_rate": wins / len(resolved) if resolved else None,
        "stress_win_rate": stress_wins / len(resolved) if resolved else None,
        "calendar_year_base_mean_net_returns": year_means,
        "positive_calendar_years": positive_years,
    }
    if not validation and base:
        s["base_mean_bootstrap_95pct_ci"] = bootstrap_ci(
            base,
            int(p["discovery"]["bootstrap_repetitions"]),
            int(p["discovery"]["bootstrap_seed"]),
        )
    return s


def discovery_gate(summary, p):
    d = p["discovery"]
    ci = summary.get("base_mean_bootstrap_95pct_ci", [None, None])
    gates = {
        "resolved_trade_floor": summary["resolved_trades"] >= int(d["resolved_trade_floor"]),
        "long_trade_floor": summary["long_trades"] >= int(d["minimum_long_trades"]),
        "short_trade_floor": summary["short_trades"] >= int(d["minimum_short_trades"]),
        "base_mean_net_return_gt_zero": summary["base_mean_net_return"] is not None and summary["base_mean_net_return"] > 0,
        "stress_mean_net_return_gt_zero": summary["stress_mean_net_return"] is not None and summary["stress_mean_net_return"] > 0,
        "base_win_rate_min": summary["base_win_rate"] is not None and summary["base_win_rate"] >= float(d["promotion_gates_all_required"]["base_win_rate_min"]),
        "base_mean_bootstrap_95pct_ci_lower_gt_zero": ci[0] is not None and ci[0] > 0,
        "positive_calendar_years_min": summary["positive_calendar_years"] >= int(d["promotion_gates_all_required"]["positive_calendar_years_min"]),
    }
    return gates, all(gates.values())


def validation_gate(summary, p):
    v = p["independent_validation"]["pass_gates_all_required"]
    gates = {
        "resolved_trades_min": summary["resolved_trades"] >= int(v["resolved_trades_min"]),
        "base_mean_net_return_gt_zero": summary["base_mean_net_return"] is not None and summary["base_mean_net_return"] > 0,
        "stress_mean_net_return_gt_zero": summary["stress_mean_net_return"] is not None and summary["stress_mean_net_return"] > 0,
        "base_wins_min": summary["base_wins"] >= int(v["base_wins_min"]),
    }
    return gates, all(gates.values())


def write(doc):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    compact = {
        "classification": doc.get("classification"),
        "source": doc.get("source_receipt"),
        "discovery_summary": (doc.get("discovery") or {}).get("summary"),
        "discovery_gates": (doc.get("discovery") or {}).get("gates"),
        "validation_summary": (doc.get("validation") or {}).get("summary") if doc.get("validation") else None,
        "validation_gates": (doc.get("validation") or {}).get("gates") if doc.get("validation") else None,
        "guards": doc.get("guards"),
    }
    print(json.dumps(compact, indent=2, sort_keys=True))


def main():
    p = json.loads(PROTO.read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_PRE_SOURCE_OUTCOME_BLIND"
    base_doc = {
        "lab_id": p["lab_id"],
        "mve_id": p["mve_id"],
        "protocol_sha256": hashlib.sha256(PROTO.read_bytes()).hexdigest(),
    }
    try:
        receipt, events, archives = source_gate(p)
    except SourceBlocked as e:
        write({**base_doc, "classification": "SOURCE_ACCESS_BLOCKED", "reason": str(e), "source_receipt": {"classification": "SOURCE_ACCESS_BLOCKED", "reason": str(e)}, "discovery": None, "validation": None, "guards": GUARDS})
        return
    except Exception as e:
        write({**base_doc, "classification": "DATA_FAILURE", "reason": f"{type(e).__name__}:{e}", "source_receipt": {"classification": "DATA_FAILURE", "reason": f"{type(e).__name__}:{e}"}, "discovery": None, "validation": None, "guards": GUARDS})
        return

    if receipt["classification"] != "SOURCE_DATA_PASS":
        write({**base_doc, "classification": receipt["classification"], "reason": receipt["reason"], "source_receipt": receipt, "source_archives": archives, "discovery": None, "validation": None, "guards": GUARDS})
        return

    discovery_events = [e for e in events if int(e["year"]) in set(p["discovery"]["years"])]
    try:
        dtrades = [build_trade(e, p) for e in discovery_events]
    except Exception as e:
        write({**base_doc, "classification": "DATA_FAILURE", "reason": f"DISCOVERY_PRICE_PARSE:{type(e).__name__}:{e}", "source_receipt": receipt, "source_archives": archives, "discovery": None, "validation": None, "guards": GUARDS})
        return
    dsum = summarize(dtrades, p, validation=False)
    dgates, survives = discovery_gate(dsum, p)
    discovery = {"summary": dsum, "gates": dgates, "trades": dtrades}
    if not survives:
        write({**base_doc, "classification": "DISCOVERY_NO_EDGE", "reason": "one or more frozen Discovery promotion gates failed", "source_receipt": receipt, "source_archives": archives, "discovery": discovery, "validation": None, "guards": GUARDS})
        return

    validation_events = [e for e in events if int(e["year"]) == int(p["independent_validation"]["year"])]
    try:
        vtrades = [build_trade(e, p) for e in validation_events]
    except Exception as e:
        write({**base_doc, "classification": "DATA_FAILURE", "reason": f"VALIDATION_PRICE_PARSE:{type(e).__name__}:{e}", "source_receipt": receipt, "source_archives": archives, "discovery": discovery, "validation": None, "guards": GUARDS})
        return
    vsum = summarize(vtrades, p, validation=True)
    vgates, vpass = validation_gate(vsum, p)
    validation = {"summary": vsum, "gates": vgates, "trades": vtrades}
    cls = "INDEPENDENT_VALIDATION_SURVIVES" if vpass else "VALIDATION_FAIL"
    reason = "all frozen independent-validation gates passed" if vpass else "one or more frozen independent-validation gates failed"
    write({**base_doc, "classification": cls, "reason": reason, "source_receipt": receipt, "source_archives": archives, "discovery": discovery, "validation": validation, "guards": GUARDS})

if __name__ == "__main__":
    main()
