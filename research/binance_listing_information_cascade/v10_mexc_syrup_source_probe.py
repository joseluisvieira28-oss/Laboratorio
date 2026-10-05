#!/usr/bin/env python3
# V1.0 source-only feasibility probe for the frozen SYRUP -> MEXC spot binding.
# Emits counts/booleans only. No prices, returns, PnL, MFE, MAE or outcome metrics.

import json
import statistics
import time
import urllib.parse
import urllib.request

T0 = 1746530720814
SYMBOL = "SYRUPUSDT"
BASE = "https://api.mexc.com/api/v3/klines"

def req(url):
    r = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 CryptoLabV10MEXCSource/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.load(x)

def fetch_chunk(a_ms, b_ms):
    q = urllib.parse.urlencode(
        {
            "symbol": SYMBOL,
            "interval": "1m",
            "startTime": int(a_ms),
            "endTime": int(b_ms),
            "limit": 1000,
        }
    )
    j = req(BASE + "?" + q)
    out = []
    for x in j or []:
        try:
            ts = int(x[0])
            volume = float(x[5])
        except (TypeError, ValueError, IndexError):
            continue
        out.append((ts, volume))
    return out

def fetch(a_ms, b_ms):
    # Stay comfortably below the documented 1000-candle ceiling per request.
    out = {}
    cur = a_ms
    span = 899 * 60000
    while cur <= b_ms:
        end = min(cur + span, b_ms)
        for row in fetch_chunk(cur, end):
            out[row[0]] = row
        cur = end + 60000
        time.sleep(0.08)
    return [out[k] for k in sorted(out)]

floor = (T0 // 60000) * 60000
ceil = ((T0 + 59999) // 60000) * 60000
start = floor - 24 * 3600000 - 10 * 60000
finish = floor + 10 * 60000

bars = fetch(start, finish)

witness = [x for x in bars if x[0] <= T0 - 24 * 3600000]
near = [x for x in bars if T0 - 10 * 60000 <= x[0] < floor]
first5 = [x for x in bars if ceil <= x[0] < ceil + 5 * 60000]
hist = [x for x in bars if T0 - 24 * 3600000 <= x[0] < T0 - 3600000]

chunks = [
    sum(y[1] for y in hist[i:i+5])
    for i in range(0, len(hist) - 4, 5)
]
med = statistics.median(chunks) if chunks else None
gaps = sum(
    1 for a, b in zip(hist, hist[1:])
    if b[0] - a[0] != 60000
)

res = {
    "bars": len(bars),
    "witness": len(witness),
    "near": len(near),
    "first5": len(first5),
    "hist_minutes": len(hist),
    "hist_5m_chunks": len(chunks),
    "hist_gaps": gaps,
    "baseline_median_volume_positive": bool(med is not None and med > 0),
    "strict_source_ok": bool(witness and near and len(first5) == 5),
    "volume_metric_possible": bool(
        len(first5) == 5 and chunks and med is not None and med > 0
    ),
}

print("V10_MEXC_SYRUP_SOURCE_BEGIN")
print(json.dumps(res, indent=2, sort_keys=True))
print("V10_MEXC_SYRUP_SOURCE_END")
