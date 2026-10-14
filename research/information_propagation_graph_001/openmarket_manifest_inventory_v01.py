#!/usr/bin/env python3
import json,re
from datetime import datetime,timezone
from pathlib import Path
from huggingface_hub import HfApi

REPO="gregyoung14/openmarket-btc-polymarket"
REV="74502466d1a7cef56395bfd8d0b465fbebc849cf"
OUT=Path("artifacts/ipg001_openmarket_manifest_inventory_v01.json")
api=HfApi()
info=api.dataset_info(REPO,revision=REV,files_metadata=True)

keywords=re.compile(r"(lead|lag|clock|offset|sync|pair|manifest|metric|summary|report|artifact|snapshot)",re.I)
rows=[]
total=0
for s in info.siblings or []:
    path=s.rfilename
    size=getattr(s,"size",None)
    if isinstance(size,int): total+=size
    if keywords.search(path):
        rows.append({"path":path,"size":size})
small=[x for x in rows if isinstance(x["size"],int) and x["size"]<=10_000_000]
receipt={
 "lab_id":"INFORMATION-PROPAGATION-GRAPH-001",
 "stage":"OPENMARKET_EXACT_REVISION_MANIFEST_INVENTORY_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "dataset_repo":REPO,
 "revision":REV,
 "repo_sha_returned":info.sha,
 "file_count":len(info.siblings or []),
 "total_size_bytes_metadata_sum":total,
 "keyword_candidate_count":len(rows),
 "small_candidate_count":len(small),
 "keyword_candidates":rows[:500],
 "small_candidates":small[:500],
 "classification":"MANIFEST_INVENTORY_PASS" if info.sha==REV else "REVISION_MISMATCH",
 "data_file_content_opened":False,
 "market_outcomes_opened":False,
 "pnl_opened":False,
 "mutation":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ("classification","revision","file_count","total_size_bytes_metadata_sum","keyword_candidate_count","small_candidate_count")},indent=2))
