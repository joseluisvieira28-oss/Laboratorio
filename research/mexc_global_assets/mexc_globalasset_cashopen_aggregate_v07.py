#!/usr/bin/env python3
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_GLOBALASSET_CASHOPEN_RULE_V0.7.json").read_text())
B=json.loads((HERE/"MEXC_GLOBALASSET_CASHOPEN_SOURCE_BINDING_V0.7.json").read_text())
IN=Path("artifacts/mexc_global_assets/cashopen_v07/assets");OUT=Path("artifacts/mexc_global_assets/cashopen_v07")
def eligible(x):
 g=R["scientific_gate"]
 return x["n"]>=g["min_n"] and x["mean_gross_bps"]>0 and x["median_gross_bps"]>0 and x["win_rate"]>g["win_rate_gt"] and all(v is not None and v>0 for v in x["half_means_bps"])
def main():
 rec=[json.loads(p.read_text()) for p in IN.glob("*.json")];expected={x["target"] for x in B["candidates"]}
 if {x["target"] for x in rec}!=expected:raise SystemExit("FAIL_CLOSED_RECEIPT_SET")
 for x in rec:x["pre_holm_eligible"]=eligible(x)
 ordered=sorted(rec,key=lambda x:x["p"] if x["p"] is not None else 1.0);m=len(ordered);still=True
 for rank,x in enumerate(ordered,1):
  c=.05/(m-rank+1);x["holm_rank"]=rank;x["holm_cutoff"]=c;x["holm_reject"]=bool(still and x["p"] is not None and x["p"]<=c)
  if not x["holm_reject"]:still=False
 for x in rec:
  x["scientific_pass"]=bool(x["pre_holm_eligible"] and x["holm_reject"])
  x["net12_survivor"]=bool(x["scientific_pass"] and x["net"]["12"]>0)
  x["net16_survivor"]=bool(x["scientific_pass"] and x["net"]["16"]>0)
  x["verdict"]="ROBUST_API_FEE_SURVIVOR" if x["net16_survivor"] else ("MAKER_MAKER_FEE_SURVIVOR_ONLY" if x["net12_survivor"] else ("SCIENTIFIC_PASS_FEE_BLOCKED" if x["scientific_pass"] else "NO_SCIENTIFIC_PASS"))
 robust=[x for x in rec if x["net16_survivor"]];floor=[x for x in rec if x["net12_survivor"]];sci=[x for x in rec if x["scientific_pass"]]
 overall="ROBUST_API_FEE_SURVIVORS_FOUND__EXECUTION_VALIDATION_REQUIRED" if robust else ("MAKER_MAKER_FEE_SURVIVORS_FOUND" if floor else ("SCIENTIFIC_SURVIVORS_FEE_BLOCKED" if sci else "NO_CASHOPEN_SURVIVOR_AT_FROZEN_V07_GATE"))
 report={"overall_verdict":overall,"scientific_pass_count":len(sci),"net12_survivor_count":len(floor),"net16_survivor_count":len(robust),"results":sorted(rec,key=lambda x:x["target"]),"live_trading_authorized":False}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"MEXC_GLOBALASSET_CASHOPEN_CLOSEOUT_V07.json").write_text(json.dumps(report,indent=2,sort_keys=True))
 top=sorted(rec,key=lambda x:x["mean_gross_bps"] if x["mean_gross_bps"] is not None else -1e9,reverse=True)
 def slim(x):return {k:x[k] for k in ["target","n","wins","win_rate","mean_gross_bps","median_gross_bps","half_means_bps","p","holm_cutoff","scientific_pass","net12_survivor","net16_survivor","verdict"]}
 print(json.dumps({"overall_verdict":overall,"scientific_pass_count":len(sci),"net12_survivor_count":len(floor),"net16_survivor_count":len(robust),"robust_survivors":[slim(x) for x in robust],"top10":[slim(x) for x in top[:10]]},indent=2))
if __name__=="__main__":main()
