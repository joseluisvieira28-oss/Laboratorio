#!/usr/bin/env python3
"""Frozen MU cash vs MUSTOCK 10-minute 24-slot historical index-proxy only."""
import collections,datetime as dt,json,math,pathlib
import mu_cash_source_v01 as gate
OUT=pathlib.Path("artifacts/mu_event10m_transfer_v01")
PIN={
"MU_CASH":{"2026-10-28":"75507bd294f80b45d99c4fbc8fe3abddd075f81c67dac38d0b741ed5920c6fbf","2026-10-29":"c11671c50dabed40ce0e3a7800740f3aba42277cdb78fb75a141c49c1fcb7ab9"},
"2026-10-28":{"2026-10-28":"1b28e0a2b6db3e9b921b8d9daa441e9653444023082aed367c5c56df7410fde5"},
"2026-10-29":{"2026-10-29":"3043c944357dcdd757f2b35178d200a362ee80a81dc63a9d6135d2cdb903264f"}
}
def fetch_fixed():
    prices={};receipts={}
    for name,url in gate.urls().items():
        response,raw_hash=gate.get(url)
        times,opens,closes=gate.vectors(response,name)
        for d in gate.DAYS if name=="MU_CASH" else (name,):
            needed=gate.needed(d)[0 if name=="MU_CASH" else 1]
            sha=gate.canon(times,opens,closes,needed)["sha256"]
            if sha!=PIN[name][d]:raise RuntimeError("IMMUTABLE_PRICE_HASH_CHANGED_"+name+"_"+d)
        rows={}
        for t,o,c in zip(times,opens,closes):
            try:t=int(t)
            except (ValueError,TypeError):continue
            if t in rows:raise ValueError("DUPLICATE_TIME")
            rows[t]=(o,c)
        prices[name]=rows
        receipts[name]={"url":url,"full_raw_sha256":raw_hash,
                         "pinned_feature_canonical_by_day":PIN[name]}
    return prices,receipts
def p(t,rows,which):
    if t not in rows:raise ValueError("NEEDED_BAR_MISSING")
    try:v=float(rows[t][0 if which=="open" else 1])
    except (ValueError,TypeError):raise ValueError("BAD_BAR_PRICE")
    if not(math.isfinite(v) and v>0):raise ValueError("NONPOSITIVE_BAR_PRICE")
    return v
def predict(c0,c1,i0,i1):
    cash_bps=10000*(c1/c0-1)
    index_bps=10000*(i1/i0-1)
    gap=cash_bps-index_bps
    eligible=abs(cash_bps)>=10 and abs(gap)>=5 and cash_bps*gap>0
    side=("UP" if cash_bps>0 else "DOWN") if eligible else "ABSTAIN"
    cash_only=("UP" if cash_bps>0 else "DOWN") if abs(cash_bps)>=10 else "ABSTAIN"
    return side,cash_only,cash_bps,index_bps,gap
def classify(side,start,end):
    if side=="ABSTAIN":return "ABSTAIN"
    if end==start:return "TIE"
    return "WIN" if (end>start)==(side=="UP") else "LOSS"
def summarize(rows,key):
    counted=[x for x in rows if x[key]!="ABSTAIN"]
    v=collections.Counter(x[key+"_outcome"] for x in counted)
    n=len(counted);w=v["WIN"];loss=v["LOSS"];ties=v["TIE"]
    return {"n":n,"win":w,"loss":loss,"tie":ties,
        "winrate_nontie":w/(w+loss) if w+loss else None,
        "q80_hypothetical_unit_EV":(0.8*w-loss)/n if n else None,
        "q85_sensitivity_unit_EV":(0.85*w-loss)/n if n else None}
def evaluation(prices):
    cash=prices["MU_CASH"];records=[]
    for day in gate.DAYS:
        index=prices[day]
        for t in gate.slots(day):
            side,only,cr,ir,gap=predict(p(t-240,cash,"close"),p(t-60,cash,"close"),
                                       p(t-240,index,"close"),p(t-60,index,"close"))
            start=p(t,index,"open");end=p(t+600,index,"open")
            record={"day":day,"slot_utc":dt.datetime.fromtimestamp(t,dt.timezone.utc).isoformat(),
              "hypothetical_decision_utc":dt.datetime.fromtimestamp(t+10,dt.timezone.utc).isoformat(),
              "horizon_seconds":600,"cash_3m_bps":cr,"index_3m_bps":ir,"gap_bps":gap,
              "index_minute_boundary_entry_proxy":start,"index_minute_boundary_expiry_proxy":end,
              "signal":side,"cash_only":only,"always_up":"UP","always_down":"DOWN"}
            for k in ("signal","cash_only","always_up","always_down"):
                record[k+"_outcome"]=classify(record[k],start,end)
            records.append(record)
    if len(records)!=24:raise ValueError("24_SLOTS_NOT_MET")
    return records
def report_group(rows):
    data={k:summarize(rows,k) for k in ("signal","cash_only","always_up","always_down")}
    data["abstentions"]=sum(x["signal"]=="ABSTAIN" for x in rows)
    data["matched_candidate_always_up"]=summarize(
        [x for x in rows if x["signal"]!="ABSTAIN"],"always_up")
    data["matched_candidate_cash_only"]=summarize(
        [x for x in rows if x["signal"]!="ABSTAIN"],"cash_only")
    return data
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"MU_MUSTOCK_EVENT10M_TWO_DAY_TRANSFER_DISCOVERY_V01",
      "gate":"BLOCKED","signals":[],"no_old_nvda_forward_access":True,
      "no_september_holdout_access":True,"no_trading":True,
      "historical_event_futures_payout":"UNKNOWN",
      "event_futures_server_entry_and_settlement_price":"NOT_OBSERVED",
      "model_rule":"UNCHANGED_FROZEN_NVDA_10BPS_CASH_5BPS_GAP",
      "actual_event_return_claim":False,
      "economic_verdict":"DISCOVERY_PROXY_ONLY_UNCERTIFIED"}
    try:
        prices,receipts=fetch_fixed()
        report["source_receipts"]=receipts
        rows=evaluation(prices)
        report["signals"]=rows
        report["summary"]=report_group(rows)
        report["by_day"]={day:report_group([x for x in rows if x["day"]==day])
                          for day in gate.DAYS}
        report["gate"]="24_FROZEN_SLOTS_COMPLETED"
    except Exception as e:
        report["error"]=type(e).__name__+":"+str(e)[:220]
        raise
    finally:
        (OUT/"historical_discovery.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="signals"},indent=2),flush=True)
if __name__=="__main__":main()
