#!/usr/bin/env python3
import json, os, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

OWNER="solendprotocol"
REPO="solend-sdk"
PATH="src/configs/production.json"
SINCE="2021-12-08T00:00:00Z"
UNTIL="2025-01-01T00:00:00Z"
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_HISTORICAL_RESERVE_REGISTRY_RECEIPT_V0.2.json")
TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

def api(url,retries=8):
    headers={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-save0c-reserve-registry/0.2"}
    if TOKEN: headers["Authorization"]=f"Bearer {TOKEN}"
    req=urllib.request.Request(url,headers=headers)
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code in (429,500,502,503,504):
                last={"http":e.code};time.sleep(min(30,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(30,2**i))
    raise RuntimeError(f"github_transport_exhausted:{last}")

def get_json(url):
    st,h,raw=api(url)
    if st!=200: raise RuntimeError(f"github_status_{st}:{raw[:300]!r}")
    return json.loads(raw)

def commits():
    out=[];page=1
    while True:
        q=urllib.parse.urlencode({"path":PATH,"since":SINCE,"until":UNTIL,"per_page":100,"page":page})
        arr=get_json(f"https://api.github.com/repos/{OWNER}/{REPO}/commits?{q}")
        if not arr:break
        for c in arr:
            out.append({"sha":c["sha"],"date":c["commit"]["committer"]["date"],"message":c["commit"]["message"]})
        if len(arr)<100:break
        page+=1
    out.sort(key=lambda x:(x["date"],x["sha"]))
    return out

def file_at(sha):
    url=f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{sha}/{PATH}"
    st,h,raw=api(url)
    if st==200:return raw.decode("utf-8","replace"),None
    if st!=404: return None,{"reason":"raw_fetch_http","sha":sha,"http_status":st}
    # 404 may be a documented removal. Verify commit diff.
    c=get_json(f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{sha}")
    hit=[f for f in c.get("files",[]) if f.get("filename")==PATH or f.get("previous_filename")==PATH]
    if len(hit)==1 and hit[0].get("status")=="removed":
        return None,{"reason":"documented_source_retirement","sha":sha,
                     "date":c["commit"]["committer"]["date"],
                     "message":c["commit"]["message"],
                     "status":"removed","deletions":hit[0].get("deletions")}
    return None,{"reason":"unexplained_404","sha":sha,"commit_path_hits":hit}

def parse_snapshot(text,meta):
    obj=json.loads(text);errors=[]
    if obj.get("programID")!=PROGRAM:
        errors.append({"reason":"program_id_mismatch","observed":obj.get("programID"),"expected":PROGRAM})
    assets={}
    for a in obj.get("assets") or []:
        sym=a.get("symbol");mint=a.get("mintAddress");dec=a.get("decimals")
        if not isinstance(sym,str) or not sym or not isinstance(mint,str) or not mint or not isinstance(dec,int):
            errors.append({"reason":"bad_asset_entry","entry":{"symbol":sym,"mintAddress":mint,"decimals":dec}});continue
        pair=(mint,dec)
        if sym in assets and assets[sym]!=pair:
            errors.append({"reason":"same_snapshot_asset_symbol_conflict","symbol":sym})
        assets[sym]=pair
    rows=[]
    for market in obj.get("markets") or []:
        market_addr=market.get("address")
        for r in market.get("reserves") or []:
            sym=r.get("asset");reserve=r.get("address");coll=r.get("collateralMintAddress")
            if not isinstance(reserve,str) or not reserve:
                errors.append({"reason":"bad_reserve_address","asset":sym,"market":market_addr});continue
            if sym not in assets:
                errors.append({"reason":"reserve_asset_not_in_same_snapshot_assets","reserve":reserve,"asset":sym});continue
            if not isinstance(coll,str) or not coll:
                errors.append({"reason":"bad_collateral_mint","reserve":reserve,"asset":sym});continue
            mint,dec=assets[sym]
            rows.append({"reserve":reserve,"asset_symbol":sym,"underlying_mint":mint,
                         "underlying_decimals":dec,"collateral_mint":coll,"market":market_addr,
                         "source_commit":meta["sha"],"source_date":meta["date"]})
    return rows,errors

cs=commits();errors=[];retirements=[];observations={};snapshot_count=0
for c in cs:
    text,meta=file_at(c["sha"])
    if meta:
        if meta.get("reason")=="documented_source_retirement":
            retirements.append(meta);continue
        errors.append(meta);continue
    try:
        rows,errs=parse_snapshot(text,c);snapshot_count+=1
        errors.extend([{"source_commit":c["sha"],"source_date":c["date"],**e} for e in errs])
        for r in rows:observations.setdefault(r["reserve"],[]).append(r)
    except Exception as e:
        errors.append({"reason":"snapshot_parse_failure","source_commit":c["sha"],"error":str(e)})

registry={};conflicts=[]
for reserve,obs in sorted(observations.items()):
    ids=sorted({(x["underlying_mint"],int(x["underlying_decimals"]),x["collateral_mint"]) for x in obs})
    if len(ids)!=1:
        conflicts.append({"reserve":reserve,"identities":[{"underlying_mint":a,"underlying_decimals":b,"collateral_mint":c} for a,b,c in ids]});continue
    mint,dec,coll=ids[0]
    registry[reserve]={"reserve":reserve,"underlying_mint":mint,"underlying_decimals":dec,
                       "collateral_mint":coll,"asset_symbols":sorted({x["asset_symbol"] for x in obs}),
                       "markets":sorted({x["market"] for x in obs if x.get("market")}),
                       "first_seen_date":min(x["source_date"] for x in obs),
                       "last_seen_date":max(x["source_date"] for x in obs),
                       "source_commits":sorted({x["source_commit"] for x in obs})}

coverage_end=min((x["date"] for x in retirements),default=None)
if errors or conflicts or not registry:
    classification="SAVE0C_HISTORICAL_RESERVE_REGISTRY_BLOCKED_FAIL_CLOSED"
elif retirements:
    classification="SAVE0C_HISTORICAL_RESERVE_REGISTRY_PARTIAL_SOURCE_COVERAGE"
else:
    classification="SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS"

receipt={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "repository":f"{OWNER}/{REPO}","path":PATH,"history_since":SINCE,"history_until":UNTIL,
 "program_id":PROGRAM,"commit_count":len(cs),"snapshot_count":snapshot_count,"reserve_count":len(registry),
 "registry":registry,"retirement_count":len(retirements),"retirements":retirements,
 "coverage_end":coverage_end,"conflict_count":len(conflicts),"conflicts":conflicts,
 "error_count":len(errors),"errors":errors[:200],"oracle_fields_read":False,
 "applicability_note":"Registry identities are source-defensible only within independently adjudicated temporal/applicability rules; post-retirement events are not silently resolved.",
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"balances":False,"token_amounts":False,
             "token_balance_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","commit_count","snapshot_count","reserve_count",
                                         "retirement_count","coverage_end","conflict_count","error_count"]},indent=2))
if classification=="SAVE0C_HISTORICAL_RESERVE_REGISTRY_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
