#!/usr/bin/env python3
"""LP-NET-002 immutable event accounting, offline and deliberately NOT USD PnL.
Input receipts already collected by separate read-only jobs. Uses Decimal.
DO NOT label 1 USD per DAI and USDC as real contemporaneous market prices.
"""
import argparse,hashlib,json
from pathlib import Path
from decimal import Decimal, getcontext
getcontext().prec=50

def words(x):
    if not isinstance(x,str) or not x.startswith("0x") or (len(x)-2)%64:
        raise ValueError("bad ABI")
    return [int(x[i:i+64],16) for i in range(2,len(x),64)]
def amounts(evt):
    w=words(evt["data"])
    if len(w)!=3:raise ValueError("unexpected ABI")
    return (Decimal(w[1])/10**18,Decimal(w[2])/10**6,w[0])

def read(p):
    raw=p.read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def calculate(life,opens,exits,independent):
    oo={int(x["token_id"]):x for x in opens["results"]}
    ee={int(x["token_id"]):x for x in exits["targets"]}
    ii={int(x["token_id"]):x for x in independent["targets"]}
    results=[]
    for t in life["targets"]:
        token=int(t["token_id"]);events=t.get("lp_logs",{}).get("events",[])
        transfers=t.get("transfer_logs",{}).get("events",[])
        if t.get("lp_status")!="INDEXED_LOGS_PRESENT" or t.get("transfer_status")!="INDEXED_LOGS_PRESENT":
            raise ValueError(f"NFT {token}: history not indexed")
        if not t["lp_logs"]["complete_pagination"] or not t["transfer_logs"]["complete_pagination"]:
            raise ValueError("partial pagination")
        if [x["name"] for x in events]!=["IncreaseLiquidity","DecreaseLiquidity","Collect"]:
            raise ValueError(f"NFT {token}: unexpected number/order of manager events")
        if len(transfers)!=1 or int(transfers[0]["topics"][1],16)!=0:
            raise ValueError("unexpected ownership history")
        inc,dec,col=events
        a0,a1,li=amounts(inc)
        b0,b1,ld=amounts(dec)
        c0,c1,_=amounts(col)
        if li!=ld or dec["txhash"]!=col["txhash"] or inc["txhash"]==dec["txhash"]:
            raise ValueError("not a fully withdrawn position")
        if inc["block"]>=dec["block"]:raise ValueError("bad time order")
        opening=oo[token]
        if opening.get("status")!="ENTRY_EVENT_POOL_MINT_AND_TX_GAS_TWO_INDEXERS":
            raise ValueError("no independently confirmed opening")
        if opening["opening_tx_hash"]!=inc["txhash"] or opening["matching_pool_mint_liquidity_raw"]!=li:
            raise ValueError("entry mint identity mismatched")
        exit_check=ee[token]
        proof=[log for s in exit_check["source_attempts"] for log in s.get("logs",[])
             if log.get("receipt_verification",{}).get("status")=="TX_RECEIPT_LOG_VERIFIED_ONE_SOURCE"]
        if len(proof)<2 or set(x["kind"] for x in proof)!={"DecreaseLiquidity","Collect"}:
            raise ValueError("exit receipt logs incomplete")
        independent_exit=ii[token]
        if not independent_exit.get("independent_tx_gas_confirmed") or not independent_exit.get("same_two_manager_log_indexes_confirmed"):
            raise ValueError("independent exit proof missing")
        exit_gas=Decimal(next(x["receipt_verification"]["whole_transaction_fee_eth"] for x in proof))
        entry_gas=Decimal(opening["whole_entry_tx_cost_eth"])
        delta_dai=c0-a0
        delta_usdc=c1-a1
        # This is illustrative equal-peg token accounting, not a historical USD valuation.
        capital=a0+a1
        increment=delta_dai+delta_usdc
        results.append({"token_id":token,"pool_address":opening["matching_pool_address"],
            "mint_block":inc["block"],"withdraw_block":dec["block"],
            "initial_dai":str(a0),"initial_usdc":str(a1),
            "decreased_principal_dai":str(b0),"decreased_principal_usdc":str(b1),
            "collected_dai":str(c0),"collected_usdc":str(c1),
            "collected_less_withdrawn_dai":str(c0-b0),
            "collected_less_withdrawn_usdc":str(c1-b1),
            "wallet_change_dai":str(delta_dai),"wallet_change_usdc":str(delta_usdc),
            "scenario_initial_capital_usd_if_both_1_usd":str(capital),
            "scenario_incremental_usd_vs_hodl_if_both_1_usd_before_gas":str(increment),
            "scenario_incremental_pct_if_both_1_usd_before_gas":str(increment/capital*100),
            "whole_mint_transaction_gas_eth":str(entry_gas),
            "whole_exit_transaction_gas_eth":str(exit_gas),
            "whole_two_transaction_gas_eth":str(entry_gas+exit_gas),
            "tx_gas_attributable_to_position":"UNKNOWN",
            "usd_net_after_costs":None,
            "evidence":"3 one-indexer complete indexed lifecycle streams; two-indexer mint+withdraw tx and logs",
            "economic_verdict":"NO_LIVE_GO"})
    return results

def main():
    p=argparse.ArgumentParser()
    for n in ["lifecycle","opening","exits","independent"]:
        p.add_argument("--"+n,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);a=p.parse_args()
    data={}
    source={}
    for n in ["lifecycle","opening","exits","independent"]:
        data[n],source[n]=read(getattr(a,n))
    out={"study":"LP-NET-002-OFFLINE-NATIVE-TOKEN-LEDGER",
         "evidence_input_sha256":source,"results":[],"economic_verdict":"NO_LIVE_GO",
         "capital_used_chf":0,"orders_sent":0}
    try:
        out["results"]=calculate(data["lifecycle"],data["opening"],data["exits"],data["independent"])
        out["status"]="SOURCE_NATIVE_LEDGER_RECONCILED"
    except (ValueError,KeyError,TypeError,IndexError) as e:
        out["status"]="SOURCE_BLOCKED"
        out["reason"]=type(e).__name__+":"+str(e)
    out["disclaimer"]="Equal-peg scenario only; actual DAI/USDC/ETH historical block marks and attributable gas, unrecorded operations and independent exhaustive lifecycle still require audit; no 2026 OOS economic edge."
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"status":out["status"],"positions":len(out["results"]),"economic_verdict":out["economic_verdict"]}))
if __name__=="__main__":main()
