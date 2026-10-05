#!/usr/bin/env python3
# V0.4.2 source-only Gate historical-archive probe for SYRUP.
# Emits only frozen source-coverage / volume-metric feasibility counts and booleans.
# MUST NOT emit price, return, PnL, MFE or MAE.
import csv
import gzip
import io
import json
import statistics
import urllib.request

T0 = 1746530720814
ARCHIVE_URL = (
    "https://download.gatedata.org/spot/candlesticks_1m/202505/"
    "SYRUP_USDT-202505.csv.gz"
)

def fetch_archive_rows():
    req = urllib.request.Request(
        ARCHIVE_URL,
        headers={
            "User-Agent": "Mozilla/5.0 CryptoLabV042GateArchive/1.0",
            "Accept": "application/gzip,application/octet-stream,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        raw = response.read()

    text = gzip.decompress(raw).decode("utf-8-sig", errors="strict")
    rows = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 2:
            continue
        try:
            ts_ms = int(float(row[0].strip())) * 1000
            volume = float(row[1].strip())
        except (TypeError, ValueError):
            # Allows an optional header without exposing its contents.
            continue
        rows[ts_ms] = (ts_ms, volume)
    return [rows[k] for k in sorted(rows)]

floor = (T0 // 60000) * 60000
ceil = ((T0 + 59999) // 60000) * 60000
window_start = floor - 24 * 3600000 - 10 * 60000
window_end = floor + 10 * 60000

all_rows = fetch_archive_rows()
bars = [x for x in all_rows if window_start <= x[0] <= window_end]

witness = [x for x in bars if x[0] <= T0 - 24 * 3600000]
near = [x for x in bars if T0 - 10 * 60000 <= x[0] < floor]
first5 = [x for x in bars if ceil <= x[0] < ceil + 5 * 60000]
hist = [x for x in bars if T0 - 24 * 3600000 <= x[0] < T0 - 3600000]

chunks = [
    sum(y[1] for y in hist[i : i + 5])
    for i in range(0, len(hist) - 4, 5)
]
med = statistics.median(chunks) if chunks else None
gaps = sum(1 for a, b in zip(hist, hist[1:]) if b[0] - a[0] != 60000)

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

print("V042_GATE_SOURCE_BEGIN")
print(json.dumps(res, indent=2, sort_keys=True))
print("V042_GATE_SOURCE_END")
