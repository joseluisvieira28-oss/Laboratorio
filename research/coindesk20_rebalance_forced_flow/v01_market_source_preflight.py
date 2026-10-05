#!/usr/bin/env python3
# SOURCE-ONLY market coverage preflight for CD20 rebalance study.
# Checks archive/checksum existence only. Does not download/open price values.
import json, urllib.request
from datetime import date, timedelta

EVENTS=[
 ("2024-04","NEAR","ADD","2024-03-19","2024-04-02"),
 ("2024-04","XLM","DELETE","2024-03-19","2024-04-02"),
 ("2024-07","HBAR","ADD","2024-06-18","2024-07-02"),
 ("2024-07","RNDR","ADD","2024-06-18","2024-07-02"),
 ("2024-07","DOGE","DELETE","2024-06-18","2024-07-02"),
 ("2024-07","SHIB","DELETE","2024-06-18","2024-07-02"),
 ("2024-10","XLM","ADD","2024-09-18","2024-10-02"),
 ("2024-10","ATOM","DELETE","2024-09-18","2024-10-02"),
 ("2025-01","SUI","ADD","2025-01-03","2025-01-31"),
 ("2025-01","AAVE","ADD","2025-01-03","2025-01-31"),
 ("2025-01","RENDER","DELETE","2025-01-03","2025-01-31"),
 ("2025-01","ETC","DELETE","2025-01-03","2025-01-31"),
 ("2025-10","CRO","ADD","2025-10-03","2025-10-31"),
 ("2025-10","FIL","DELETE","2025-10-03","2025-10-31"),
]
BASE="https://data.binance.vision/data/spot/daily/klines"
UA={"User-Agent":"Mozilla/5.0 CryptoLabCD20Coverage/1.0"}

def exists(url):
    try:
        req=urllib.request.Request(url,headers=UA)
        with urllib.request.urlopen(req,timeout=20) as r:
            body=r.read(256).decode("utf-8","replace").strip()
            return r.status==200 and len(body)>0
    except Exception:
        return False

def plus2(s):
    y,m,d=map(int,s.split("-"))
    return (date(y,m,d)+timedelta(days=2)).isoformat()

rows=[]
for q,sym,act,pub,impl in EVENTS:
    pair=sym+"USDT"
    d1=plus2(pub)
    d2=impl
    urls=[
      f"{BASE}/{pair}/1m/{pair}-1m-{d1}.zip.CHECKSUM",
      f"{BASE}/{pair}/1m/{pair}-1m-{d2}.zip.CHECKSUM",
    ]
    ok=[exists(u) for u in urls]
    rows.append({"quarter":q,"symbol":sym,"action":act,"publication":pub,
                 "entry_probe_date":d1,"implementation_date":impl,
                 "binance_pair":pair,"entry_checksum":ok[0],
                 "implementation_checksum":ok[1],
                 "binance_core_coverage":all(ok)})
btc_dates=sorted(set([plus2(x[3]) for x in EVENTS]+[x[4] for x in EVENTS]))
btc=all(exists(f"{BASE}/BTCUSDT/1m/BTCUSDT-1m-{d}.zip.CHECKSUM") for d in btc_dates)
res={
 "observations":len(rows),
 "binance_full_observation_coverage":sum(r["binance_core_coverage"] for r in rows),
 "binance_missing":[r for r in rows if not r["binance_core_coverage"]],
 "btc_benchmark_all_dates":btc,
 "rows":rows,
 "market_values_opened":False,
}
print("CD20_MARKET_SOURCE_PREFLIGHT_BEGIN")
print(json.dumps(res,indent=2,sort_keys=True))
print("CD20_MARKET_SOURCE_PREFLIGHT_END")
if not btc:
    raise SystemExit(2)
