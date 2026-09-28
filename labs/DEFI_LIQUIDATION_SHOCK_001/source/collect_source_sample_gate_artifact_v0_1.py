#!/usr/bin/env python3
import argparse,io,json,os,urllib.parse,urllib.request,zipfile
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--repository",required=True)
ap.add_argument("--out",required=True)
args=ap.parse_args()

TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
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

NAME="dls-source-cluster-sample-gate-v01"
OUT=Path(args.out);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_MAPPING_SAMPLE_ARTIFACT_SELECTION_RECEIPT_V0.1.json")

def api(url,binary=False):
    h={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-market-mapping-collector/0.1"}
    if TOKEN:h["Authorization"]=f"Bearer {TOKEN}"
    req=urllib.request.Request(url,headers=h)
    with OPENER.open(req,timeout=180) as r:
        raw=r.read()
    return raw if binary else json.loads(raw)

q=urllib.parse.urlencode({"name":NAME,"per_page":100})
obj=api(f"https://api.github.com/repos/{args.repository}/actions/artifacts?{q}")
arts=[a for a in obj.get("artifacts",[]) if a.get("name")==NAME and not a.get("expired")]
arts.sort(key=lambda a:(a.get("created_at") or "",int(a.get("id") or 0)),reverse=True)
errors=[];selected=None
if not arts:
    errors.append({"reason":"sample_gate_artifact_not_found","artifact_name":NAME})
else:
    selected=arts[0]
    raw=api(selected["archive_download_url"],binary=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extractall(OUT)
        files=sorted(z.namelist())
    rp=OUT/"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json"
    cp=OUT/"SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"
    if not rp.exists():errors.append({"reason":"sample_gate_receipt_missing"})
    else:
        sr=json.loads(rp.read_text())
        if sr.get("classification")!="SOURCE_SAMPLE_GATE_PASS":
            errors.append({"reason":"newest_sample_gate_not_pass","classification":sr.get("classification")})
    if not cp.exists():errors.append({"reason":"cluster_census_missing"})

classification="MARKET_MAPPING_SAMPLE_ARTIFACT_SELECTION_PASS" if not errors else "MARKET_MAPPING_SAMPLE_ARTIFACT_SELECTION_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "artifact_name":NAME,
 "selected_artifact":None if selected is None else {
   "id":selected.get("id"),"created_at":selected.get("created_at"),
   "updated_at":selected.get("updated_at"),"size_in_bytes":selected.get("size_in_bytes")
 },
 "selection_reads_market_outcomes":False,
 "error_count":len(errors),"errors":errors,
 "firewall":{"prices":False,"returns":False,"pnl":False,"economic_outcomes":False,
             "protected_market_outcomes_2025_2026":False,"post_outcome_tuning":False,
             "live_trading":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARKET_MAPPING_SAMPLE_ARTIFACT_SELECTION_PASS":raise SystemExit(2)
