"""Offline V3 cost decomposition from verified V2 archives.

Research-only. No HTTP, orders, credentials, scheduler or modification to V2.
Hold-to-expiry values are *entry costs*, NOT PnL or evidence of alpha.
"""
from decimal import Decimal as D
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "economic_proof_v1"))
import audit_deribit as auditor

def compute(root=None):
    root = Path(root) if root is not None else auditor.ROOT
    rows = []
    for day, (filename, digest) in auditor.PINNED.items():
        a = auditor.audit(root / "evidence" / day / filename, digest, day)
        row = {"date": day, "source_status": a["status"], "technical_valid": a["status"] != "SOURCE_BLOCKED_REPRODUCED",
               "prospective_v3": False, "trade_executed": False, "net_pnl": None,
               "delivery_fee_status": "UNVERIFIED", "combo": "NO_VERIFIED_QUOTE",
               "maker": "FILL_NOT_OBSERVED"}
        if a["status"] == "COST_ABSTENTION_REPRODUCED":
            premium = D(a["premium_usdc"])
            spread = D(a["spread_usdc"])
            fees = D(a["four_fees_usdc"])
            # Auditor fee() is invoked twice per leg; fee split is NOT recoverable
            # from the aggregate without reconstructing the original books.
            # Thus do not mislabel half of fees as entry fees.
            row.update({
                "premium_ask_usdc": str(premium),
                "full_spread_usdc": str(spread),
                "four_trading_fees_usdc": str(fees),
                "v2_roundtrip_friction_usdc": str(spread + fees),
                "v2_roundtrip_friction_pct": str((spread + fees) / premium * 100),
                "v2_gate_pass": (spread + fees) / premium <= D(".08"),
                "hold_to_expiry_entry_cost_usdc": None,
                "hold_to_expiry_note": "ENTRY_FEES_NOT_DECOMPOSED; DELIVERY_FEE_UNVERIFIED",
                "stress_25pct_spread_widening_pct": str((spread * D("1.25") + fees) / premium * 100),
                "stress_50pct_spread_widening_pct": str((spread * D("1.50") + fees) / premium * 100),
            })
        rows.append(row)
    valid = [r for r in rows if r["technical_valid"]]
    return {
        "research_mode": "OFFLINE_REPLAY", "forward_v3_count": 0,
        "historic_attempts": len(rows), "historic_technical_valid": len(valid),
        "historic_v2_gate_pass": sum(r.get("v2_gate_pass", False) for r in valid),
        "all_in_pnl_available": False, "live_go": False,
        "warning": "Historical diagnostics only; no prospective V3 sessions or validated hold-to-expiry cash flow.",
        "rows": rows,
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, help="New JSON output path (never overwrite)")
    a = p.parse_args()
    result = compute()
    with Path(a.out).open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))
