#!/usr/bin/env python3
import argparse,io,json,os,urllib.parse,urllib.request,zipfile
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--repository",required=True)
ap.add_argument("--out",required=True)
args=ap.parse_args()

TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
ROOT=Path(args.out);ROOT.mkdir(parents=True,exist_ok=True)
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/FINAL_PRE_DISCOVERY_PREREQUISITE_SELECTION_RECEIPT_V0.1.json")

class StripCrossHostAuthRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req=super().redirect_request(req,fp,code,msg,headers,newurl)
        if new_req is not None:
            old_host=urllib.parse.urlsplit(req.full_url).netloc.lower()
            new_host=urllib.parse.urlsplit(newurl).netloc.lower()
            if old_host!=new_host:
                new_req.remove_header("Authorization")
        return new_req

OPENER=urllib.request.build_opener(StripCrossHostAuthRedirect())

GROUPS={
 "global_field":{
   "artifact":"dls-global-field-coverage-final-v01",
   "receipt":"GLOBAL_FIELD_COVERAGE_FINAL_RECEIPT_V0.1.json",
   "expected":"GLOBAL_FIELD_COVERAGE_FINAL_PASS"},
 "sample_gate":{
   "artifact":"dls-source-cluster-sample-gate-v01",
   "receipt":"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json",
   "expected":"SOURCE_SAMPLE_GATE_PASS"},
 "market_data":{
   "artifact":"dls-market-data-source-feasibility-v01",
   "receipt":"MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json",
   "expected":"MARKET_DATA_SOURCE_PASS"},
}

def api(url,binary=False):
    h={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-pre-discovery-collector/0.1"}
    if TOKEN:h["Authorization"]=f"Bearer {TOKEN}"
    q=urllib.request.Request(url,headers=h)
    with OPENER.open(q,timeout=180) as r:raw=r.read()
    return raw if binary else json.loads(raw)

selected={};errors=[]
for logical,cfg in GROUPS.items():
    q=urllib.parse.urlencode({"name":cfg["artifact"],"per_page":100})
    obj=api(f"https://api.github.com/repos/{args.repository}/actions/artifacts?{q}")
    arts=[a for a in obj.get("artifacts",[]) if a.get("name")==cfg["artifact"] and not a.get("expired")]
    arts.sort(key=lambda a:(a.get("created_at") or "",int(a.get("id") or 0)),reverse=True)
    if not arts:
        errors.append({"reason":"required_artifact_missing","group":logical,"artifact":cfg["artifact"]});continue
    a=arts[0];target=ROOT/logical;target.mkdir(parents=True,exist_ok=True)
    raw=api(a["archive_download_url"],binary=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extractall(target);files=sorted(z.namelist())
    rp=target/cfg["receipt"]
    actual=None
    if not rp.exists():
        errors.append({"reason":"required_receipt_missing","group":logical,"receipt":cfg["receipt"]})
    else:
        objr=json.loads(rp.read_text());actual=objr.get("classification")
        if actual!=cfg["expected"]:
            errors.append({"reason":"prerequisite_not_pass","group":logical,"actual":actual,"expected":cfg["expected"]})
    selected[logical]={"artifact_id":a.get("id"),"artifact_name":a.get("name"),
                       "created_at":a.get("created_at"),"files":files,
                       "receipt":cfg["receipt"],"classification":actual,"expected":cfg["expected"]}

classification="FINAL_PRE_DISCOVERY_PREREQUISITE_SELECTION_PASS" if not errors else "FINAL_PRE_DISCOVERY_PREREQUISITE_SELECTION_BLOCKED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "selection_freeze":"FINAL_PRE_DISCOVERY_PREREQUISITE_ARTIFACT_SELECTION_FREEZE_V0.1.md",
 "selected":selected,"error_count":len(errors),"errors":errors,
 "selection_reads_market_outcomes":False,
 "firewall":{"prices_opened":False,"returns_opened":False,"pnl_opened":False,
             "economic_outcomes_opened":False,"protected_2025_2026_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="FINAL_PRE_DISCOVERY_PREREQUISITE_SELECTION_PASS":raise SystemExit(2)
