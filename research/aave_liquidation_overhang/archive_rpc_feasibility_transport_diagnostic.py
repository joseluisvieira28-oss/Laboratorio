#!/usr/bin/env python3
import json
from pathlib import Path

fs=list(Path("downloaded_archive_feas").rglob("AAVE_ARCHIVE_RPC_REPLACEMENT_SOURCE_FEASIBILITY_V0_2B.json"))
if len(fs)!=1:
    raise SystemExit(f"expected one receipt, found {len(fs)}")
obj=json.loads(fs[0].read_text())
rows={}
single_all=[]
for ep,r in (obj.get("endpoint_results") or {}).items():
    singles=r.get("single_calls") or []
    single_ok=sum(1 for x in singles if x.get("ok"))
    single_all_pass=(len(singles)==4 and single_ok==4)
    if single_all_pass:
        single_all.append(ep)
    rows[ep]={
      "single_pass_count":single_ok,
      "single_all_4_pass":single_all_pass,
      "batch_ok":bool((r.get("batch") or {}).get("ok")),
      "batch_shape":(r.get("batch") or {}).get("shape"),
      "endpoint_full_pass":bool(r.get("endpoint_pass")),
      "single_error_codes":[x.get("error_code") for x in singles if not x.get("ok")],
      "batch_error_code":(r.get("batch") or {}).get("error_code"),
      "batch_http_status":(r.get("batch") or {}).get("http_status"),
    }
out={"upstream_classification":obj.get("classification"),"single_call_all_4_pass_count":len(single_all),"single_call_all_4_pass_endpoints":single_all,"endpoint_summary":rows,"safety":obj.get("safety")}
Path("archive_rpc_feas_diag_output").mkdir(exist_ok=True)
Path("archive_rpc_feas_diag_output/AAVE_ARCHIVE_RPC_FEASIBILITY_TRANSPORT_DIAGNOSTIC.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
