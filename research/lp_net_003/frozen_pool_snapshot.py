#!/usr/bin/env python3
"""LP-NET-003 future as-of stablecoin-pool selector SOURCE gate.

This is a snapshot + frozen descriptive fee-intensity metric, NOT LP earnings.
Exact 2 known Ethereum v3 DAI/USDC pool contracts; no wallets or orders.
"""
import argparse,hashlib,json,math,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen

POOLS={
 "DAI_USDC_100":{"address":"0x5777d92f208679db4b9778590fa3cab3ac9e2168","fee":0.0001},
 "DAI_USDC_500":{"address":"0x6c6bc977e13df9b0de53b251522280bb72383700","fee":0.0005},
}
ALLOWED=("https://api.geckoterminal.com/api/v2/networks/eth/pools/",
         "https://api.dexscreener.com/latest/dex/pairs/ethereum/",
         "https://coins.llama.fi/prices/current/")
DAI="ethereum:0x6b175474e89094c44da98b954eedeac495271d0f"
USDC="ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

def call(url):
 if not url.startswith(ALLOWED):raise ValueError("Disallowed source")
 req=Request(url,headers={"Accept":"application/json","User-Agent":"LP-NET-003-PIT-RESEARCH/0.1"})
 with urlopen(req,timeout=15) as r:raw=r.read(750000)
 return json.loads(raw),hashlib.sha256(raw).hexdigest()

def positive(x):
 x=float(x)
 if not math.isfinite(x) or x<=0:raise ValueError("invalid positive metric")
 return x

def current_peg(ts):
 src,sha=call("https://coins.llama.fi/prices/current/"+DAI+","+USDC)
 vals={};errors=[]
 for name,key in (("DAI",DAI),("USDC",USDC)):
  a=src.get("coins",{}).get(key)
  if not isinstance(a,dict):errors.append(name+":NO_QUOTE");continue
  try:
   price=positive(a["price"]);qt=int(a["timestamp"])
   if not 0<=ts-qt<=600:raise ValueError("stale or future")
   if a.get("confidence") is not None and float(a["confidence"])<.90:raise ValueError("confidence")
   vals[name]={"price_usd":price,"quote_timestamp":qt,"confidence":a.get("confidence")}
  except (ValueError,TypeError,KeyError) as e:
   errors.append(name+":"+str(e))
 return {"sha256":sha,"values":vals,"errors":errors,"peg_screen_pass":
         not errors and all(.995<=v["price_usd"]<=1.005 for v in vals.values())}

def metrics(name,p):
 address=p["address"]
 gg,gsha=call("https://api.geckoterminal.com/api/v2/networks/eth/pools/"+address)
 dd,dsha=call("https://api.dexscreener.com/latest/dex/pairs/ethereum/"+address)
 a=gg.get("data",{}).get("attributes",{})
 pairs=dd.get("pairs") or []
 d=next((x for x in pairs if x.get("pairAddress","").lower()==address and
          x.get("chainId","").lower() in ("ethereum","eth")),None)
 if a.get("address","").lower()!=address or not d:
  raise ValueError("pool address/chain missing from at least one provider")
 gv=positive(a.get("volume_usd",{}).get("h24"))
 gl=positive(a.get("reserve_in_usd"))
 dv=positive(d.get("volume",{}).get("h24"))
 dl=positive(d.get("liquidity",{}).get("usd"))
 discrepancy_v=abs(gv-dv)/max(gv,dv)
 discrepancy_l=abs(gl-dl)/max(gl,dl)
 coherent=discrepancy_v<=.30 and discrepancy_l<=.30
 proxy=gv*p["fee"]/gl
 return {"pool":name,"address":address,"reported_asof_utc":datetime.now(timezone.utc).isoformat(),
         "declared_nominal_pool_fee":p["fee"],
         "geckoterminal":{"volume_usd_h24":gv,"reserve_usd":gl,"sha256":gsha},
         "dexscreener":{"volume_usd_h24":dv,"reported_liquidity_usd":dl,"sha256":dsha},
         "provider_disagreement_volume_pct":100*discrepancy_v,
         "provider_disagreement_liquidity_pct":100*discrepancy_l,
         "source_consistent":coherent,"nominal_pool_fee_intensity_proxy_per_day":proxy,
         "not_position_lp_apr":True,
         "source_threshold_pass":coherent and gv>=100000 and gl>=1000000,
         "range_liquidity_and_protocol_fee":"UNBOUND",
         "decision":"WATCH_ONLY_NO_LIVE_GO"}

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--output",type=Path,required=True)
 args=parser.parse_args()
 ts=int(time.time())
 out={"study":"LP-NET-003-FROZEN-PIT-SNAPSHOT","captured_at_utc":datetime.fromtimestamp(ts,timezone.utc).isoformat(),
      "snapshot_universe":POOLS,"historical_policy_frozen_before_source_access":True,
      "zero_orders":True,"zero_wallets":True,"capital_chf":0,"economic_verdict":"NO_LIVE_GO",
      "selector_not_live_trading_signal":True,"pool_states":[]}
 try:out["token_peg"]=current_peg(ts)
 except (OSError,ValueError,KeyError,TypeError) as e:
  out["token_peg"]={"peg_screen_pass":False,"error":type(e).__name__+":"+str(e)[:150]}
 for name,p in POOLS.items():
  try:out["pool_states"].append(metrics(name,p))
  except (OSError,ValueError,KeyError,TypeError) as e:
   out["pool_states"].append({"pool":name,"address":p["address"],"decision":"SOURCE_BLOCKED",
                  "reason":type(e).__name__+":"+str(e)[:150]})
  time.sleep(.5)
 eligible=[x for x in out["pool_states"] if x.get("source_threshold_pass") and
           out["token_peg"].get("peg_screen_pass")]
 eligible=sorted(eligible,key=lambda r:(-r["nominal_pool_fee_intensity_proxy_per_day"],r["pool"]))
 out["descriptive_ranking_predeclared"]=[x["pool"] for x in eligible]
 out["strategy_signal"]="NO_TRADE_SOURCE_ONLY_ACTIVE_LIQUIDITY_AND_2026_PROTOCOL_FEE_UNBOUND"
 out["next_gate"]="Uniswap v3 onchain current pool feeProtocol/ticks and per-notional executable LP mint/range risk, plus 7- and 30-day forward independent outcomes"
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
 print(json.dumps({"captured_at":out["captured_at_utc"],
      "pool_statuses":{x["pool"]:x["decision"] for x in out["pool_states"]},
      "peg_pass":out["token_peg"].get("peg_screen_pass"),
      "research_ranked_pool_names":out["descriptive_ranking_predeclared"],
      "economic_verdict":out["economic_verdict"]}))
if __name__=="__main__":main()
