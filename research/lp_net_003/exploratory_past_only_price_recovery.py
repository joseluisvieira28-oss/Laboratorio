#!/usr/bin/env python3
"""LP-NET-003-B exploratory, past-only price-source recovery.
No tuning to outcomes: fixed descending as-of query offsets for ALL 3 NFTs.
This is NOT the LP-NET-003 original prospectively frozen quote verdict.
"""
import argparse,hashlib,json,time
from pathlib import Path
from historical_price_markout import get_block,get_prices,compute
OFFSETS_SECONDS=(0,600,1800,3600,7200,14400,21600)
EXPECTED_SOURCE_SHA="2da935a6d5f417994b350f009a6880885577dc06d199f3276629594f45578160"

def recover(original_ts):
 attempts=[]
 for offset in OFFSETS_SECONDS:
  lookup=original_ts-offset
  try:
   quote=get_prices(lookup)
   errors=list(quote.get("errors",[]))
   if quote.get("status")=="PASS":
    # Apply checks again relative to ORIGINAL trade block, not the API search time.
    for symbol,value in quote["prices"].items():
     age=original_ts-int(value["quote_timestamp"])
     if not 0<=age<=6*3600:
      errors.append(symbol+":outside original 6h past-only window")
   attempts.append({"offset_seconds":offset,"looked_up_at":lookup,
       "returned_sha256":quote.get("sha256"),"status":quote.get("status"),
       "errors":errors})
   if quote.get("status")=="PASS" and not errors:
    return {"status":"RECOVERED_PAST_ONLY", "offset_seconds":offset,
      "query_attempts":attempts, "quote":quote}
  except (OSError,ValueError,TypeError,KeyError) as e:
   attempts.append({"offset_seconds":offset,"looked_up_at":lookup,
                    "status":"PROVIDER_ERROR","reason":type(e).__name__+":"+str(e)[:130]})
  time.sleep(.2)
 return {"status":"PRICE_SOURCE_BLOCKED","query_attempts":attempts}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--fixture",required=True,type=Path)
 p.add_argument("--output",required=True,type=Path)
 a=p.parse_args()
 data=a.fixture.read_bytes();source=json.loads(data)
 if source.get("source_ledger_sha256")!=EXPECTED_SOURCE_SHA:raise ValueError("fixture source not frozen")
 out={"study":"LP-NET-003-B","source_fixture_sha256":hashlib.sha256(data).hexdigest(),
     "scope":"EXPLORATORY_QUOTE_RECOVERY_AFTER_V0_1_NOT_PROSPECTIVE",
     "unchanged_original":"LP-NET-003 V0.1 SOURCE_BLOCKED remains authoritative",
     "offsets_before_trade_seconds":OFFSETS_SECONDS,
     "capital_chf":0,"orders_sent":0,"economic_verdict":"NO_LIVE_GO","results":[]}
 for pos in source["positions"]:
  rec={"nft":pos["id"]}
  try:
   entry=get_block(pos["mint_block"]);exit_=get_block(pos["exit_block"])
   if exit_["timestamp"]!=pos["exit_timestamp_expected"]:raise ValueError("exit timestamp mismatch")
   ep=recover(entry["timestamp"]);xp=recover(exit_["timestamp"])
   rec.update({"entry_source":ep,"exit_source":xp})
   if ep["status"]=="RECOVERED_PAST_ONLY" and xp["status"]=="RECOVERED_PAST_ONLY":
    rec["valuation"]=compute(pos,entry,exit_,ep["quote"],xp["quote"])
    rec["valuation"]["economic_go"]=False
    rec["valuation"]["recover_label"]="EXPLORATORY_NOT_ORIGINAL_PROTOCOL"
   else:rec["valuation"]={"state":"PRICE_SOURCE_BLOCKED","usd_net":None}
  except (OSError,ValueError,TypeError,KeyError) as e:
   rec["valuation"]={"state":"SOURCE_BLOCKED","reason":type(e).__name__+":"+str(e)[:150]}
  out["results"].append(rec)
 out["diagnostic_priced_nfts"]=sum(x["valuation"].get("state")=="VALUED_SINGLE_PRICE_AGGREGATOR" for x in out["results"])
 out["no_oos_claim"]=True
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
 print(json.dumps({"exploratory_priced_nfts":out["diagnostic_priced_nfts"],
   "statuses":{str(x["nft"]):x["valuation"].get("state") for x in out["results"]},
   "economic_verdict":out["economic_verdict"]},ensure_ascii=False))
if __name__=="__main__":main()
