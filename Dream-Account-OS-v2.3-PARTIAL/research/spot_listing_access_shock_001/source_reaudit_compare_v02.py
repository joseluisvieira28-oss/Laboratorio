#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib
from pathlib import Path

canonical_path=Path("artifacts/slas_reaudit/canonical_source_gate.json")
current_path=Path("Dream-Account-OS-v2.3-PARTIAL/research/spot_listing_access_shock_001/source_evidence/SLAS_SOURCE_GATE_V01.json")
out_path=Path("artifacts/slas_reaudit/SLAS_SOURCE_REAUDIT_V0_2.json")

old=json.loads(canonical_path.read_text())
new=json.loads(current_path.read_text())

def summary(d):
    r=d["receipt"]
    ids=sorted((x["symbol"],x["event_timestamp_utc"]) for x in d.get("qualified_events",[]))
    return {
      "classification":r["classification"],
      "root_spot_exact_usdt_symbols":r["root_spot_exact_usdt_symbols"],
      "qualified_events":r["qualified_events"],
      "qualified_distinct_symbols":r["qualified_distinct_symbols"],
      "qualified_year_counts":r["qualified_year_counts"],
      "counts_by_kind":r["counts_by_kind"],
      "technical_count":r["technical_count"],
      "source_block_count":r["source_block_count"],
      "qualified_identity":ids,
      "qualified_identity_sha256":hashlib.sha256(json.dumps(ids,separators=(",",":"),sort_keys=True).encode()).hexdigest(),
    }

o=summary(old); n=summary(new)
changed={k:{"canonical":o[k],"reaudit":n[k]} for k in o if o[k]!=n[k]}

if n["classification"] in {"SOURCE_ACCESS_BLOCKED","TECHNICAL_FAILURE"}:
    cls="SOURCE_REAUDIT_SOURCE_BLOCKED"
elif n["classification"]=="SOURCE_DATA_PASS":
    cls="SOURCE_REAUDIT_SOURCE_DATA_PASS"
elif not changed:
    cls="SOURCE_REAUDIT_UNCHANGED"
else:
    cls="SOURCE_REAUDIT_BACKFILL_CHANGED_STILL_INSUFFICIENT"

doc={
  "lab_id":"SPOT-LISTING-ACCESS-SHOCK-001",
  "mve_id":"SLAS-BINANCE-SPOT-AFTER-PERP-001",
  "audit_id":"SLAS-SOURCE-REAUDIT-V0.2",
  "classification":cls,
  "canonical":o,
  "reaudit":n,
  "changed_fields":changed,
  "market_price_values_opened":False,
  "ohlc_opened":False,
  "returns_computed":False,
  "pnl_computed":False,
  "year_2025_opened":False,
  "year_2026_opened":False,
  "discovery_authorized":False,
}
out_path.parent.mkdir(parents=True,exist_ok=True)
out_path.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:doc[k] for k in ("classification","changed_fields")},sort_keys=True))
