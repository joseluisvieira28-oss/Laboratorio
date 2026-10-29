#!/usr/bin/env python3
"""Read-only Tardis raw API: six frozen April 1 minutes, disconnect-marker feasibility."""
import gzip,hashlib,json,urllib.parse,urllib.request,urllib.error
from pathlib import Path
OFFSETS=(0,1,360,720,1200,1439)
BASE="https://api.tardis.dev/v1/data-feeds/bybit"
OUT=Path("artifacts/triple_flow_v02b")
def query(offset):
    params={"from":"2026-04-01","offset":str(offset),"filters":json.dumps(
        [{"channel":"allLiquidation","symbols":["BTCUSDT","ETHUSDT"]}],
        separators=(",",":"))}
    url=BASE+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={
        "User-Agent":"CryptoLab-SourceOnly-NoAuth/0.2b",
        "Accept-Encoding":"gzip","Accept":"application/x-ndjson,application/json,*/*"
    })
    rec={"minute_offset":offset,"request_url":url,"response_bytes":0,
         "raw_sha256":None,"lines":0,"disconnect_markers":0,"valid_payloads":0,
         "status":None,"error":None}
    try:
        with urllib.request.urlopen(req,timeout=25) as rsp:
            rec["status"]=rsp.status
            data=rsp.read(3_000_001)
            encoding=rsp.headers.get("Content-Encoding","")
            rec["content_encoding"]=encoding
        if len(data)>3_000_000:raise RuntimeError("RESPONSE_TOO_LARGE")
        rec["response_bytes"]=len(data)
        rec["raw_sha256"]=hashlib.sha256(data).hexdigest()
        if "gzip" in encoding.lower() or data[:2]==b"\x1f\x8b":
            data=gzip.decompress(data)
        if len(data)>20_000_000:raise RuntimeError("DECOMPRESSED_LIMIT")
        text=data.decode("utf-8")
        rec["decoded_bytes"]=len(data)
        for line in text.split("\n"):
            rec["lines"]+=1
            if not line.strip():
                rec["disconnect_markers"]+=1
                continue
            # Raw feeds prepend collector-local ISO time, then original exchange JSON.
            first,sep,payload=line.partition(" ")
            if not sep or not first.startswith("20"):
                raise RuntimeError("RAW_LINE_FORMAT_UNVERIFIED")
            obj=json.loads(payload)
            if not isinstance(obj,dict):raise RuntimeError("UNEXPECTED_JSON")
            topic=obj.get("topic","")
            if topic and not topic.startswith("allLiquidation."):
                raise RuntimeError("UNEXPECTED_TOPIC")
            rec["valid_payloads"]+=1
        # trailing newline is a terminator and not a disconnect.
        if text.endswith("\n"):rec["disconnect_markers"]-=1
        rec["disconnect_markers"]=max(0,rec["disconnect_markers"])
        rec["gate"]="RAW_MINUTE_READABLE"
    except urllib.error.HTTPError as exc:
        rec["status"]=exc.code;rec["error"]="HTTP_"+str(exc.code)
        rec["gate"]="RAW_ACCESS_BLOCKED"
    except Exception as exc:
        rec["error"]=type(exc).__name__+":"+str(exc)[:160]
        rec["gate"]="RAW_SOURCE_UNVERIFIED"
    return rec
if __name__=="__main__":
    OUT.mkdir(exist_ok=True,parents=True)
    report={"study":"TRIPLE_FLOW_V02B_RAW_DISCONNECT_DISCOVERY",
            "prior_exposed_date":"2026-04-01",
            "offsets":list(OFFSETS),
            "historical_full_day_tested":False,
            "outcomes_opened":0,"economic_edge_claim":False,
            "protected_holdout_accessed":False,
            "private_calls":0,"real_orders":0,
            "receipts":[query(i) for i in OFFSETS]}
    passes=sum(r["gate"]=="RAW_MINUTE_READABLE" for r in report["receipts"])
    report["gate"]="RAW_SAMPLED_MINUTES_READABLE" if passes==len(OFFSETS) else "RAW_SAMPLE_INCOMPLETE"
    report["liquidation_day_continuity_proven"]=False
    report["can_open_market_outcomes"]=False
    (OUT/"raw_disconnect_probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    if report["gate"]!="RAW_SAMPLED_MINUTES_READABLE":
        raise SystemExit(2)
