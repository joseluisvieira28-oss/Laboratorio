#!/usr/bin/env python3
import argparse, json, os, urllib.parse, urllib.request, urllib.error, zipfile, io
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--repository",required=True)
ap.add_argument("--out",required=True)
args=ap.parse_args()

TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUTROOT=Path(args.out)
OUTROOT.mkdir(parents=True,exist_ok=True)
MANIFEST=Path("labs/DEFI_LIQUIDATION_SHOCK_001/GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_RECEIPT_V0.1.json")

GROUPS={
 "marginfi_save0c_field":["dls-marginfi-save0c-field-enrichment-population-v01"],
 "kamino_save11_field":["dls-kamino-save11-field-enrichment-population-v01"],
 "drift_field_and_units":["dls-drift-field-unit-final-v03"],
 "kamino_save11_units":["dls-kamino-save11-unit-metadata-population-v01"],
 "save0c_units":[
   "dls-save0c-unit-metadata-source-completion-v03",
   "dls-save0c-unit-metadata-source-completion-v02",
   "dls-save0c-unit-metadata-population-v01"
 ],
 "marginfi_units":[
   "dls-marginfi-bank-unit-source-completion-v02",
   "dls-marginfi-bank-unit-registry-v01"
 ],
}

def api(url):
    headers={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-global-field-finalizer/0.1"}
    if TOKEN: headers["Authorization"]=f"Bearer {TOKEN}"
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=90) as r:
        return json.loads(r.read())

def download(url):
    headers={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-global-field-finalizer/0.1"}
    if TOKEN: headers["Authorization"]=f"Bearer {TOKEN}"
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=180) as r:
        return r.read()

def candidates(name):
    q=urllib.parse.urlencode({"name":name,"per_page":100})
    obj=api(f"https://api.github.com/repos/{args.repository}/actions/artifacts?{q}")
    arts=[a for a in (obj.get("artifacts") or []) if a.get("name")==name and not a.get("expired")]
    arts.sort(key=lambda a:(a.get("created_at") or "",int(a.get("id") or 0)),reverse=True)
    return arts

selected={}; errors=[]
for logical,names in GROUPS.items():
    chosen=None
    for name in names:
        arts=candidates(name)
        if arts:
            chosen=arts[0]
            break
    if not chosen:
        errors.append({"reason":"required_artifact_not_found","logical_group":logical,"candidate_names":names})
        continue
    raw=download(chosen["archive_download_url"])
    target=OUTROOT/logical
    target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extractall(target)
        files=sorted(z.namelist())
    selected[logical]={
      "artifact_id":chosen["id"],
      "artifact_name":chosen["name"],
      "created_at":chosen.get("created_at"),
      "updated_at":chosen.get("updated_at"),
      "size_in_bytes":chosen.get("size_in_bytes"),
      "files":files
    }

classification="GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_PASS" if not errors and len(selected)==len(GROUPS) else "GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,
 "selection_freeze":"GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_FREEZE_V0.1.md",
 "repository":args.repository,
 "selected":selected,
 "error_count":len(errors),"errors":errors,
 "selection_reads_receipt_classifications":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_amounts":False,"requested_amount_values":False,
             "realized_transfer_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
MANIFEST.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_PASS":
    raise SystemExit(2)
