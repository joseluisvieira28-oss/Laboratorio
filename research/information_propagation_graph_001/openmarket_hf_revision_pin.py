#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path
from huggingface_hub import HfApi

REPO="gregyoung14/openmarket-btc-polymarket"
REV="7450246"
OUT=Path("artifacts/ipg001_openmarket_hf_revision_pin.json")

api=HfApi()
info=api.dataset_info(REPO, revision=REV, files_metadata=False)
siblings=[x.rfilename for x in (info.siblings or [])]
receipt={
  "lab_id":"INFORMATION-PROPAGATION-GRAPH-001",
  "stage":"OPENMARKET_HF_DATASET_REVISION_PIN",
  "captured_at_utc":datetime.now(timezone.utc).isoformat(),
  "dataset_repo":REPO,
  "requested_revision":REV,
  "resolved_full_sha":info.sha,
  "last_modified":str(info.last_modified),
  "siblings_count":len(siblings),
  "has_readme":"README.md" in siblings,
  "classification":"DATASET_REVISION_PIN_PASS" if isinstance(info.sha,str) and len(info.sha)==40 else "DATASET_REVISION_PIN_BLOCKED",
  "market_outcomes_opened":False,
  "mutation":False,
  "pnl_opened":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if receipt["classification"]!="DATASET_REVISION_PIN_PASS":
    raise SystemExit(2)
