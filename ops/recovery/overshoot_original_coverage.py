"""Read-only matrix from immutable V024 artifacts; never generate candles or outcomes."""
import io,json,hashlib,os,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
import requests

ROOT=Path("evidence"); ROOT.mkdir(exist_ok=True)
REPO="joseluisvieira28-oss/Laboratorio"
ARTS=[(11564951470,"b766d27f2785748278352d26c1221a7b044665927517122b6b73408b06052b67"),(11575591555,"50712ef27bac0d6c632ceda3384783a286722b4d193b3cd9c1073ab63063e999")]
receipts=[];manifest=[]
for aid,expected in ARTS:
    r=requests.get(f"https://api.github.com/repos/{REPO}/actions/artifacts/{aid}/zip",headers={"Authorization":"Bearer "+os.environ["GH_TOKEN"],"Accept":"application/vnd.github+json"},allow_redirects=False,timeout=30)
    if r.status_code!=302: raise RuntimeError(f"ARCHIVE_REDIRECT_REQUIRED:{aid}:{r.status_code}")
    target=r.headers["Location"]
    if not target.startswith("https://"): raise RuntimeError("HTTPS_REQUIRED")
    archive=requests.get(target,timeout=60); archive.raise_for_status()
    digest=hashlib.sha256(archive.content).hexdigest()
    if digest!=expected: raise RuntimeError(f"ORIGINAL_ARTIFACT_HASH_MISMATCH:{aid}")
    with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
        names=[n for n in z.namelist() if Path(n).name.startswith("shadow_") and n.endswith(".json")]
        if len(names)!=1: raise RuntimeError("EXACT_ONE_RECEIPT_REQUIRED")
        raw=z.read(names[0]); rec=json.loads(raw)
        if rec["shadow_version"]!="0.2.4" or rec["epoch"]!="V0.2.4_CLEAN_PROSPECTIVE": raise RuntimeError("WRONG_EPOCH")
        receipts.append(rec)
        manifest.append({"artifact_id":aid,"zip_sha256":digest,"receipt_sha256":hashlib.sha256(raw).hexdigest(),"receipt_name":names[0]})
        (ROOT/f"original_{aid}.json").write_bytes(raw)

binding=json.loads(Path("research/mexc_global_assets/MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SOURCE_BINDING_V1.0.json").read_text())
targets=sorted(c["target"] for c in binding["candidates"])
events={}; conflicts=[]; errors=Counter(); transport=[]
for rec in receipts:
    transport.append({"segment":rec["segment"],"started_utc":rec["started_utc"],"transport":rec["transport"]})
    for ev in rec["events"]:
        ts=int(ev["timestamp"])
        for asset in ev["assets"]:
            key=(ts,asset["target"]); encoded=json.dumps(asset,sort_keys=True)
            if key in events and json.dumps(events[key],sort_keys=True)!=encoded: conflicts.append({"timestamp":ts,"target":asset["target"]})
            events.setdefault(key,asset)
admitted=[];last=None
for ts in sorted(set(ts for ts,_ in events)):
    if last is None or ts-last>=600: admitted.append(ts);last=ts
rows=[]
for rec in receipts:
    def instant(hm):
        if "T" in hm:return datetime.fromisoformat(hm.replace("Z","+00:00"))
        return datetime.fromisoformat(rec["date"]+"T"+hm+":00+00:00")
    start=instant(rec["start_utc"]);end=instant(rec["end_utc"])
    indexed=defaultdict(list); global_errors=defaultdict(list)
    for e in rec["errors"]:
        errors[str(e.get("error","UNKNOWN")).split(":")[0]]+=1
        if e.get("minute"):
            key=instant(e["minute"]).replace(second=0,microsecond=0)
            if e.get("target") in targets:indexed[(key,e["target"])].append(e["error"])
            else:global_errors[key].append(e["error"])
    while start<=end:
        for target in targets:
            causes=indexed.get((start,target),[])+global_errors.get(start,[])
            key=(int(start.timestamp()),target)
            if causes:
                status="MISSING_EXACT_SOURCE_POINTS" if any("EXACT_POINTS_MISSING" in x for x in causes) else "INVALID_REPORTED_SOURCE_OR_TIMING"
            elif key in events:
                status="ACCEPTED_FROZEN_COOLDOWN" if key[0] in admitted else "ELIGIBLE_SIGNAL_COOLDOWN_SUPPRESSED"
            else:status="NO_TRIGGER_NO_ERROR_REPORTED__RAW_POINT_PROOF_NOT_RETAINED"
            rows.append({"segment":rec["segment"],"minute_utc":start.isoformat(),"target":target,"status":status,"reported_errors":causes})
        start+=timedelta(minutes=1)
summary={"family_id":"MEXC-GLOBALASSET-INTRADAY-OVERSHOOT-SNAPBACK-V1.0","epoch":"V0.2.4_CLEAN_PROSPECTIVE","original_artifacts":manifest,"expected_asset_minute_cells":len(rows),"frozen_universe_count":len(targets),"status_counts":dict(Counter(x["status"] for x in rows)),"reported_error_counts":dict(errors),"accepted_baskets":len(admitted),"duplicate_asset_event_conflicts":conflicts,"transport":transport,"verdict":"EXECUTION_SOURCE_BLOCKED" if errors or conflicts else "NO_NEW_SCIENTIFIC_VERDICT","new_economics_computed":False,"no_backfill":True,"limitation":"Non-trigger points are not retained in original receipts. No-error cells do not independently prove raw-point availability. Matrix uses original errors/accepted events; no missing candle is fabricated."}
(ROOT/"OVERSHOOT_V024_COVERAGE_MATRIX_2026-10-12.json").write_text(json.dumps(rows,indent=2))
(ROOT/"OVERSHOOT_V024_COVERAGE_SUMMARY_2026-10-12.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,sort_keys=True))
