#!/usr/bin/env python3
"""LP-NET-003: frozen historical as-of quotes; no wallets, trades or new parameters.

Exact three NFTs come from the immutable prior LP-NET-002 reconciling original
transaction receipts (two independent indexers) and native token flows.
A per-token quote newer than its Ethereum block or older than 6h is BLOCKED.
Past position results are diagnostic only, NOT prospective pool selection.
"""
import argparse,hashlib,json,math,time
from decimal import Decimal,getcontext
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
getcontext().prec=45
BLOCKSCOUT="https://eth.blockscout.com/api/v2/blocks/"
ROUTESCAN="https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api"
PRICES="https://coins.llama.fi/prices/historical/"
COINS={
 "DAI":"ethereum:0x6b175474e89094c44da98b954eedeac495271d0f",
 "USDC":"ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
 "ETH":"coingecko:ethereum"}
STALE_SECS=6*3600

def fetch(url):
    if not url.startswith((BLOCKSCOUT,ROUTESCAN,PRICES)):
        raise ValueError("Unapproved external host")
    q=Request(url,headers={"Accept":"application/json","User-Agent":"LP-NET-003-RESEARCH-NO-TRADING/0.1"})
    with urlopen(q,timeout=16) as response:raw=response.read(1_000_000)
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def get_block(num):
    bs,bs_sha=fetch(BLOCKSCOUT+str(num))
    if not isinstance(bs,dict) or int(bs.get("height",bs.get("number",0)))!=num:
        raise ValueError("Blockscout block number mismatch")
    raw_ts=bs.get("timestamp")
    if not isinstance(raw_ts,str):raise ValueError("Missing ISO timestamp")
    ts=int(datetime.fromisoformat(raw_ts.replace("Z","+00:00")).timestamp())
    if ts<1_500_000_000:raise ValueError("Implausible block timestamp")
    # Second source optional, never silently claim it if blocked.
    independent={"status":"ROUTESCAN_BLOCK_TIMESTAMP_UNAVAILABLE"}
    try:
        query=urlencode({"module":"proxy","action":"eth_getBlockByNumber",
                         "tag":hex(num),"boolean":"false"})
        rs,rs_sha=fetch(ROUTESCAN+"?"+query)
        block=rs.get("result")
        if isinstance(block,dict):
            rs_ts=int(block["timestamp"],16)
            independent={"status":"MATCHED" if rs_ts==ts else "DISAGREED",
                         "routescan_timestamp":rs_ts,"sha256":rs_sha}
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as e:
        independent={"status":"ROUTESCAN_BLOCK_TIMESTAMP_UNAVAILABLE","error":type(e).__name__}
    if independent["status"]=="DISAGREED":raise ValueError("Independent block timestamps disagree")
    return {"number":num,"timestamp":ts,"blockscout_sha256":bs_sha,
            "timestamp_iso":datetime.fromtimestamp(ts,timezone.utc).isoformat(),
            "timestamp_independent_check":independent}

def get_prices(ts):
    coins=",".join(COINS.values())
    obj,sha=fetch(PRICES+str(ts)+"/"+coins+"?searchWidth=6h")
    raw=obj.get("coins") if isinstance(obj,dict) else None
    if not isinstance(raw,dict):raise ValueError("DefiLlama missing coins object")
    vals={};errors=[]
    for symbol,coinkey in COINS.items():
        v=raw.get(coinkey) or raw.get(coinkey.lower())
        if not isinstance(v,dict):
            errors.append(symbol+":NO_PRICE");continue
        try:
            at=int(v["timestamp"]);amount=Decimal(str(v["price"]))
            confidence=v.get("confidence")
            if not amount.is_finite() or amount<=0:raise ValueError("invalid price")
            if not 0<=ts-at<=STALE_SECS:raise ValueError("future-or-stale quote")
            if confidence is not None and Decimal(str(confidence))<Decimal("0.90"):
                raise ValueError("confidence below 0.90")
            vals[symbol]={"price_usd":str(amount),"quote_timestamp":at,
                "age_seconds":ts-at,"confidence":confidence,
                "source":coinkey}
        except (ValueError,KeyError,TypeError,ArithmeticError) as e:
            errors.append(symbol+":"+str(e)[:90])
    return {"requested_block_timestamp":ts,"provider":"DefiLlama historical",
            "sha256":sha,"prices":vals,"errors":errors,
            "status":"PASS" if not errors else "PRICE_SOURCE_BLOCKED"}

def dec(d,k):return Decimal(d[k])
def compute(p,entry,exit_,pe,px):
    if pe["status"]!="PASS" or px["status"]!="PASS":
        return {"state":"PRICE_SOURCE_BLOCKED","reason":pe["errors"]+px["errors"],
                "real_dollar_result":None}
    v0=sum(dec(p,"initial_"+a.lower())*dec(pe["prices"][a],"price_usd") for a in ("DAI","USDC"))
    hold1=sum(dec(p,"initial_"+a.lower())*dec(px["prices"][a],"price_usd") for a in ("DAI","USDC"))
    v1=sum(dec(p,"exit_"+a.lower())*dec(px["prices"][a],"price_usd") for a in ("DAI","USDC"))
    g0=dec(p,"gas_entry_eth")*dec(pe["prices"]["ETH"],"price_usd")
    g1=dec(p,"gas_exit_eth")*dec(px["prices"]["ETH"],"price_usd")
    delta=v1-hold1
    days=Decimal(exit_["timestamp"]-entry["timestamp"])/Decimal(86400)
    if days<=0:raise ValueError("nonchronological blocks")
    return {"state":"VALUED_SINGLE_PRICE_AGGREGATOR",
       "initial_usd":str(v0),"hold_final_usd":str(hold1),"lp_final_usd_before_gas":str(v1),
       "hold_absolute_pnl_usd":str(hold1-v0),
       "lp_absolute_pnl_usd_full_gas_scenario":str(v1-v0-g0-g1),
       "incremental_gross_vs_hodl_usd":str(delta),
       "mint_whole_tx_gas_usd":str(g0),"exit_whole_tx_gas_usd":str(g1),
       "incremental_net_full_gas_vs_hodl_usd":str(delta-g0-g1),
       "incremental_net_half_gas_vs_hodl_usd":str(delta-(g0+g1)/2),
       "incremental_net_full_gas_pct_initial":str((delta-g0-g1)/v0*100),
       "duration_days":str(days),"attributable_gas":"UNPROVEN_WHOLE_TX_SCENARIO",
       "economic_go":False,"historical_not_oos":True}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--fixture",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    raw=a.fixture.read_bytes();source=json.loads(raw)
    if source.get("source_ledger_sha256")!="2da935a6d5f417994b350f009a6880885577dc06d199f3276629594f45578160":
        raise ValueError("Non-authoritative source ledger")
    out={"study":"LP-NET-003-PIT-HISTORICAL","fixture_sha256":hashlib.sha256(raw).hexdigest(),
       "selected_positions":"PRESELECTED_IN_LP_NET_002_BEFORE_PRICE_LOOKUP",
       "economic_verdict":"NO_LIVE_GO","capital_chf":0,"orders_sent":0,"results":[]}
    for p in source["positions"]:
        row={"nft":p["id"],"source_mint_block":p["mint_block"],"source_exit_block":p["exit_block"]}
        try:
            entry=get_block(p["mint_block"])
            exit_=get_block(p["exit_block"])
            if exit_["timestamp"]!=p["exit_timestamp_expected"]:
                raise ValueError("Block exit timestamp differs from frozen CSV")
            pe=get_prices(entry["timestamp"]);px=get_prices(exit_["timestamp"])
            row.update({"entry_block":entry,"exit_block":exit_,"entry_prices":pe,
                        "exit_prices":px,"valuation":compute(p,entry,exit_,pe,px)})
        except (OSError,ValueError,KeyError,TypeError,RuntimeError) as e:
            row["valuation"]={"state":"SOURCE_BLOCKED","reason":type(e).__name__+":"+str(e)[:140],
                              "real_dollar_result":None}
        out["results"].append(row)
        time.sleep(.5)
    out["priced_nft_count"]=sum(x["valuation"]["state"]=="VALUED_SINGLE_PRICE_AGGREGATOR"
                               for x in out["results"])
    out["disclaimer"]="Not a trading backtest. Historical prices from one aggregator, whole-tx gas allocation, prior retroactively sampled NFTs. Economic promotion forbidden."
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"priced_nft_count":out["priced_nft_count"],
       "statuses":{str(x["nft"]):x["valuation"]["state"] for x in out["results"]},
       "economic_verdict":out["economic_verdict"]},ensure_ascii=False))
if __name__=="__main__":main()
