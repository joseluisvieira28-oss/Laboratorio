#!/usr/bin/env python3
"""BTC-ONLY one-shot Nov 2026 PAPER signal. No accounts, orders or live trading.

Never run --outcome or query future market data. User must arrange operator trigger.
"""
import asyncio,datetime as dt,json,pathlib,time
import btc_event10m_source_preflight_v04 as pre
from event10m_spot_depth_divergence_v03 import decide
OUT=pathlib.Path("artifacts/btc_event10m_paper_v05")
def ms():return int(time.time()*1000)
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pre.OUT=OUT;pre.RAW=OUT/"raw";pre.RAW.mkdir(parents=True,exist_ok=True)
    # Next UTC 10-minute boundary at least 90 seconds in the future for startup.
    now=ms()
    boundary=((now+90000+599999)//600000)*600000
    output={"study":"BTC_EVENT10M_V05_FROZEN_PROSPECTIVE_PAPER_ONLY",
      "status":"BLOCKED","selected_utc_10m_boundary_ms":boundary,
      "model":"EVENT10M_OKX_SPOT_VS_MEXC_PERP_DIVERGENCE_V03",
      "private_calls_or_orders":0,"actual_event_futures_execution":False,
      "index_event_settlement_parity_proven":False,
      "research_no_money":True,
      "preexpiry_artifact_server_verified":False}
    try:
        if not(dt.datetime(2026,11,1,tzinfo=dt.timezone.utc).timestamp()*1000<=
               boundary<dt.datetime(2026,12,1,tzinfo=dt.timezone.utc).timestamp()*1000):
            raise ValueError("OUTSIDE_FROZEN_NOVEMBER_PAPER_WINDOW")
        src=await pre.collect(target_boundary_ms=boundary)
        output["source_receipt"]=src
        if src["status"]!="FOUR_LEG_ASOF_SOURCE_PASS":
            raise ValueError("CAUSAL_SOURCE_GATES_BLOCKED_"+str(src.get("error") or src.get("source_gates")))
        model=decide("BTC_USDT",src["asof_ms"],src["samples"],src["product"],src["index"])
        output["forecast"]=model
        output["decision_ms"]=model["decision_ms"]
        output["expiry_target_ms"]=model["target_ms"]
        output["status"]="ABSTAIN_PREEXPIRY" if model["side"]=="ABSTAIN" else "PAPER_FORECAST_UNANCHORED"
        output["requires_independent_prepublished_artifact"]=True
        output["no_outcome_opened"]=True
    except Exception as exc:
        output["block_code"]=type(exc).__name__+":"+str(exc)[:220]
    finally:
        output["receipt_saved_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
        (OUT/"decision.json").write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
        print(json.dumps({k:v for k,v in output.items() if k!="source_receipt"},indent=2,sort_keys=True))
    if output["status"]=="BLOCKED":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())
