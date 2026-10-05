#!/usr/bin/env python3
# V2.0 source-only feasibility probe for frozen SYRUP -> LBANK spot binding.
# Emits counts/booleans only. No prices, returns, PnL, MFE, MAE or outcome metrics.

import json
import statistics
import urllib.parse
import urllib.request

T0 = 1746530720814
SYMBOL = "syrup_usdt"
BASE = "https://api.lbank.info/v2/kline.do"

floor = (T0 // 60000) * 60000
ceil = ((T0 + 59999) // 60000) * 60000
start = floor - 24 * 3600000 - 10 * 60000
finish = floor + 10 * 60000

params = urllib.parse.urlencode({
    "symbol": SYMBOL,
    "size": 2000,
    "type": "minute1",
    "time": start // 1000,
})
req = urllib.request.Request(
    BASE + "?" + params,
    headers={
        "User-Agent": "Mozilla/5.0 CryptoLabV20LBankSource/1.0",
        "Accept": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=30) as r:
    payload = json.load(r)

rows = {}
for x in (payload.get("data") or []):
    try:
        ts_ms = int(float(x[0])) * 1000
        volume = float(x[5])
    except (TypeError, ValueError, IndexError):
        continue
    if start <= ts_ms <= finish:
        rows[ts_ms] = (ts_ms, volume)

bars = [rows[k] for k in sorted(rows)]
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
    "api_result_true": str(payload.get("result")).lower() == "true",
    "api_error_code": payload.get("error_code"),
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

print("V20_LBANK_SYRUP_SOURCE_BEGIN")
print(json.dumps(res, indent=2, sort_keys=True))
print("V20_LBANK_SYRUP_SOURCE_END")

# trigger after workflow registration
