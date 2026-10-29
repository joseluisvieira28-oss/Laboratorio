#!/usr/bin/env python3
"""Source-only 4 x 20s intraday receiver freshness snapshots, no outcomes."""
import datetime as dt,json,pathlib,time
from zoneinfo import ZoneInfo
import nvda_cash_ref_fresh_v02 as source
OUT=pathlib.Path("artifacts/nvda_cash_ref_event10m_fresh_v03")
OUT.mkdir(parents=True,exist_ok=True)
def main():
    now=dt.datetime.now(dt.timezone.utc)
    ny=now.astimezone(ZoneInfo("America/New_York"))
    minutes=ny.hour*60+ny.minute
    rep={"lab":"NVDA_CASH_REF_EVENT10M_FRESHNESS_4SHOT_V03",
         "started_utc":now.isoformat(),"ny_market_clock":ny.isoformat(),
         "snapshots":[],"samples_expected":4,"sample_interval_seconds":20,
         "price_returns_or_labels_opened":0,"model_signal_generated":False,
         "old_nvda_forward_still_sealed":True,"orders":0,"gate":"STARTING"}
    try:
        if not(ny.weekday()<5 and 580<=minutes<=950):
            raise RuntimeError("WRONG_CASH_SESSION")
        for i in range(4):
            record={"sample":i,"received_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
                    "feeds":[source.yahoo(),source.mexc()]}
            rep["snapshots"].append(record)
            for x in record["feeds"]:
                age=x["close_freshness_seconds"]
                if not 0<=age<=120:raise RuntimeError("STALE_FEED_"+str(x["provider"])+"_"+str(age))
            print("SOURCE_ONLY_SAMPLE",i,{x["provider"]:x["close_freshness_seconds"] for x in record["feeds"]},flush=True)
            if i<3:time.sleep(20)
        for idx in (0,1):
            times={s["feeds"][idx]["last_completed_candle_start_utc"] for s in rep["snapshots"]}
            if len(times)<2:raise RuntimeError("NO_PROSPECTIVE_MINUTE_PROGRESS_"+str(idx))
        rep["gate"]="FOUR_SAMPLE_LIVE_PUBLIC_SOURCE_FRESHNESS_PASS__ASOF_UNCERTIFIED"
    except Exception as e:
        rep["gate"]="SOURCE_FRESHNESS_INCOMPLETE"
        rep["error"]=type(e).__name__+":"+str(e)[:200]
        raise
    finally:
        rep["finished_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
        (OUT/"four_sample_receipt.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"gate":rep["gate"],"samples":len(rep["snapshots"]),
          "age_seconds":[[x["close_freshness_seconds"] for x in row["feeds"]]
                         for row in rep["snapshots"]],
          "error":rep.get("error")},indent=2),flush=True)
if __name__=="__main__":main()
