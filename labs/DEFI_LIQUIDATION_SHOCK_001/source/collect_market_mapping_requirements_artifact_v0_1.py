#!/usr/bin/env python3
import argparse,io,json,os,urllib.parse,urllib.request,zipfile
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--repository",required=True)
ap.add_argument("--out",required=True)
args=ap.parse_args()

TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
NAME="dls-market-mapping-requirements-v01"
OUT=Path(args.out);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_DATA_REQUIREMENTS_ARTIFACT_SELECTION_RECEIPT_V0.1.json")

def api(url,binary=False):
    h={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-market-data-collector/0.1"}
    if TOKEN:h["Authorization"]=f"Bearer {TOKEN}"
    q=urllib.request.Request(url,headers=h)
    with urllib.request.urlopen(q,timeout=180) as r:raw=r.read()
    return raw if binary else json.loads(raw)

q=urllib.parse.urlencode({"name":NAME,"per_page":100})
obj=api(f"https://api.github.com/repos/{args.repository}/actions/artifacts?{q}")
arts=[a for a in obj.get("artifacts",[]) if a.get("name")==NAME and not a.get("expired")]
arts.sort(key=lambda a:(a.get("created_at") or "",int(a.get("id") or 0)),reverse=True)
errors=[];selected=None;actual=None
if not arts:
    errors.append({"reason":"mapping_requirements_artifact_not_found"})
else:
    selected=arts[0]
    raw=api(selected["archive_download_url"],binary=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:z.extractall(OUT)
    rp=OUT/"MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json"
    if not rp.exists():
        errors.append({"reason":"mapping_requirements_receipt_missing"})
    else:
        rr=json.loads(rp.read_text());actual=rr.get("classification")
        if actual!="MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS":
            errors.append({"reason":"mapping_requirements_not_pass","classification":actual})

classification="MARKET_DATA_REQUIREMENTS_ARTIFACT_SELECTION_PASS" if not errors else "MARKET_DATA_REQUIREMENTS_ARTIFACT_SELECTION_BLOCKED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "artifact_name":NAME,
 "selected_artifact":None if selected is None else {"id":selected.get("id"),"created_at":selected.get("created_at"),
                                                     "size_in_bytes":selected.get("size_in_bytes")},
 "requirements_classification":actual,
 "error_count":len(errors),"errors":errors,
 "selection_reads_market_outcomes":False,
 "firewall":{"candles_opened":False,"prices_opened":False,"returns_computed":False,"pnl_computed":False,
             "economic_outcomes_opened":False,"protected_2025_2026_opened":False,"post_outcome_tuning":False,
             "live_trading":False,"merge_main":False}}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARKET_DATA_REQUIREMENTS_ARTIFACT_SELECTION_PASS":raise SystemExit(2)
