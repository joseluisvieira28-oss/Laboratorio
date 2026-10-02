from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://api.mexc.com/api/v1/contract/kline/index_price"
ASSETS = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT",
    "NVDAUSDT": "NVIDIA_USDT",
    "MUUSDT": "MUSTOCK_USDT",
    "SPCXUSDT": "SPCXSTOCK_USDT",
}
INTERVALS = ("Min1","Min5","Min15","Min30","Min60","Hour4","Day1")
JULY_START = 1782864000
JULY_END = 1782950400  # 24h
SEPT_START = 1788220800
SEPT_END = 1788307200


def get(symbol: str, interval: str, params: dict[str,str]) -> dict:
    q = urllib.parse.urlencode({"interval": interval, **params})
    url = f"{BASE}/{symbol}?{q}"
    req = urllib.request.Request(url, headers={"User-Agent":"crypto-edge-radar/history-transport-probe-v01"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def summarize(payload: dict) -> dict:
    data = payload.get("data") if isinstance(payload,dict) else None
    times = data.get("time",[]) if isinstance(data,dict) else []
    return {
        "success": payload.get("success") if isinstance(payload,dict) else None,
        "code": payload.get("code") if isinstance(payload,dict) else None,
        "message": payload.get("message") if isinstance(payload,dict) else None,
        "rows": len(times) if isinstance(times,list) else None,
        "first_ts": int(times[0]) if isinstance(times,list) and times else None,
        "last_ts": int(times[-1]) if isinstance(times,list) and times else None,
        "prices_reported": False,
    }


def main() -> int:
    out = {
      "probe_id":"MEXC_EVENT_FUTURES_HISTORY_TRANSPORT_PROBE_V0.1",
      "created_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "outcomes_computed":False,
      "prices_reported":False,
      "assets":{},
    }
    for display,symbol in ASSETS.items():
        asset = {}
        for interval in INTERVALS:
            modes = {}
            tests = (
              ("JULY_BOTH", {"start":str(JULY_START),"end":str(JULY_END-60)}),
              ("JULY_END_ONLY", {"end":str(JULY_END-60)}),
              ("SEPT_BOTH", {"start":str(SEPT_START),"end":str(SEPT_END-60)}),
            )
            for name,params in tests:
                try:
                    modes[name]=summarize(get(symbol,interval,params))
                except Exception as e:
                    modes[name]={"error":f"{type(e).__name__}:{e}","prices_reported":False}
                time.sleep(0.12)
            asset[interval]=modes
        out["assets"][display]={"symbol":symbol,"intervals":asset}
    with open("mexc_event_futures_history_transport_probe_v01.json","w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
