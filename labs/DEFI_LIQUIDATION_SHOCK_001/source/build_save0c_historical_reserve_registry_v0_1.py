#!/usr/bin/env python3
import json, os, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

OWNER="solendprotocol"
REPO="solend-sdk"
PATH="src/configs/production.json"
SINCE="2021-12-08T00:00:00Z"
UNTIL="2025-01-01T00:00:00Z"
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_HISTORICAL_RESERVE_REGISTRY_RECEIPT_V0.1.json")
TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

def api(url,retries=8):
    headers={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-save0c-reserve-registry/0.1"}
    if TOKEN:
        headers["Authorization"]=f"Bearer {TOKEN}"
    req=urllib.request.Request(url,headers=headers)
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code in (429,500,502,503,504):
                last={"http":e.code}; time.sleep(min(30,2**i)); continue
            raise RuntimeError(f"github_http_{e.code}:{raw[:500]!r}")
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}; time.sleep(min(30,2**i))
    raise RuntimeError(f"github_transport_exhausted:{last}")

def get_json(url):
    st,h,raw=api(url)
    if st!=200: raise RuntimeError(f"github_status_{st}")
    return json.loads(raw)

def get_text(sha):
    url=f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{sha}/{PATH}"
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-save0c-reserve-registry/0.1"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return r.read().decode("utf-8","replace")

def commits():
    out=[]; page=1
    while True:
        q=urllib.parse.urlencode({"path":PATH,"since":SINCE,"until":UNTIL,"per_page":100,"page":page})
        arr=get_json(f"https://api.github.com/repos/{OWNER}/{REPO}/commits?{q}")
        if not arr: break
        for c in arr:
            out.append({
                "sha":c["sha"],
                "date":c["commit"]["committer"]["date"],
                "message":c["commit"]["message"]
            })
        if len(arr)<100: break
        page+=1
    out.sort(key=lambda x:(x["date"],x["sha"]))
    return out

def parse_snapshot(text,meta):
    obj=json.loads(text)
    errors=[]
    if obj.get("programID")!=PROGRAM:
        errors.append({"reason":"program_id_mismatch","observed":obj.get("programID"),"expected":PROGRAM})

    assets={}
    for a in obj.get("assets") or []:
        sym=a.get("symbol"); mint=a.get("mintAddress"); dec=a.get("decimals")
        if not isinstance(sym,str) or not sym or not isinstance(mint,str) or not mint or not isinstance(dec,int):
            errors.append({"reason":"bad_asset_entry","entry":{"symbol":sym,"mintAddress":mint,"decimals":dec}})
            continue
        pair=(mint,dec)
        if sym in assets and assets[sym]!=pair:
            errors.append({"reason":"same_snapshot_asset_symbol_conflict","symbol":sym,
                           "prior":{"mint":assets[sym][0],"decimals":assets[sym][1]},
                           "new":{"mint":mint,"decimals":dec}})
        assets[sym]=pair

    rows=[]
    for market in obj.get("markets") or []:
        market_addr=market.get("address")
        for r in market.get("reserves") or []:
            sym=r.get("asset"); reserve=r.get("address"); collateral=r.get("collateralMintAddress")
            if not isinstance(reserve,str) or not reserve:
                errors.append({"reason":"bad_reserve_address","asset":sym,"market":market_addr}); continue
            if sym not in assets:
                errors.append({"reason":"reserve_asset_not_in_same_snapshot_assets","reserve":reserve,"asset":sym}); continue
            if not isinstance(collateral,str) or not collateral:
                errors.append({"reason":"bad_collateral_mint","reserve":reserve,"asset":sym}); continue
            mint,dec=assets[sym]
            rows.append({
                "reserve":reserve,
                "asset_symbol":sym,
                "underlying_mint":mint,
                "underlying_decimals":dec,
                "collateral_mint":collateral,
                "market":market_addr,
                "source_commit":meta["sha"],
                "source_date":meta["date"]
            })
    return rows,errors

cs=commits()
errors=[]; observations={}; snapshot_count=0
for c in cs:
    try:
        rows,errs=parse_snapshot(get_text(c["sha"]),c)
        snapshot_count+=1
        errors.extend([{"source_commit":c["sha"],"source_date":c["date"],**e} for e in errs])
    except Exception as e:
        errors.append({"reason":"snapshot_parse_or_fetch_failure","source_commit":c["sha"],
                       "source_date":c["date"],"error":str(e)})
        continue
    for r in rows:
        observations.setdefault(r["reserve"],[]).append(r)

registry={};conflicts=[]
for reserve,obs in sorted(observations.items()):
    identities=sorted({
        (x["underlying_mint"],int(x["underlying_decimals"]),x["collateral_mint"])
        for x in obs
    })
    if len(identities)!=1:
        conflicts.append({
            "reserve":reserve,
            "identities":[{"underlying_mint":a,"underlying_decimals":b,"collateral_mint":c}
                          for a,b,c in identities],
            "source_commits":sorted({x["source_commit"] for x in obs})
        })
        continue
    mint,dec,coll=identities[0]
    registry[reserve]={
        "reserve":reserve,
        "underlying_mint":mint,
        "underlying_decimals":dec,
        "collateral_mint":coll,
        "asset_symbols":sorted({x["asset_symbol"] for x in obs}),
        "markets":sorted({x["market"] for x in obs if x.get("market")}),
        "first_seen_date":min(x["source_date"] for x in obs),
        "last_seen_date":max(x["source_date"] for x in obs),
        "observation_count":len(obs),
        "source_commits":sorted({x["source_commit"] for x in obs})
    }

passed=(len(cs)>0 and snapshot_count==len(cs) and not errors and not conflicts and len(registry)>0)
receipt={
    "schema_version":"0.1",
    "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
    "classification":"SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS" if passed else "SAVE0C_HISTORICAL_RESERVE_REGISTRY_BLOCKED_FAIL_CLOSED",
    "repository":f"{OWNER}/{REPO}",
    "path":PATH,
    "history_since":SINCE,
    "history_until":UNTIL,
    "program_id":PROGRAM,
    "commit_count":len(cs),
    "snapshot_count":snapshot_count,
    "reserve_count":len(registry),
    "registry":registry,
    "conflict_count":len(conflicts),
    "conflicts":conflicts,
    "error_count":len(errors),
    "errors":errors[:200],
    "oracle_fields_read":False,
    "firewall":{
        "prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
        "direction":False,"economic_outcomes":False,"balances":False,"token_amounts":False,
        "token_balance_amounts":False,"protected_market_outcomes_2025_2026":False,
        "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
        "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False
    }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","commit_count","snapshot_count","reserve_count","conflict_count","error_count"]},indent=2))
if not passed:
    raise SystemExit(2)
