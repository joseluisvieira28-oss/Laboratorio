"""Offline release audit. Synthetic files only; no exchange client or credentials.

Exit 2 means a release invariant failed. This is not an executor or readiness tool.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from radar.operator_risk_v02 import build_operator_risk_state, realized_loss_state
from radar.global_fishing_dispatcher_v02 import arbitrate_due_signals

NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


class SyntheticAccount:
    def open_positions(self):
        return []

    def open_orders(self):
        return []

    def assets(self):
        return [{"currency": "USDT", "equity": 100, "availableBalance": 100}]


def run_audit():
    checks = []

    def record(code, passed, observed, required):
        checks.append({"code": code, "pass": bool(passed),
                       "observed": observed, "required": required})

    def risk(root):
        return build_operator_risk_state(private_client=SyntheticAccount(),
                                         receipt_root=root, now=NOW)

    with tempfile.TemporaryDirectory(prefix="triple-offline-audit-") as td:
        base = Path(td)
        with patch.dict(os.environ, {"CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS": ""}):
            for name, filename, content in [
                ("CORRUPT_RECONCILIATION", "POST_TRADE_RECONCILIATION.json", "{"),
                ("CORRUPT_ACTIVE_STATE", "ACTIVE_TRADE_STATE.json", "{"),
                ("UNRESOLVED_INTENT", "ORDER_INTENT.json", json.dumps({
                    "external_oid": "synthetic-pending", "signal_identity": "synthetic"})),
                ("NONFINITE_PNL", "POST_TRADE_RECONCILIATION.json", json.dumps({
                    "closed_at_utc": "2026-09-30T10:00:00Z",
                    "realized_net_pnl_usdt": "NaN"})),
            ]:
                root = base / name
                root.mkdir()
                (root / filename).write_text(content, encoding="utf-8")
                state = risk(root)
                record(name, not state["pass"],
                       {"risk_pass": state["pass"], "blockers": state["blockers"]},
                       "FAIL_CLOSED until the receipt or intent is reconciled")

            root = base / "overlap"
            child = root / "trade"
            child.mkdir(parents=True)
            (child / "POST_TRADE_RECONCILIATION.json").write_text(json.dumps({
                "signal_identity": "synthetic-one-trade",
                "closed_at_utc": "2026-09-30T10:00:00Z",
                "realized_net_pnl_usdt": -3}), encoding="utf-8")
            with patch.dict(os.environ, {"CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS": str(child)}):
                state = realized_loss_state(root, now=NOW)
            record("OVERLAPPING_RECEIPT_ROOTS", state["daily_realized_loss_usdt"] == 3,
                   state["daily_realized_loss_usdt"], "Count this one receipt once: 3 USDT")

    signal = {"candidate_id": "SYNTHETIC", "immutable_signal_key": "one",
              "entry_target_utc": "2026-09-30T11:00:00Z", "max_late_seconds": "NaN"}
    decision = arbitrate_due_signals([signal], now=NOW, global_slot_occupied=False)
    record("NONFINITE_LATENESS", decision["winner"] is None,
           decision["status"], "Reject non-finite timing; a one-hour-old signal must not win")

    source_root = Path(__file__).resolve().parents[1]
    files = ["radar/operator_risk_v02.py", "radar/global_fishing_dispatcher_v02.py",
             "radar/operator_futures_engine_v02.py", "radar/dh03_12h_local.py",
             "radar/dh03_12h_core.py"]
    hashes = {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest()
              for name in files}
    return {"audit_id": "TRIPLE_FISHING_V03_OFFLINE_RELEASE_AUDIT",
            "status": "BLOCKED" if any(not c["pass"] for c in checks) else "PROBES_PASS_ONLY",
            "live_readiness_verified": False, "exchange_contacted": False,
            "runtime_modified": False, "synthetic_probe_count": len(checks),
            "failed_invariant_count": sum(not c["pass"] for c in checks),
            "source_sha256": hashes, "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_audit()
    # Never overwrite an earlier audit or any live receipt.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in
                      ("status", "synthetic_probe_count", "failed_invariant_count")}))
    raise SystemExit(2 if report["status"] == "BLOCKED" else 0)
