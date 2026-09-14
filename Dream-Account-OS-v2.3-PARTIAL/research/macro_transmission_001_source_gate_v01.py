#!/usr/bin/env python3
from __future__ import annotations
import csv, io, json, urllib.request, zipfile
from datetime import datetime, timezone

FRED_SERIES = ["DGS2", "DTWEXBGS", "NASDAQCOM"]
FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
FRED_RANGE = "&cosd=2018-01-01&coed=2024-12-31"
BINANCE_BASE = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d"
MONTHS = [f"{y}-{m:02d}" for y in range(2019, 2025) for m in range(1,13)]
END_EXCLUSIVE_MS = int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
START_MS = int(datetime(2019,1,1,tzinfo=timezone.utc).timestamp()*1000)


def get(url: str) -> bytes:
    allowed = url.startswith(FRED_BASE) or url.startswith(BINANCE_BASE + "/")
    if not allowed:
        raise PermissionError(f"network destination not allowed: {url}")
    req = urllib.request.Request(url, headers={"User-Agent":"MACRO-TRANSMISSION-001/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def audit_fred(series: str) -> dict:
    raw = get(FRED_BASE + series + FRED_RANGE)
    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 2:
        raise RuntimeError(f"bad FRED schema {series}")
    header = rows[0]
    if header[0].strip().upper() not in {"DATE","OBSERVATION_DATE"}:
        raise RuntimeError(f"bad FRED date header {series}: {header}")
    dates=[]; valid=0
    for r in rows[1:]:
        if len(r)<2 or not r[0].strip():
            continue
        try:
            d=datetime.strptime(r[0].strip(), "%Y-%m-%d").date()
        except ValueError:
            raise RuntimeError(f"bad FRED date {series}: {r[0]}")
        dates.append(d)
        v=r[1].strip()
        if v not in {"", "."}:
            try: float(v)
            except ValueError: raise RuntimeError(f"bad FRED value {series}: {v}")
            valid += 1
    if len(dates) != len(set(dates)):
        raise RuntimeError(f"duplicate FRED dates {series}")
    if not dates:
        raise RuntimeError(f"empty FRED series {series}")
    return {"series":series,"first_date":str(min(dates)),"last_date":str(max(dates)),"rows":len(dates),"valid_numeric_rows":valid}


def audit_binance_month(ym: str) -> dict:
    filename=f"BTCUSDT-1d-{ym}.zip"
    raw=get(f"{BINANCE_BASE}/{filename}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.endswith('.csv')]
        if len(names)!=1:
            raise RuntimeError(f"unexpected CSV cardinality {ym}")
        b=z.read(names[0])
    rows=list(csv.reader(io.StringIO(b.decode('utf-8-sig'))))
    ts=[]
    for r in rows:
        if not r: continue
        try: t=int(float(r[0]))
        except ValueError: continue
        if t >= 10**14: t //= 1000
        ts.append(t)
    if not ts:
        raise RuntimeError(f"no timestamps {ym}")
    if len(ts)!=len(set(ts)):
        raise RuntimeError(f"duplicate timestamps {ym}")
    if any(t>=END_EXCLUSIVE_MS for t in ts):
        raise RuntimeError(f"protected 2025 timestamp found {ym}")
    return {"month":ym,"rows":len(ts),"first_ms":min(ts),"last_ms":max(ts)}


def main():
    fred=[audit_fred(s) for s in FRED_SERIES]
    for a in fred:
        if a["first_date"] > "2019-01-01" or a["last_date"] < "2024-12-01":
            raise RuntimeError(f"insufficient FRED coverage: {a}")
    btc=[audit_binance_month(m) for m in MONTHS]
    expected=72
    if len(btc)!=expected:
        raise RuntimeError(f"expected {expected} BTC monthly archives, got {len(btc)}")
    if btc[0]["first_ms"] > START_MS or btc[-1]["last_ms"] >= END_EXCLUSIVE_MS:
        raise RuntimeError("BTC coverage boundary violation")
    result={
      "experiment":"MACRO-TRANSMISSION-001",
      "status":"SOURCE_DATA_PASS",
      "outcome_blind":True,
      "fred":fred,
      "btc_months":len(btc),
      "btc_first_ms":btc[0]["first_ms"],
      "btc_last_ms":btc[-1]["last_ms"],
      "computed_macro_signals":False,
      "computed_btc_returns":False,
      "computed_pnl":False,
      "opened_2025":False,
      "opened_2026":False,
      "live_trading":False,
      "exchange_mutation":False
    }
    print("MACRO_TRANSMISSION_SOURCE_GATE="+json.dumps(result,sort_keys=True))

if __name__ == "__main__":
    main()
