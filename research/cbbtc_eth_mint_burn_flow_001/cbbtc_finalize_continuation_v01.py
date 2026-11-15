#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

HERE=Path("research/cbbtc_eth_mint_burn_flow_001")
MAN=Path("artifacts/cbbtc_continuation_manifest_v01.json")
OUT_JSON=HERE/"CLOSEOUT_RECEIPT_V0.1.json"
OUT_MD=HERE/"CLOSEOUT_V0.1.md"

if not MAN.exists():
    raise SystemExit("CONTINUATION_MANIFEST_MISSING")

m=json.loads(MAN.read_text())
cls=m.get("classification")

terminal={
  "PREDICTOR_FLOW_CENSUS_BLOCKED",
  "FLOW_STATE_CALIBRATION_BLOCKED",
  "FLOW_PREDICTOR_SOURCE_BLOCKED",
  "FLOW_PREDICTOR_INSUFFICIENT_SAMPLE",
  "DISCOVERY_OUTCOME_INSUFFICIENT_SAMPLE",
  "FLOW_DISCOVERY_FAIL",
  "FLOW_DISCOVERY_BLOCKED"
}

if cls=="FLOW_DISCOVERY_PASS":
    status={
      "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
      "stage":"POST_DISCOVERY_STATUS_V0.1",
      "classification":"FLOW_DISCOVERY_PASS_PENDING_SEPARATE_OOS_AUTHORITY",
      "terminal":False,
      "protected_2026_opened":False,
      "pnl_opened":False,
      "live_trading":False,
      "promotion_credit":0,
      "completed_stages":m.get("completed_stages",[])
    }
    OUT_JSON.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    OUT_MD.write_text("""# CBBTC-ETH-MINT-BURN-FLOW-001 — POST-DISCOVERY STATUS V0.1

Classification: FLOW_DISCOVERY_PASS_PENDING_SEPARATE_OOS_AUTHORITY

Discovery PASS is mechanism evidence only.

2026 remains CLOSED.
No OOS, PnL, sizing, live trading, exchange mutation or main merge is authorized.

A separate pre-frozen OOS authority is required before any 2026 data may be opened.
""")
    print(json.dumps(status,indent=2,sort_keys=True))
    raise SystemExit(0)

if cls not in terminal:
    raise SystemExit("NONTERMINAL_OR_UNKNOWN_CONTINUATION_CLASSIFICATION:"+str(cls))

rec={
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"CLOSEOUT_V0.1",
  "closed_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "final_classification":cls,
  "terminal":True,
  "completed_stages":m.get("completed_stages",[]),
  "census_classification":m.get("census_classification"),
  "ledger_event_count":m.get("ledger_event_count"),
  "daily_row_count":m.get("daily_row_count"),
  "q10":m.get("q10"),
  "q90":m.get("q90"),
  "sample_classification":m.get("sample_classification"),
  "transition_event_count":m.get("transition_event_count"),
  "negative_extreme_event_count":m.get("negative_extreme_event_count"),
  "positive_extreme_event_count":m.get("positive_extreme_event_count"),
  "discovery_classification":m.get("discovery_classification"),
  "market_returns_opened":m.get("market_returns_opened",False),
  "protected_2026_opened":False,
  "pnl_opened":False,
  "live_trading":False,
  "mutation":False,
  "promotion_credit":0,
  "rescue_allowed":False
}
OUT_JSON.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")

md=f"""# CBBTC-ETH-MINT-BURN-FLOW-001 — CLOSEOUT V0.1

Final classification: **{cls}**

This classification is terminal for the exact frozen lab.

Completed stages:
{chr(10).join('- '+str(x) for x in m.get('completed_stages',[]))}

Outcome boundary:
- market returns opened: {str(m.get('market_returns_opened',False)).lower()}
- protected 2026 opened: false
- PnL opened: false
- live trading: false
- promotion credit: 0

## No rescue

Do not rescue this exact lab by:
- changing source network or contract;
- changing q10/q90;
- using raw instead of normalized flow;
- changing H2-2025 sample construction;
- altering de-clustering;
- dropping one tail;
- changing the frozen 24h primary horizon;
- using the 72h diagnostic as primary;
- inverting direction;
- opening 2026.

A successor requires a materially distinct hypothesis and a new pre-outcome freeze.
"""
OUT_MD.write_text(md)
print(json.dumps(rec,indent=2,sort_keys=True))
