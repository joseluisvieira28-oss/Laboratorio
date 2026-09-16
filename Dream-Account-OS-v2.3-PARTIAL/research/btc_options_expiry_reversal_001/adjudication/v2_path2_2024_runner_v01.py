import calendar
import csv
import hashlib
import io
import json
import math
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = HERE / "V2_PATH2_REPLICATION_2024_FREEZE_V01.json"
AUTH = HERE / "AUTHORIZATION_2024_OPEN_2026-09-16.md"
OUT = HERE / "BOER_V2_PATH2_2024_RESULT_V01.json"
DV = "https://data.binance.vision"
ROOT = "data/futures/um/monthly/klines/BTCUSDT/1m"
UA = {"User-Agent": "Mozilla/5.0 BOER-V2-PATH2-2024-001/1.0"}
YEAR = 2024

GUARDS = {
    "authorized_year": YEAR,
    "year_2024_price_fields_opened": False,
    "year_2025_market_data_requested": False,
    "year_2026_market_data_requested": False,
    "signal_changed": False,
    "costs_changed": False,
    "timing_changed": False,
    "horizon_changed": False,
    "event_exclusions_added": False,
    "interpolation_or_substitution": False,
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


def get(url, attempts=5):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                break
        except Exception as e:
            last = e
        time.sleep(min(8.0, 0.5 * (2 ** i)))
    raise SourceBlocked(f"GET_FAILED:{url}:{type(last).__name__}:{last}")


def last_friday(year, month):
    day = calendar.monthrange(year, month)[1]
    d = datetime(year, month, day, 8, 0, tzinfo=timezone.utc)
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


def event_times(expiry):
    y, m, d = expiry.year, expiry.month, expiry.day
    return {
        "pre_start": int(datetime(y, m, d, 4, 0, tzinfo=timezone.utc).timestamp()),
        "pre_last": int(datetime(y, m, d, 7, 59, tzinfo=timezone.utc).timestamp()),
        "entry": int(datetime(y, m, d, 8, 5, tzinfo=timezone.utc).timestamp()),
        "exit": int(datetime(y, m, d, 10, 5, tzinfo=timezone.utc).timestamp()),
    }


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


def profit_factor(values):
    pos = sum(v for v in values if v > 0)
    neg = -sum(v for v in values if v < 0)
    if neg == 0:
        return None if pos == 0 else float("inf")
    return pos / neg


def mean(values):
    return sum(values) / len(values) if values else None


def main():
    if not FREEZE.exists() or not AUTH.exists():
        raise RuntimeError("FREEZE_OR_AUTHORIZATION_MISSING")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_PRE_2024_OUTCOME_ACCESS":
        raise RuntimeError("FREEZE_STATUS_INVALID")
    if freeze.get("replication_id") != "BOER-V2-PATH2-2024-001":
        raise RuntimeError("REPLICATION_ID_MISMATCH")

    base_cost = float(freeze["rules_immutable_from_parent"]["base_round_trip_cost_fraction"])
    stress_cost = float(freeze["rules_immutable_from_parent"]["stress_round_trip_cost_fraction"])
    events = []
    source_records = []

    try:
        for month in range(1, 13):
            expiry = last_friday(YEAR, month)
            times = event_times(expiry)
            ym = f"{YEAR:04d}-{month:02d}"
            name = f"BTCUSDT-1m-{ym}.zip"
            path = f"{ROOT}/{name}"
            checksum_raw = get(f"{DV}/{path}.CHECKSUM")
            official_sha = parse_checksum(checksum_raw, name)
            zb = get(f"{DV}/{path}")
            actual_sha = hashlib.sha256(zb).hexdigest().lower()
            if actual_sha != official_sha:
                raise DataFailure(f"SHA256_MISMATCH:{name}")

            wanted = set(times.values())
            found_ts = set()
            px = {}
            rows = 0
            with zipfile.ZipFile(io.BytesIO(zb)) as zz:
                bad = zz.testzip()
                if bad is not None:
                    raise DataFailure(f"ZIP_CRC_FAILURE:{name}:{bad}")
                members = [n for n in zz.namelist() if not n.endswith("/")]
                if len(members) != 1:
                    raise DataFailure(f"ZIP_MEMBER_COUNT:{name}:{len(members)}")
                with zz.open(members[0]) as f:
                    wrapper = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace", newline="")
                    for row in csv.reader(wrapper):
                        if not row:
                            continue
                        s = str(row[0]).strip()
                        if s.lower() in {"open_time", "opentime"}:
                            continue
                        if not s.isdigit():
                            raise DataFailure(f"FIRST_FIELD_NOT_TIMESTAMP:{name}")
                        ts = normalize_ts(s)
                        rows += 1
                        if ts not in wanted:
                            continue
                        found_ts.add(ts)
                        GUARDS["year_2024_price_fields_opened"] = True
                        if ts == times["pre_start"]:
                            px["pre_start_open"] = float(row[1])
                        elif ts == times["pre_last"]:
                            px["pre_last_close"] = float(row[4])
                        elif ts == times["entry"]:
                            px["entry_open"] = float(row[1])
                        elif ts == times["exit"]:
                            px["exit_open"] = float(row[1])
            missing = sorted(wanted - found_ts)
            if missing:
                raise DataFailure(f"MISSING_REQUIRED_EVENT_BARS:{ym}:{missing}")
            if len(px) != 4:
                raise DataFailure(f"PRICE_FIELDS_MISSING:{ym}:{sorted(px)}")
            for k, v in px.items():
                if not math.isfinite(v) or v <= 0:
                    raise DataFailure(f"NONPOSITIVE_OR_NONFINITE_PRICE:{ym}:{k}:{v}")

            pre_ret = px["pre_last_close"] / px["pre_start_open"] - 1.0
            if pre_ret == 0.0:
                trade = {
                    "year": YEAR,
                    "month": month,
                    "expiry_utc": expiry.isoformat().replace("+00:00", "Z"),
                    "resolved": False,
                    "reason": "EXACT_ZERO_PRE_RETURN",
                }
            else:
                direction = -1 if pre_ret > 0 else 1
                post_ret = px["exit_open"] / px["entry_open"] - 1.0
                gross = direction * post_ret
                base = gross - base_cost
                stress = gross - stress_cost
                trade = {
                    "year": YEAR,
                    "month": month,
                    "expiry_utc": expiry.isoformat().replace("+00:00", "Z"),
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
            events.append(trade)
            source_records.append({
                "year": YEAR,
                "month": month,
                "archive_path": path,
                "sha256": actual_sha,
                "rows": rows,
                "required_timestamps_present": True,
            })

        resolved = [t for t in events if t.get("resolved")]
        base = [t["base_net_return"] for t in resolved]
        stress = [t["stress_net_return"] for t in resolved]
        wins = sum(t["base_win"] for t in resolved)
        pf = profit_factor(base)
        loo = []
        if len(base) >= 2:
            for i in range(len(base)):
                rem = base[:i] + base[i+1:]
                loo.append(mean(rem))
        min_loo = min(loo) if loo else None

        metrics = {
            "scheduled_events": len(events),
            "resolved_trades": len(resolved),
            "unresolved_trades": len(events) - len(resolved),
            "base_mean_net_return": mean(base),
            "base_profit_factor": pf,
            "stress_mean_net_return": mean(stress),
            "base_wins": wins,
            "base_win_rate": wins / len(resolved) if resolved else None,
            "minimum_leave_one_trade_out_base_mean": min_loo,
            "long_trades": sum(t.get("direction") == "LONG" for t in resolved),
            "short_trades": sum(t.get("direction") == "SHORT" for t in resolved),
        }

        gates = {
            "resolved_trades_min": metrics["resolved_trades"] >= int(freeze["path2_pass_gates_all_required"]["resolved_trades_min"]),
            "base_mean_net_return_gt_zero": metrics["base_mean_net_return"] is not None and metrics["base_mean_net_return"] > 0,
            "base_profit_factor_min": metrics["base_profit_factor"] is not None and metrics["base_profit_factor"] >= float(freeze["path2_pass_gates_all_required"]["base_profit_factor_min"]),
            "stress_mean_net_return_gt_zero": metrics["stress_mean_net_return"] is not None and metrics["stress_mean_net_return"] > 0,
            "base_wins_min": metrics["base_wins"] >= int(freeze["path2_pass_gates_all_required"]["base_wins_min"]),
            "minimum_leave_one_trade_out_base_mean_gt_zero": metrics["minimum_leave_one_trade_out_base_mean"] is not None and metrics["minimum_leave_one_trade_out_base_mean"] > 0,
        }

        if metrics["resolved_trades"] < int(freeze["path2_pass_gates_all_required"]["resolved_trades_min"]):
            classification = "INSUFFICIENT_SAMPLE"
            v2 = "TIER_3_WATCHLIST_WEAK_CANDIDATE"
            operational = "NOT_QUASE_DIAMANTE"
        elif all(gates.values()):
            classification = "V2_SUPPORT_PATH_2_PASS__TIER_2_PROMOTED_CANDIDATE_QUASE_DIAMANTE"
            v2 = "TIER_2_PROMOTED_CANDIDATE"
            operational = "QUASE_DIAMANTE"
        else:
            classification = "V2_PATH2_FAIL__APPLY_FROZEN_POLICY_WITHOUT_RESCUE"
            v2 = "TIER_4_REJECTED_FOR_TESTED_IMPLEMENTATION"
            operational = "STONE_AFTER_INDEPENDENT_OOS"

        result = {
            "replication_id": freeze["replication_id"],
            "governing_policy_id": freeze["governing_policy_id"],
            "historical_parent_classification_preserved": freeze["historical_parent_classification"],
            "classification": classification,
            "v2_classification_after_2024": v2,
            "operational_label": operational,
            "metrics": metrics,
            "gates": gates,
            "events": events,
            "source_records": source_records,
            "guards": GUARDS,
        }
    except SourceBlocked as e:
        result = {
            "replication_id": freeze["replication_id"],
            "classification": "SOURCE_ACCESS_BLOCKED",
            "reason": str(e),
            "guards": GUARDS,
        }
    except DataFailure as e:
        result = {
            "replication_id": freeze["replication_id"],
            "classification": "DATA_FAILURE",
            "reason": str(e),
            "guards": GUARDS,
        }
    except Exception as e:
        result = {
            "replication_id": freeze["replication_id"],
            "classification": "TECHNICAL_FAILURE",
            "reason": f"{type(e).__name__}:{e}",
            "guards": GUARDS,
        }

    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
