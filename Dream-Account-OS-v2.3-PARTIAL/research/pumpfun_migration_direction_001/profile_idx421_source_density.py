#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
from collections import Counter
from source_rebuild_helius_v01 import Rpc, bonding_curve_pda, load_manifest, parse_ts
from chain_boundary_feasibility_v06 import paginate_window, BOUNDARY_LOOKBACK_SECONDS

IDX=421
RETRIEVAL_ENVELOPE_SECONDS=600

rows=load_manifest(Path("pmd_source_rebuild_manifest_v01.jsonl"))
r=rows[IDX]
mint=r["mint"]; pda=bonding_curve_pda(mint); t0=parse_ts(r["t0"])
rpc=Rpc("https://api.mainnet-beta.solana.com","pmd_v074_idx421_profile")
sigs,paging=paginate_window(rpc,pda,t0-RETRIEVAL_ENVELOPE_SECONDS)
valid=[x for x in sigs if x.get("blockTime") is not None and t0-RETRIEVAL_ENVELOPE_SECONDS<=float(x["blockTime"])<=math.floor(t0)]
bins=Counter()
for x in valid:
    lag=int(t0-float(x["blockTime"]))
    bins[(lag//60)*60]+=1
slots={int(x["slot"]) for x in valid if x.get("slot") is not None}
receipt={
 "lab":"PMD-001","stage":"IDX421_SOURCE_DENSITY_PROFILE","economic_outcomes_opened":False,
 "scientific_verdict_authority":False,"index":IDX,"mint":mint,"t0":r["t0"],
 "retrieval_envelope_seconds":RETRIEVAL_ENVELOPE_SECONDS,
 "signatures_total_returned":len(sigs),"signatures_in_envelope":len(valid),
 "unique_slots_in_envelope":len(slots),"paging":paging,
 "per_60s_lag_bins":[{"lag_start_s":k,"count":bins[k]} for k in sorted(bins)],
 "rpc_request_counter":rpc.counter
}
Path("idx421_profile.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
