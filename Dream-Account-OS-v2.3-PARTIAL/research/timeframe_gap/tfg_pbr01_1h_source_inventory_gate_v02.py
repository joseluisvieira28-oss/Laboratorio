from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

LAB_ID = "TFG-PBR01-1H-001"
FREEZE_FILENAME = "TFG_PBR01_1H_001_FREEZE.json"
START_MONTH = "2022-01"
END_MONTH = "2024-12"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
EXPECTED_MONTHS_PER_SYMBOL = 36
EXPECTED_FILE_COUNT = 216


def months(start: str, end: str) -> list[str]:
    cursor = datetime.strptime(start, "%Y-%m")
    finish = datetime.strptime(end, "%Y-%m")
    out: list[str] = []
    while cursor <= finish:
        out.append(cursor.strftime("%Y-%m"))
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = cursor.replace(year=year, month=month, day=1)
    return out


def prefix(symbol: str) -> str:
    return f"{symbol[:-4]}_USDT"


def run(raw_dir: Path, freeze_path: Path) -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    discovery = freeze["data_stages"]["discovery"]
    if freeze.get("experiment_id") != LAB_ID:
        raise RuntimeError("FREEZE_ID_MISMATCH")
    if freeze["timeframe_transformation"].get("target_timeframe") != "1H":
        raise RuntimeError("FREEZE_TIMEFRAME_MISMATCH")
    if freeze["timeframe_transformation"].get("policy") != "BAR_COUNT_INVARIANT":
        raise RuntimeError("FREEZE_TRANSFORMATION_MISMATCH")
    if discovery.get("requested_start") != "2022-01-01T00:00:00Z":
        raise RuntimeError("FREEZE_START_MISMATCH")
    if discovery.get("requested_end") != "2024-12-31T23:59:59Z":
        raise RuntimeError("FREEZE_END_MISMATCH")
    if freeze["governance"].get("2025_access") is not False:
        raise RuntimeError("2025_FIREWALL_MISMATCH")
    if freeze["governance"].get("2026_access") is not False:
        raise RuntimeError("2026_FIREWALL_MISMATCH")

    month_list = months(START_MONTH, END_MONTH)
    present: list[str] = []
    missing: list[str] = []
    per_symbol: dict[str, dict] = {}
    for symbol in SYMBOLS:
        found = []
        absent = []
        for month in month_list:
            name = f"{prefix(symbol)}-Min15-{month}-01.csv"
            if (raw_dir / name).is_file():
                found.append(month)
                present.append(name)
            else:
                absent.append(month)
                missing.append(name)
        per_symbol[symbol] = {
            "present_month_count": len(found),
            "missing_month_count": len(absent),
            "first_present_month": found[0] if found else None,
            "last_present_month": found[-1] if found else None,
            "missing_months": absent,
        }

    return {
        "status": "PASS_SOURCE_FILE_INVENTORY" if not missing else "BLOCKED_PRE_OUTCOME_SOURCE_FILES_MISSING",
        "lab_id": LAB_ID,
        "frozen_start_month": START_MONTH,
        "frozen_end_month": END_MONTH,
        "expected_months_per_symbol": EXPECTED_MONTHS_PER_SYMBOL,
        "expected_source_file_count": EXPECTED_FILE_COUNT,
        "present_source_file_count": len(present),
        "missing_source_file_count": len(missing),
        "per_symbol": per_symbol,
        "outcome_evaluation_performed": False,
        "market_file_contents_read": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--freeze", required=True)
    args = parser.parse_args()
    try:
        payload = run(Path(args.raw_dir), Path(args.freeze))
    except Exception as exc:
        payload = {
            "status": "BLOCKED_PRE_OUTCOME",
            "lab_id": LAB_ID,
            "reason": f"{type(exc).__name__}:{exc}",
            "outcome_evaluation_performed": False,
            "market_file_contents_read": False,
            "validation_2025_access_performed": False,
            "holdout_2026_access_performed": False,
            "network_access_performed": False,
            "exchange_mutation_performed": False,
        }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0 if payload["status"] == "PASS_SOURCE_FILE_INVENTORY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
