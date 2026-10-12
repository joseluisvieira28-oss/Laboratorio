"""Offline audit only. Reads local copies; never contacts the exchange."""
import argparse
import hashlib
import json
from pathlib import Path
from radar.mexc_accounting import order_fee, reconcile_session


def audit(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    for item in manifest["files"]:
        p = root / item["path"]
        if item.get("preserved_in_repository") and not p.exists():
            raise ValueError(f"evidence missing: {item['path']}")
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"evidence hash mismatch: {item['path']}")
    rows = []
    count = 0
    for p in sorted(root.rglob("POST_TRADE_RECONCILIATION.json")):
        row = json.loads(p.read_text())
        session = p.parent
        entry = json.loads((session / "FILL_RECEIPT.json").read_text())["order"]
        exit_path = session / "EXIT_FILL_RECEIPT.json"
        exits = json.loads(exit_path.read_text())["orders"] if exit_path.exists() else []
        count += 1 + len(exits)
        result = {"signal_identity": row["signal_identity"],
                  "original_reconciliation_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                  "stored_net_pnl_usdt": row["realized_net_pnl_usdt"],
                  "entry_fee_from_execution_usdt": str(order_fee(entry)),
                  "exit_fee_from_execution_usdt": str(sum(order_fee(o) for o in exits)) if exits else None,
                  "observed_taker_fee_rates": [o.get("takerFeeRate") for o in [entry, *exits]],
                  "observed_maker_fee_rates": [o.get("makerFeeRate") for o in [entry, *exits]],
                  "accounting_verified": False}
        try:
            result.update(reconcile_session(session))
            result["status"] = "VERIFIED"
        except (ValueError, KeyError, FileNotFoundError) as exc:
            blocker = (f"MISSING_EVIDENCE:{Path(exc.filename).name}"
                       if isinstance(exc, FileNotFoundError) else f"{type(exc).__name__}:{exc}")
            result.update(status="FAIL_CLOSED", blocker=blocker,
                          missing_evidence=[name for name in ("EXIT_FILL_RECEIPT.json", "FINAL_POSITION_HISTORY.json")
                                            if not (session / name).exists()])
        rows.append(result)
    return {"status": "FAIL_CLOSED" if any(not r["accounting_verified"] for r in rows) else "VERIFIED",
            "trade_count": len(rows), "execution_records_available": count,
            "execution_records_expected": 12, "original_receipts_mutated": False,
            "exchange_access_performed": False, "entries": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = audit(args.root)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "entries"}, indent=2))
