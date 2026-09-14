from __future__ import annotations

import ast
import calendar
import csv
import hashlib
import io
import json
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LAB_ID = "TOKEN-UNLOCK-EVENT-001"
MVE_ID = "TUE-CLIFF-ADV30-001"
SOURCE_REPO = "6th-Man-Ventures/token-vesting"
SOURCE_COMMIT = "7d2bf881ca3c6ffe7c30ab34889bb92c08b1904a"
SOURCE_PATH = "data/vesting_data.py"
SOURCE_URL = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{SOURCE_PATH}"
KNOWN_AT = datetime(2023, 5, 19, 18, 0, 5, tzinfo=timezone.utc)
MIN_EVENT_DATE = date(2023, 6, 19)  # >=30 full calendar days after immutable snapshot
MAX_EVENT_DATE = date(2024, 12, 31)
ALLOWED_FREQ = {"weekly", "monthly", "quarterly", "annually"}
OUT_DIR = Path(__file__).resolve().parent / "source_probe_output_v02"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_source() -> tuple[str, str]:
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "CryptoLab-SourceGate/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    sha = hashlib.sha256(raw).hexdigest()
    return raw.decode("utf-8"), sha


def extract_literal_dicts(src: str) -> dict[str, dict]:
    tree = ast.parse(src)
    wanted = {"private_allocations", "public_allocations"}
    found: dict[str, dict] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in wanted:
            val = ast.literal_eval(node.value)
            if not isinstance(val, dict):
                raise TypeError(f"{target.id} is not a dict")
            found[target.id] = val
    missing = wanted.difference(found)
    if missing:
        raise RuntimeError(f"missing source dictionaries: {sorted(missing)}")
    return found


def parse_date(s: str) -> date:
    # Source pipeline uses pandas' default parsing for MM-DD-YYYY strings.
    return datetime.strptime(s, "%m-%d-%Y").date()


def add_months(d: date, months: int) -> date:
    month0 = d.month - 1 + months
    year = d.year + month0 // 12
    month = month0 % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def step_date(d: date, frequency: str) -> date:
    if frequency == "weekly":
        return d + timedelta(weeks=1)
    if frequency == "monthly":
        return add_months(d, 1)
    if frequency == "quarterly":
        return add_months(d, 3)
    if frequency == "annually":
        return add_months(d, 12)
    raise ValueError(f"unsupported discrete frequency: {frequency}")


def source_semantic_events(row: dict) -> list[tuple[date, float, str]]:
    """Reproduce the 6MV vesting engine's discrete release semantics without market data.

    Returns (date, token_amount, event_component_kind). Daily schedules are excluded upstream.
    The source's cliff alignment is intentionally reproduced from utils/daily_charts.py.
    """
    start = parse_date(row["start"])
    end = parse_date(row["end"])
    allocation = float(row["allocation"])
    cliff = int(row.get("cliff", 0) or 0)
    cliff_pct = float(row.get("cliff_amt", 0) or 0)
    frequency = str(row.get("vesting_frequency", "daily"))

    if start > MAX_EVENT_DATE:
        return []
    if start == end:
        return [(start, allocation, "single_release")]
    if frequency not in ALLOWED_FREQ:
        return []

    vest_length = (end - start).days
    if vest_length <= 0:
        return []

    adjusted_start = start + timedelta(days=cliff)
    vest_dates = []
    cur = adjusted_start
    while cur <= end:
        vest_dates.append(cur)
        cur = step_date(cur, frequency)

    if cliff or cliff_pct:
        cliff_amount = (cliff / vest_length) * allocation if cliff_pct == 0 else allocation * (cliff_pct / 100.0)
    else:
        cliff_amount = 0.0

    vest_amount = (allocation - cliff_amount) / (len(vest_dates) - 1) if len(vest_dates) > 1 else 0.0

    # Reproduce source list alignment: cliff_list is prepended to an allocation list
    # indexed against the original start date. TGE adjustment removes one day when
    # an immediate explicit cliff amount exists.
    tge_adjustment = 1 if cliff_amount and cliff == 0 else 0
    n_regular_days = max(0, vest_length - cliff - tge_adjustment)
    values = []
    kinds = []
    if cliff or cliff_amount:
        n_cliff_days = max(0, cliff - 1)
        values.extend([0.0] * n_cliff_days)
        kinds.extend(["none"] * n_cliff_days)
        values.append(cliff_amount)
        kinds.append("cliff_release")

    for i in range(n_regular_days):
        d = adjusted_start + timedelta(days=i)
        if d in vest_dates:
            values.append(vest_amount)
            kinds.append("discrete_vest")
        else:
            values.append(0.0)
            kinds.append("none")

    out = []
    for idx, (amt, kind) in enumerate(zip(values, kinds)):
        if amt <= 0:
            continue
        d = start + timedelta(days=idx)
        out.append((d, amt, kind))
    return out


def main() -> None:
    src, source_sha256 = fetch_source()
    dicts = extract_literal_dicts(src)

    aggregate: dict[tuple[str, date], dict] = {}
    source_schedule_count = 0
    candidate_component_count = 0

    for allocation_class, token_map in dicts.items():
        for token, meta in token_map.items():
            for row in meta.get("vesting", []):
                source_schedule_count += 1
                frequency = str(row.get("vesting_frequency", "daily"))
                if frequency == "daily":
                    continue
                for event_date, amount, kind in source_semantic_events(row):
                    if not (MIN_EVENT_DATE <= event_date <= MAX_EVENT_DATE):
                        continue
                    candidate_component_count += 1
                    key = (token, event_date)
                    rec = aggregate.setdefault(key, {
                        "lab_id": LAB_ID,
                        "mve_id": MVE_ID,
                        "token_id": token,
                        "scheduled_date_utc": event_date.isoformat(),
                        "scheduled_unlock_tokens": 0.0,
                        "component_count": 0,
                        "allocation_classes": set(),
                        "recipient_groups": set(),
                        "frequencies": set(),
                        "component_kinds": set(),
                        "known_at_utc": KNOWN_AT.isoformat().replace("+00:00", "Z"),
                        "known_lead_days": (event_date - KNOWN_AT.date()).days,
                        "source_repo": SOURCE_REPO,
                        "source_commit": SOURCE_COMMIT,
                        "source_path": SOURCE_PATH,
                        "source_sha256": source_sha256,
                        "pit_status": "IMMUTABLE_SNAPSHOT_CANDIDATE",
                        "timing_precision": "calendar_date_only",
                        "outcome_data_accessed": False,
                    })
                    rec["scheduled_unlock_tokens"] += float(amount)
                    rec["component_count"] += 1
                    rec["allocation_classes"].add(allocation_class)
                    rec["recipient_groups"].add(str(row.get("group", "unknown")))
                    rec["frequencies"].add(frequency)
                    rec["component_kinds"].add(kind)

    rows = []
    for rec in aggregate.values():
        rec = dict(rec)
        for field in ("allocation_classes", "recipient_groups", "frequencies", "component_kinds"):
            rec[field] = sorted(rec[field])
        rec["scheduled_unlock_tokens"] = round(rec["scheduled_unlock_tokens"], 12)
        rows.append(rec)
    rows.sort(key=lambda r: (r["scheduled_date_utc"], r["token_id"]))

    # Hard output guard: nothing after 2024 may be serialized.
    for r in rows:
        d = date.fromisoformat(r["scheduled_date_utc"])
        assert d <= MAX_EVENT_DATE
        assert d >= MIN_EVENT_DATE
        assert r["known_lead_days"] >= 30
        assert r["outcome_data_accessed"] is False

    distinct_tokens = sorted({r["token_id"] for r in rows})
    years = sorted({int(r["scheduled_date_utc"][:4]) for r in rows})
    cliff_events = sum("cliff_release" in r["component_kinds"] for r in rows)

    manifest_path = OUT_DIR / "TUE_6MV_CANDIDATE_MANIFEST_2023_2024_V01.json"
    manifest_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # CSV contains only <=2024 candidate source fields; no price/outcome fields exist.
    csv_path = OUT_DIR / "TUE_6MV_CANDIDATE_MANIFEST_2023_2024_V01.csv"
    fields = [
        "token_id", "scheduled_date_utc", "scheduled_unlock_tokens", "component_count",
        "known_at_utc", "known_lead_days", "pit_status", "timing_precision",
        "source_commit", "source_sha256"
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "mode": "SOURCE_ONLY_CANDIDATE_MANIFEST",
        "source_repo": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "source_sha256": source_sha256,
        "known_at_utc": KNOWN_AT.isoformat().replace("+00:00", "Z"),
        "min_candidate_event_date": MIN_EVENT_DATE.isoformat(),
        "max_candidate_event_date": MAX_EVENT_DATE.isoformat(),
        "daily_schedules_excluded": True,
        "candidate_events": len(rows),
        "candidate_components": candidate_component_count,
        "distinct_tokens": len(distinct_tokens),
        "calendar_years": years,
        "cliff_events": cliff_events,
        "source_schedules_parsed": source_schedule_count,
        "hard_gate_counts_met": len(rows) >= 40 and len(distinct_tokens) >= 15 and len(years) >= 2,
        "all_rows_pit_final": False,
        "timing_precision_final": False,
        "source_gate_pass": False,
        "classification": "SOURCE_PIT_PROVENANCE_INCOMPLETE",
        "guards": {
            "future_event_rows_serialized": False,
            "price_data_accessed": False,
            "returns_computed": False,
            "pnl_computed": False,
            "profit_factor_computed": False,
            "year_2025_market_data_accessed": False,
            "year_2026_market_data_accessed": False,
            "live_trading": False,
            "exchange_mutation": False
        },
        "next_requirement": "Upgrade enough candidate rows to final PIT/timing provenance and validate Binance pre-event volume availability without opening outcomes."
    }
    (OUT_DIR / "TUE_6MV_CANDIDATE_RECEIPT_V01.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("NO PRICE / NO RETURNS / NO PNL / OUTCOMES CLOSED")


if __name__ == "__main__":
    main()
