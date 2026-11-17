#!/usr/bin/env python3
"""LP-NET-001 -- historical source-integrity gate, never an investment backtest.

Reads only predownloaded public full CSVs from ThanosDrossos/IL_Measurement.
Does not contact a blockchain, a wallet, an exchange, or an API.
The data rows are burn observations, NOT independent completed positions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SOURCE_REPO = "ThanosDrossos/IL_Measurement"
SOURCE_COMMIT = "e75c0c566116b63a68107b9f8907071c53ca8ef2"
EXPECTED_GIT_BLOBS = {
    "DAI_USDC_500": "ab68f0cf6690b57cd26e018a854b2c020947c934",
    "DAI_USDC_100": "a33090679d99868abc057564948fe4ad20557be7",
    "USDC_WETH_10000": "80a36c21be612580b271f6817124a7affc3d0646",
    "USDC_WETH_100": "5474fa89e3b9f75df238770bec286ff98a9ad067",
    "MKR_WETH_10000": "f057eac64330d955e80fafd98a2b5163dd646714",
}
SOURCE_START = datetime(2022, 5, 1, tzinfo=timezone.utc).timestamp()
SOURCE_END = datetime(2024, 4, 2, tzinfo=timezone.utc).timestamp()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def number(row: dict, col: str) -> float:
    return float(row[col].replace(",", "."))


def aggregate(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0, "net_vs_hodl_sum_usd": None, "net_over_initial_pct": None,
                "positive_net_pct": None, "positive_after_15_usd_pct": None}
    net = sum(r["net"] for r in rows)
    capital = sum(r["initial"] for r in rows)
    return {"n": len(rows), "net_vs_hodl_sum_usd": round(net, 2),
            "net_over_initial_pct": round(100 * net / capital, 6) if capital > 0 else None,
            "positive_net_pct": round(100 * sum(r["net"] > 0 for r in rows) / len(rows), 3),
            "positive_after_15_usd_pct": round(100 * sum(r["net"] > 15 for r in rows) / len(rows), 3)}


def assess_csv(data: bytes, pool: str, expected_blob: str) -> dict:
    from io import StringIO
    blob = git_blob_sha1(data)
    result = {"pool": pool, "source_git_blob": blob, "blob_verified": blob == expected_blob}
    if not result["blob_verified"]:
        result["status"] = "SOURCE_HASH_MISMATCH"
        return result
    reader = csv.DictReader(StringIO(data.decode("utf-8-sig")), delimiter=";")
    rows, invalid_numeric = [], 0
    for row in reader:
        try:
            event_ts = number(row, "event_timestamp")
            initial, il, fees = [number(row, col) for col in
                                 ("initialValue", "lossVersusHODLExact", "event_feesUSD")]
            position = row["position_id"]
            identifier = row["id"]
            if not all((initial > 0, position, identifier)):
                invalid_numeric += 1
                continue
            rows.append({"ts": event_ts, "id": identifier, "position": position,
                         "initial": initial, "il": il, "fee": fees, "net": il + fees})
        except (ValueError, TypeError, KeyError, OverflowError):
            invalid_numeric += 1
    ids = Counter(x["id"] for x in rows)
    train = [x for x in rows if datetime.fromtimestamp(x["ts"], timezone.utc).year <= 2022]
    later = [x for x in rows if datetime.fromtimestamp(x["ts"], timezone.utc).year >= 2023]
    problems = {"invalid_rows": invalid_numeric,
                "duplicate_event_keys": sum(c > 1 for c in ids.values()),
                "positive_loss_vs_hodl_gt_1cent": sum(x["il"] > .01 for x in rows),
                "negative_attributed_fee": sum(x["fee"] < 0 for x in rows),
                "observations_before_documented_window": sum(x["ts"] < SOURCE_START for x in rows),
                "observations_after_documented_window": sum(x["ts"] >= SOURCE_END for x in rows)}
    return {**result, "status": "SOURCE_FLAGS_PRESENT" if any(problems.values()) else "SOURCE_FLAGS_ABSENT",
            "n_burn_rows": len(rows),
            "n_distinct_positions": len(set(x["position"] for x in rows)),
            "integrity_flags": problems, "training_2021_22": aggregate(train),
            "descriptive_later_2023_24": aggregate(later),
            "overall_ex_post_not_tradeable": aggregate(rows)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, required=True, help="Directory of pinned complete full CSVs")
    p.add_argument("--output", type=Path, default=Path("lp_net_001_source_gate.json"))
    args = p.parse_args()
    out = {"study": "LP-NET-001", "asof_date": "2026-11-17", "source_repo": SOURCE_REPO,
           "source_commit": SOURCE_COMMIT, "source_type": "retrospective burn-event CSVs",
           "execution": "none", "fills": 0, "live_orders": 0, "capital_spent_chf": 0,
           "scope_warning": "Not a pre-entry pool selection backtest; gas and onchain integrity unverified.",
           "results": []}
    for pool, expected in EXPECTED_GIT_BLOBS.items():
        path = args.data_dir / f"{pool}_normalized_data.csv"
        if not path.is_file():
            out["results"].append({"pool": pool, "status": "SOURCE_NOT_PRESENT"})
            continue
        out["results"].append(assess_csv(path.read_bytes(), pool, expected))
    out["economic_verdict"] = "NO_LIVE_GO_SOURCE_ONLY"
    out["next_gate"] = "Independent onchain NFT-level mint/decrease/collect reconstruction; point-in-time signals; real gas and exit depth; OOS."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"economic_verdict": out["economic_verdict"],
                      "statuses": {x["pool"]: x["status"] for x in out["results"]}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
