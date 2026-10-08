#!/usr/bin/env python3
"""Read-only public runtime status probe for frozen TFG Donchian regime shadow.

Only GET /health of known public Radar service; no tokens, secrets, private account,
database read, orders, or scientific outcomes modified. Reports source/persistence
observability; a healthy probe never constitutes economic edge evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
from pathlib import Path
import sys

URL = "https://crypto-edge-radar-v05-canary.onrender.com/health"
OUT = Path("research/tfg_simplicity/receipt_public_runtime_only.json")


def probe() -> int:
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt = {
        "type": "TFG_REGIME_RUNTIME_PUBLIC_ONLY",
        "checked_at_utc": stamp,
        "endpoint": URL,
        "private_account_reads": False,
        "database_reads_direct": False,
        "orders": False,
        "science_changed": False,
        "outcome_reconstruction": False,
    }
    try:
        request = Request(URL, headers={"User-Agent": "TFG-public-health-research-only/0.1"}, method="GET")
        try:
            with urlopen(request, timeout=45) as resp:
                code = resp.status
                raw = resp.read(250000)
        except HTTPError as error:
            code = error.code
            raw = error.read(250000)
        receipt["http_status"] = code
        state = json.loads(raw.decode("utf-8"))
        tfg = state.get("tfg") or {}
        met = state.get("tfg_forward_metrics") or {}
        errs = state.get("errors") or {}
        receipt.update({
            "radar_health": state.get("health"),
            "radar_mode": state.get("mode"),
            "radar_checked_at_utc": state.get("checked_at_utc"),
            "runtime_revision": (state.get("runtime_identity") or {}).get("git_commit"),
            "persistence_backend": state.get("evidence_backend"),
            "watcher_status": tfg.get("status"),
            "watcher_latest_signal_close": tfg.get("latest_due_signal_close_utc"),
            "watcher_boundaries_scanned": tfg.get("boundaries_scanned"),
            "watcher_eligible_signals": tfg.get("eligible_signal_count"),
            "source_error_class": (
                str(errs.get("tfg", "")).split(":", 1)[0] if errs.get("tfg") else None
            ),
            "forward_classification": met.get("classification"),
            "resolved_forward_trades": met.get("resolved_forward_trades"),
            "forward_minimum": met.get("minimum_resolved_forward_trades"),
            "unresolved_forward_trades": met.get("unresolved_execution_paths"),
            "rule_deviations": met.get("rule_deviations"),
            "missed_eligible_signals": met.get("missed_eligible_signals"),
            "base_expectancy_r": met.get("base_expectancy_r"),
            "base_profit_factor": met.get("base_profit_factor"),
            "base_total_r": met.get("base_total_r"),
            "stress_expectancy_r": met.get("stress_expectancy_r"),
            "stress_profit_factor": met.get("stress_profit_factor"),
            "stress_total_r": met.get("stress_total_r"),
            "unresolved_state_breakdown": met.get("unresolved_state_breakdown"),
            "gate_checks": met.get("gate_checks"),
            "readiness_gate_pass": met.get("readiness_gate_pass"),
            "live_capital_enabled": state.get("live_capital_enabled"),
            "orders_created": state.get("orders_created"),
        })
        if not met:
            receipt["classification"] = "RUNTIME_SCHEMA_OR_METRICS_MISSING"
        elif tfg.get("status") == "FAIL_CLOSED" or errs.get("tfg"):
            receipt["classification"] = "TFG_WATCHER_FAIL_CLOSED"
        elif code != 200:
            receipt["classification"] = "RUNTIME_HEALTH_NON200"
        elif met.get("readiness_gate_pass"):
            receipt["classification"] = "FORWARD_GATE_REPORTED_PASS_REQUIRES_INDEPENDENT_AUDIT"
        else:
            receipt["classification"] = "TFG_PROSPECTIVE_EVIDENCE_NOT_YET_VERIFIED"
    except Exception as exc:
        receipt["classification"] = "PUBLIC_RUNTIME_UNAVAILABLE"
        receipt["error_type"] = type(exc).__name__
        receipt["error_message"] = str(exc)[:300]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0 if receipt["classification"] in {
        "FORWARD_GATE_REPORTED_PASS_REQUIRES_INDEPENDENT_AUDIT",
        "TFG_PROSPECTIVE_EVIDENCE_NOT_YET_VERIFIED",
    } else 2


if __name__ == "__main__":
    sys.exit(probe())
