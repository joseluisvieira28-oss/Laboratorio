#!/usr/bin/env python3
import json, os, re, urllib.parse, urllib.request, urllib.error, time
from pathlib import Path
from datetime import datetime, timezone

OWNER="velocity-exchange"; REPO="protocol-v2"
SINCE="2022-11-04T00:00:00Z"; UNTIL="2025-01-01T00:00:00Z"
SPOT_PATH="sdk/src/constants/spotMarkets.ts"
PERP_PATH="sdk/src/constants/perpMarkets.ts"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_TEMPORAL_RECEIPT_V0.3.json")
TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

PRECISION_MAP={
 "QUOTE_PRECISION_EXP":6,"SPOT_MARKET_BALANCE_PRECISION_EXP":9,"LAMPORTS_EXP":9,
 "FIVE":5,"SIX":6,"SEVEN":7,"EIGHT":8,"NINE":9,
}
WRAPPED_SOL="So11111111111111111111111111111111111111112"

def api(url,retries=8):
    headers={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-drift-market-registry/0.3"}
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
                last={"http":e.code}; time.sleep(min(30,2**i)); continue
            raise RuntimeError(f"github_http_{e.code}:{raw[:500]!r}")
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}; time.sleep(min(30,2**i))
    raise RuntimeError(f"github_transport_exhausted:{last}")

def get_json(url):
    st,h,raw=api(url)
    if st!=200: raise RuntimeError(f"github_status_{st}")
    return json.loads(raw)

def get_text(path,sha):
    url=f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{sha}/{path}"
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-drift-market-registry/0.3"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return r.read().decode("utf-8","replace")

def commits_for(path):
    out=[]; page=1
    while True:
        q=urllib.parse.urlencode({"path":path,"since":SINCE,"until":UNTIL,"per_page":100,"page":page})
        obj=get_json(f"https://api.github.com/repos/{OWNER}/{REPO}/commits?{q}")
        if not obj: break
        for c in obj:
            out.append({"sha":c["sha"],"date":c["commit"]["committer"]["date"],
                        "message":c["commit"]["message"],"parents":[p["sha"] for p in c.get("parents",[])]})
        if len(obj)<100: break
        page+=1
    # chronological source order; sha tie-break deterministic
    out.sort(key=lambda x:(x["date"],x["sha"]))
    return out

def array_body(text,name):
    marker=f"export const {name}"
    p=text.find(marker)
    if p<0: raise ValueError(f"missing_array:{name}")
    eq=text.find("=",p)
    if eq<0: raise ValueError(f"missing_array_assignment:{name}")
    lb=text.find("[",eq)
    if lb<0: raise ValueError(f"missing_array_open:{name}")
    depth=0; quote=None; esc=False
    for i in range(lb,len(text)):
        ch=text[i]
        if quote:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch==quote: quote=None
            continue
        if ch in ("'","\"", "`"): quote=ch; continue
        if ch=="[": depth+=1
        elif ch=="]":
            depth-=1
            if depth==0: return text[lb+1:i]
    raise ValueError(f"missing_array_close:{name}")

def object_blocks(body):
    out=[]; depth=0; start=None; quote=None; esc=False
    for i,ch in enumerate(body):
        if quote:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch==quote: quote=None
            continue
        if ch in ("'","\"", "`"): quote=ch; continue
        if ch=="{":
            if depth==0:start=i
            depth+=1
        elif ch=="}":
            depth-=1
            if depth==0 and start is not None:
                out.append(body[start:i+1]);start=None
    return out

def grab_int(block,name):
    m=re.search(rf"\b{name}\s*:\s*(\d+)",block)
    return int(m.group(1)) if m else None
def grab_str(block,name):
    m=re.search(rf"\b{name}\s*:\s*['\"]([^'\"]+)['\"]",block)
    return m.group(1) if m else None
def parse_mint(block):
    m=re.search(r"\bmint\s*:\s*new PublicKey\(\s*['\"]([^'\"]+)['\"]\s*\)",block,re.S)
    if m:return m.group(1)
    if re.search(r"\bmint\s*:\s*new PublicKey\(\s*WRAPPED_SOL_MINT\s*\)",block,re.S):return WRAPPED_SOL
    return None
def parse_precision_exp(block):
    m=re.search(r"\bprecisionExp\s*:\s*([A-Z_][A-Z0-9_]*)",block)
    if m:return PRECISION_MAP.get(m.group(1)),m.group(1)
    m=re.search(r"\bprecisionExp\s*:\s*new BN\(\s*(\d+)\s*\)",block)
    if m:return int(m.group(1)),f"literal:{m.group(1)}"
    m=re.search(r"\bprecisionExp\s*:\s*(\d+)",block)
    if m:return int(m.group(1)),f"literal:{m.group(1)}"
    return None,None

def parse_spot(text):
    rows=[]
    for b in object_blocks(array_body(text,"MainnetSpotMarkets")):
        idx=grab_int(b,"marketIndex")
        if idx is None:continue
        dec,src=parse_precision_exp(b)
        rows.append({"market_index":idx,"symbol":grab_str(b,"symbol"),"mint":parse_mint(b),
                     "decimals":dec,"precision_source":src,"launch_ts":grab_int(b,"launchTs")})
    return rows

def parse_perp(text):
    rows=[]
    for b in object_blocks(array_body(text,"MainnetPerpMarkets")):
        idx=grab_int(b,"marketIndex")
        if idx is None:continue
        rows.append({"market_index":idx,"symbol":grab_str(b,"symbol"),
                     "base_asset_symbol":grab_str(b,"baseAssetSymbol"),"launch_ts":grab_int(b,"launchTs")})
    return rows

def compress_spot(obs):
    versions=[]; ambiguity=[]
    by_time={}
    for x in obs:
        by_time.setdefault(x["date"],[]).append(x)
    for t in sorted(by_time):
        group=by_time[t]
        pairs={(x.get("mint"),x.get("decimals")) for x in group}
        if len(pairs)>1:
            ambiguity.append({"date":t,"pairs":[{"mint":a,"decimals":b} for a,b in sorted(pairs,key=str)],
                              "commits":[x["sha"] for x in group]})
            continue
        x=sorted(group,key=lambda y:y["sha"])[-1]
        pair=(x.get("mint"),x.get("decimals"))
        if pair[0] is None or pair[1] is None:
            ambiguity.append({"date":t,"reason":"null_unit_identity","commit":x["sha"],
                              "mint":pair[0],"decimals":pair[1]})
            continue
        if not versions or (versions[-1]["mint"],versions[-1]["decimals"])!=pair:
            versions.append({"effective_from":t,"mint":pair[0],"decimals":pair[1],
                             "precision_source":x.get("precision_source"),"symbol":x.get("symbol"),
                             "launch_ts":x.get("launch_ts"),"source_commit":x["sha"],
                             "source_message":x.get("message")})
        else:
            versions[-1]["last_confirmed_at"]=t
            versions[-1]["last_confirmed_commit"]=x["sha"]
    for i,v in enumerate(versions):
        v["effective_until"]=versions[i+1]["effective_from"] if i+1<len(versions) else UNTIL
    return versions,ambiguity

def compress_perp(obs):
    versions=[]; ambiguity=[]
    by_time={}
    for x in obs: by_time.setdefault(x["date"],[]).append(x)
    for t in sorted(by_time):
        group=by_time[t]
        ids={(x.get("symbol"),x.get("base_asset_symbol"),x.get("launch_ts")) for x in group}
        if len(ids)>1:
            ambiguity.append({"date":t,"identities":[list(i) for i in sorted(ids,key=str)],
                              "commits":[x["sha"] for x in group]})
            continue
        x=sorted(group,key=lambda y:y["sha"])[-1]
        ident=(x.get("symbol"),x.get("base_asset_symbol"),x.get("launch_ts"))
        if not versions or (versions[-1]["symbol"],versions[-1]["base_asset_symbol"],versions[-1]["launch_ts"])!=ident:
            versions.append({"effective_from":t,"symbol":ident[0],"base_asset_symbol":ident[1],"launch_ts":ident[2],
                             "base_precision":1000000000,"base_precision_exp":9,
                             "quote_precision":1000000,"quote_precision_exp":6,
                             "source_commit":x["sha"],"source_message":x.get("message")})
        else:
            versions[-1]["last_confirmed_at"]=t
            versions[-1]["last_confirmed_commit"]=x["sha"]
    for i,v in enumerate(versions):
        v["effective_until"]=versions[i+1]["effective_from"] if i+1<len(versions) else UNTIL
    return versions,ambiguity

spot_commits=commits_for(SPOT_PATH); perp_commits=commits_for(PERP_PATH)
errors=[];spot_obs={};perp_obs={};stats={"spot_snapshots":0,"perp_snapshots":0}
for c in spot_commits:
    try: rows=parse_spot(get_text(SPOT_PATH,c["sha"]));stats["spot_snapshots"]+=1
    except Exception as e:
        errors.append({"kind":"spot_snapshot_parse","sha":c["sha"],"date":c["date"],"error":str(e)});continue
    for r in rows: spot_obs.setdefault(r["market_index"],[]).append({**r,**c})
for c in perp_commits:
    try: rows=parse_perp(get_text(PERP_PATH,c["sha"]));stats["perp_snapshots"]+=1
    except Exception as e:
        errors.append({"kind":"perp_snapshot_parse","sha":c["sha"],"date":c["date"],"error":str(e)});continue
    for r in rows: perp_obs.setdefault(r["market_index"],[]).append({**r,**c})

spot_registry={};perp_registry={};ambiguities=[]
for idx,obs in sorted(spot_obs.items()):
    versions,amb=compress_spot(obs)
    if amb: ambiguities.extend([{"type":"spot","market_index":idx,**x} for x in amb])
    spot_registry[str(idx)]={"market_index":idx,"versions":versions,"version_count":len(versions)}
for idx,obs in sorted(perp_obs.items()):
    versions,amb=compress_perp(obs)
    if amb: ambiguities.extend([{"type":"perp","market_index":idx,**x} for x in amb])
    perp_registry[str(idx)]={"market_index":idx,"versions":versions,"version_count":len(versions)}

# Explicit audit of the known USDC correction lineage.
usdc0=(spot_registry.get("0") or {}).get("versions") or []
known_correction_pass=(
    len(usdc0)>=2 and
    usdc0[0].get("mint")=="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" and usdc0[0].get("decimals")==9 and
    any(v.get("mint")=="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" and v.get("decimals")==6
        and v.get("effective_from")=="2022-11-04T17:07:15Z" for v in usdc0)
)
if not known_correction_pass:
    errors.append({"kind":"known_usdc_precision_lineage_not_recovered","versions":usdc0})

passed=(not errors and not ambiguities and spot_registry and perp_registry)
receipt={
 "schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_TEMPORAL_SOURCE_PASS" if passed else "DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_TEMPORAL_BLOCKED_FAIL_CLOSED",
 "repository":f"{OWNER}/{REPO}","history_since":SINCE,"history_until":UNTIL,
 "spot_commit_count":len(spot_commits),"perp_commit_count":len(perp_commits),"parse_stats":stats,
 "spot_market_count":len(spot_registry),"perp_market_count":len(perp_registry),
 "spot_registry":spot_registry,"perp_registry":perp_registry,
 "known_usdc_index0_correction_recovered":known_correction_pass,
 "ambiguity_count":len(ambiguities),"ambiguities":ambiguities[:100],
 "error_count":len(errors),"errors":errors[:200],
 "perp_unit_authority":{"base_precision":1000000000,"base_precision_exp":9,
                        "quote_precision":1000000,"quote_precision_exp":6,
                        "source_commit":"e77518dec79b9ade13680d1d8da1a479aca759b1"},
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"token_amounts":False,
             "requested_max_amount_values":False,"limit_price_values":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","spot_commit_count","perp_commit_count","spot_market_count",
                                         "perp_market_count","known_usdc_index0_correction_recovered",
                                         "ambiguity_count","error_count"]},indent=2))
if not passed: raise SystemExit(2)
