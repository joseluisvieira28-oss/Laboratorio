#!/usr/bin/env python3
"""Source-only public BTC futures depth timestamp inventory: no returns or signals."""
import datetime as dt,hashlib,json,pathlib,time,urllib.request
OUT=pathlib.Path("artifacts/btc_event10m_depth_timestamp_v06")
URL="https://contract.mexc.com/api/v1/contract/depth/BTC_USDT?limit=20"
def ms():return int(time.time()*1000)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"BTC_EVENT10M_DEPTH_CLOCK_SOURCE_V06",
      "sources":[],"market_labels_read":0,"trading_or_account_calls":0,
      "causal_depth_clock_status":"NO_UNVERIFIED_PASS"}
    for i in range(3):
        if i:time.sleep(2)
        rec={"snapshot":i}
        try:
            req=urllib.request.Request(URL,headers={"Accept":"application/json",
                 "User-Agent":"CryptoLab-BTC-10m-DepthClock-ReadOnly"})
            with urllib.request.urlopen(req,timeout=15) as rsp:
                b=rsp.read(300001)
            recv=ms()
            if len(b)>300000:raise ValueError("BODY_LIMIT")
            raw=json.loads(b)
            if raw.get("success") is not True or not isinstance(raw.get("data"),dict):
                raise ValueError("DEPTH_RESPONSE_SCHEMA")
            v=raw["data"];stamp=v.get("timestamp")
            rec.update(received_ms=recv,raw_sha256=hashlib.sha256(b).hexdigest(),
                server_timestamp=stamp,type_of_timestamp=type(stamp).__name__,
                age_ms=recv-stamp if type(stamp) is int else None,
                bid_levels=len(v.get("bids") or []),ask_levels=len(v.get("asks") or []),
                status="CLOCK_VALID" if type(stamp) is int and 0<=recv-stamp<=2000
                    else "DEPTH_SOURCE_CLOCK_UNPROVEN")
        except Exception as e:
            rec["status"]="SOURCE_FETCH_BLOCKED"
            rec["error"]=type(e).__name__+":"+str(e)[:200]
        report["sources"].append(rec)
    allvalid=all(x.get("status")=="CLOCK_VALID" for x in report["sources"])
    report["causal_depth_clock_status"]="THREE_RECEIPTS_SERVER_TIMESTAMP_PASS" if allvalid else "CLOCK_NOT_CERTIFIED"
    (OUT/"depth_clock_receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    if not allvalid:raise SystemExit(2)
if __name__=="__main__":main()
