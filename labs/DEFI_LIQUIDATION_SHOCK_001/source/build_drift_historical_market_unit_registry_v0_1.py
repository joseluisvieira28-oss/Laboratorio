#!/usr/bin/env python3
import datetime as dt, json, os, re, urllib.parse, urllib.request, urllib.error, time
from pathlib import Path

OWNER="velocity-exchange"
REPO="protocol-v2"
SINCE="2022-11-04T00:00:00Z"
UNTIL="2025-01-01T00:00:00Z"
SPOT_PATH="sdk/src/constants/spotMarkets.ts"
PERP_PATH="sdk/src/constants/perpMarkets.ts"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_RECEIPT_V0.1.json")
TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

PRECISION_MAP={
 "QUOTE_PRECISION_EXP":6,
 "SPOT_MARKET_BALANCE_PRECISION_EXP":9,
 "LAMPORTS_EXP":9,
 "FIVE":5,"SIX":6,"SEVEN":7,"EIGHT":8,"NINE":9,
}
WRAPPED_SOL="So11111111111111111111111111111111111111112"

def api(url,retries=8):
    headers={"Accept":"application/vnd.github+json","User-Agent":"crypto-lab-dls-drift-market-registry/0.1"}
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
                last={"http":e.code,"body":raw[:300].decode("utf-8","replace")}
                time.sleep(min(30,2**i)); continue
            raise RuntimeError(f"github_http_{e.code}:{raw[:500]!r}")
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(30,2**i))
    raise RuntimeError(f"github_transport_exhausted:{last}")

def get_json(url):
    st,h,raw=api(url)
    if st!=200: raise RuntimeError(f"github_status_{st}")
    return json.loads(raw),h

def get_text(path,sha):
    url=f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{sha}/{path}"
    headers={"User-Agent":"crypto-lab-dls-drift-market-registry/0.1"}
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=90) as r:
        return r.read().decode("utf-8","replace")

def commits_for(path):
    out=[]; page=1
    while True:
        q=urllib.parse.urlencode({"path":path,"since":SINCE,"until":UNTIL,"per_page":100,"page":page})
        obj,h=get_json(f"https://api.github.com/repos/{OWNER}/{REPO}/commits?{q}")
        if not obj: break
        for c in obj:
            out.append({"sha":c["sha"],"date":c["commit"]["committer"]["date"],"message":c["commit"]["message"]})
        if len(obj)<100: break
        page+=1
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
    body=array_body(text,"MainnetSpotMarkets")
    rows=[]
    for b in object_blocks(body):
        idx=grab_int(b,"marketIndex")
        if idx is None:continue
        dec,src=parse_precision_exp(b)
        rows.append({
          "market_index":idx,
          "symbol":grab_str(b,"symbol"),
          "mint":parse_mint(b),
          "decimals":dec,
          "precision_source":src,
          "launch_ts":grab_int(b,"launchTs"),
        })
    return rows

def parse_perp(text):
    body=array_body(text,"MainnetPerpMarkets")
    rows=[]
    for b in object_blocks(body):
        idx=grab_int(b,"marketIndex")
        if idx is None:continue
        rows.append({
          "market_index":idx,
          "symbol":grab_str(b,"symbol"),
          "base_asset_symbol":grab_str(b,"baseAssetSymbol"),
          "launch_ts":grab_int(b,"launchTs"),
        })
    return rows

spot_commits=commits_for(SPOT_PATH)
perp_commits=commits_for(PERP_PATH)
errors=[]
spot_obs={};perp_obs={};parse_stats={"spot_snapshots":0,"perp_snapshots":0}

for c in reversed(spot_commits):
    try:
        rows=parse_spot(get_text(SPOT_PATH,c["sha"]));parse_stats["spot_snapshots"]+=1
    except Exception as e:
        errors.append({"kind":"spot_snapshot_parse","sha":c["sha"],"date":c["date"],"error":str(e)});continue
    for r in rows:
        ent=spot_obs.setdefault(r["market_index"],[])
        ent.append({**r,"sha":c["sha"],"date":c["date"]})

for c in reversed(perp_commits):
    try:
        rows=parse_perp(get_text(PERP_PATH,c["sha"]));parse_stats["perp_snapshots"]+=1
    except Exception as e:
        errors.append({"kind":"perp_snapshot_parse","sha":c["sha"],"date":c["date"],"error":str(e)});continue
    for r in rows:
        ent=perp_obs.setdefault(r["market_index"],[])
        ent.append({**r,"sha":c["sha"],"date":c["date"]})

spot_registry={};spot_conflicts=[]
for idx,obs in sorted(spot_obs.items()):
    pairs=sorted({(x.get("mint"),x.get("decimals")) for x in obs if x.get("mint") and x.get("decimals") is not None})
    unresolved=[x for x in obs if not x.get("mint") or x.get("decimals") is None]
    aliases=sorted({x.get("symbol") for x in obs if x.get("symbol")})
    if len(pairs)!=1:
        spot_conflicts.append({"market_index":idx,"unit_pairs":[{"mint":a,"decimals":b} for a,b in pairs],
                               "unresolved_observation_count":len(unresolved)})
    elif unresolved:
        errors.append({"kind":"spot_unresolved_snapshot_fields","market_index":idx,
                       "unresolved_observation_count":len(unresolved)})
    pair=pairs[0] if len(pairs)==1 else (None,None)
    spot_registry[str(idx)]={
      "market_index":idx,"mint":pair[0],"decimals":pair[1],"aliases":aliases,
      "first_seen_date":min(x["date"] for x in obs),"last_seen_date":max(x["date"] for x in obs),
      "observation_count":len(obs),
      "source_commits":sorted({x["sha"] for x in obs}),
      "launch_ts_values":sorted({x["launch_ts"] for x in obs if x.get("launch_ts") is not None}),
    }

perp_registry={}
for idx,obs in sorted(perp_obs.items()):
    aliases=sorted({x.get("symbol") for x in obs if x.get("symbol")})
    base_aliases=sorted({x.get("base_asset_symbol") for x in obs if x.get("base_asset_symbol")})
    perp_registry[str(idx)]={
      "market_index":idx,"aliases":aliases,"base_asset_aliases":base_aliases,
      "base_precision":1000000000,"base_precision_exp":9,
      "quote_precision":1000000,"quote_precision_exp":6,
      "first_seen_date":min(x["date"] for x in obs),"last_seen_date":max(x["date"] for x in obs),
      "observation_count":len(obs),
      "source_commits":sorted({x["sha"] for x in obs}),
      "launch_ts_values":sorted({x["launch_ts"] for x in obs if x.get("launch_ts") is not None}),
    }

passed=(not errors and not spot_conflicts and len(spot_registry)>0 and len(perp_registry)>0)
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_SOURCE_PASS" if passed else "DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED",
 "repository":f"{OWNER}/{REPO}","history_since":SINCE,"history_until":UNTIL,
 "spot_commit_count":len(spot_commits),"perp_commit_count":len(perp_commits),
 "parse_stats":parse_stats,
 "spot_market_count":len(spot_registry),"perp_market_count":len(perp_registry),
 "spot_registry":spot_registry,"perp_registry":perp_registry,
 "spot_conflict_count":len(spot_conflicts),"spot_conflicts":spot_conflicts,
 "error_count":len(errors),"errors":errors[:200],
 "perp_unit_authority":{
   "base_precision":1000000000,"base_precision_exp":9,
   "quote_precision":1000000,"quote_precision_exp":6,
   "source_commit":"e77518dec79b9ade13680d1d8da1a479aca759b1",
   "numeric_constants_file":"sdk/src/constants/numericConstants.ts",
   "perp_state_file":"programs/drift/src/state/perp_market.rs"
 },
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"token_amounts":False,"requested_max_amount_values":False,
             "limit_price_values":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
             "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
             "account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","spot_commit_count","perp_commit_count",
 "spot_market_count","perp_market_count","spot_conflict_count","error_count"]},indent=2))
if not passed:raise SystemExit(2)
