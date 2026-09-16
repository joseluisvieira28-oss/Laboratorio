#!/usr/bin/env python3
import csv, io, json, math, os, hashlib, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone, date
from pathlib import Path

LAB = "BTC-OPTIONS-VRP-001"
GATE = "OVRP-DVOL-RV30-SOURCE-001"
START = datetime(2021,4,1,tzinfo=timezone.utc)
END = datetime(2024,12,31,23,59,59,999000,tzinfo=timezone.utc)
OUT = Path("artifacts/btc_options_vrp_source_v01")
OUT.mkdir(parents=True, exist_ok=True)


def get_bytes(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent":"MSEL-Crypto-Lab/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ms(dt):
    return int(dt.timestamp()*1000)


def iso_date_from_ms(x):
    return datetime.fromtimestamp(int(x)/1000, tz=timezone.utc).date().isoformat()


def month_iter(y0,m0,y1,m1):
    y,m=y0,m0
    while (y,m) <= (y1,m1):
        yield y,m
        if m==12: y,m=y+1,1
        else: m+=1

result = {
    "lab_id": LAB,
    "source_gate_id": GATE,
    "classification": None,
    "access_2025": False,
    "access_2026": False,
    "btc_prices_opened": False,
    "future_realized_variance_opened": False,
    "forward_returns_opened": False,
    "pnl_opened": False,
    "deribit": {},
    "binance": {},
    "errors": []
}

# ---- DERIBIT DVOL: source signal only ----
try:
    base = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
    cursor_end = ms(END)
    start_ms = ms(START)
    seen_payload_hashes=[]
    rows=[]
    loops=0
    while True:
        loops += 1
        if loops > 30:
            raise RuntimeError("Deribit pagination loop exceeded 30 pages")
        q = urllib.parse.urlencode({
            "currency":"BTC",
            "start_timestamp":start_ms,
            "end_timestamp":cursor_end,
            "resolution":"1D"
        })
        raw = get_bytes(base+"?"+q)
        seen_payload_hashes.append(hashlib.sha256(raw).hexdigest())
        obj=json.loads(raw.decode("utf-8"))
        if "error" in obj:
            raise RuntimeError(f"Deribit error: {obj['error']}")
        payload=obj.get("result",{})
        data=payload.get("data",[]) or []
        rows.extend(data)
        cont=payload.get("continuation")
        if cont is None:
            break
        cont=int(cont)
        if cont >= cursor_end:
            raise RuntimeError("Deribit continuation did not move backward")
        if cont <= start_ms:
            break
        cursor_end=cont

    norm={}
    for r in rows:
        if not isinstance(r,list) or len(r)!=5:
            raise RuntimeError("Unexpected Deribit candle shape")
        ts=int(r[0])
        d=iso_date_from_ms(ts)
        if d >= "2025-01-01":
            result["access_2025"] = True
            raise RuntimeError("Protected-period Deribit row encountered")
        vals=[float(x) for x in r[1:]]
        if not all(math.isfinite(x) and x>0 for x in vals):
            raise RuntimeError(f"Non-positive/non-finite DVOL candle on {d}")
        # Exact duplicate timestamp must be byte-equivalent at value level.
        if ts in norm and norm[ts] != vals:
            raise RuntimeError(f"Conflicting duplicate Deribit timestamp {ts}")
        norm[ts]=vals

    ordered=sorted(norm.items())
    dates=[iso_date_from_ms(ts) for ts,_ in ordered]
    unique_dates=sorted(set(dates))
    if len(unique_dates) < 1300:
        raise RuntimeError(f"Deribit insufficient daily coverage: {len(unique_dates)}")
    if unique_dates[0] > "2021-04-02":
        raise RuntimeError(f"Deribit starts too late: {unique_dates[0]}")
    if unique_dates[-1] < "2024-12-30":
        raise RuntimeError(f"Deribit ends too early: {unique_dates[-1]}")

    ledger=[]
    for ts,vals in ordered:
        d=iso_date_from_ms(ts)
        if "2021-04-01" <= d <= "2024-12-31":
            ledger.append({"timestamp_ms":ts,"utc_date":d,"open":vals[0],"high":vals[1],"low":vals[2],"close":vals[3]})
    b=("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in ledger)+"\n").encode()
    (OUT/"deribit_dvol_1d.jsonl").write_bytes(b)
    result["deribit"]={
        "pass": True,
        "pages": loops,
        "raw_payload_sha256": seen_payload_hashes,
        "unique_utc_dates": len(set(x["utc_date"] for x in ledger)),
        "first_date": ledger[0]["utc_date"],
        "last_date": ledger[-1]["utc_date"],
        "ledger_sha256": hashlib.sha256(b).hexdigest()
    }
except Exception as e:
    result["deribit"]={"pass":False,"error":repr(e)}
    result["errors"].append("DERIBIT:"+repr(e))

# ---- BINANCE DATA VISION: provenance/timestamps only; never parse OHLC ----
try:
    base="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/"
    manifest=[]
    all_dates=[]
    months=0
    for y,m in month_iter(2021,4,2024,12):
        months += 1
        stem=f"BTCUSDT-1d-{y:04d}-{m:02d}.zip"
        zurl=base+stem
        curl=zurl+".CHECKSUM"
        chk_raw=get_bytes(curl).decode("utf-8",errors="replace").strip()
        expected=chk_raw.split()[0].lower()
        zraw=get_bytes(zurl)
        actual=hashlib.sha256(zraw).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Checksum mismatch {stem}")
        with zipfile.ZipFile(io.BytesIO(zraw)) as zf:
            names=zf.namelist()
            if len(names)!=1:
                raise RuntimeError(f"Unexpected zip members {stem}: {names}")
            text=zf.read(names[0]).decode("utf-8")
        dates=[]
        for row in csv.reader(io.StringIO(text)):
            if not row: continue
            # Inspect timestamp column only. Never convert/read columns 1+.
            ts=int(row[0])
            d=iso_date_from_ms(ts)
            if d >= "2025-01-01":
                result["access_2025"] = True
                raise RuntimeError(f"Protected-period Binance row {d}")
            dates.append(d)
            all_dates.append(d)
        manifest.append({
            "file":stem,
            "archive_sha256":actual,
            "checksum_text_sha256":hashlib.sha256(chk_raw.encode()).hexdigest(),
            "rows":len(dates),
            "first_date":min(dates),
            "last_date":max(dates)
        })

    unique=sorted(set(all_dates))
    expected_dates=[]
    d=START.date()
    while d <= END.date():
        expected_dates.append(d.isoformat())
        d=date.fromordinal(d.toordinal()+1)
    missing=sorted(set(expected_dates)-set(unique))
    extras=sorted(set(unique)-set(expected_dates))
    if months != 45:
        raise RuntimeError(f"Expected 45 months, got {months}")
    if len(unique) != 1371 or missing or extras:
        raise RuntimeError(f"Binance timestamp coverage failure unique={len(unique)} missing={len(missing)} extras={len(extras)}")
    if len(all_dates) != len(unique):
        raise RuntimeError("Duplicate Binance UTC dates")

    mb=("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in manifest)+"\n").encode()
    (OUT/"binance_timestamp_manifest.jsonl").write_bytes(mb)
    result["binance"]={
        "pass":True,
        "months":months,
        "unique_utc_dates":len(unique),
        "first_date":unique[0],
        "last_date":unique[-1],
        "manifest_sha256":hashlib.sha256(mb).hexdigest(),
        "price_columns_inspected":False
    }
except Exception as e:
    result["binance"]={"pass":False,"error":repr(e),"price_columns_inspected":False}
    result["errors"].append("BINANCE:"+repr(e))

if result["access_2025"] or result["access_2026"]:
    result["classification"]="PROVENANCE_FAILURE"
elif result["deribit"].get("pass") and result["binance"].get("pass"):
    result["classification"]="SOURCE_DATA_PASS"
elif result["deribit"].get("pass"):
    result["classification"]="SOURCE_DATA_PARTIAL"
else:
    # Network/auth/schema distinction is preserved in errors; no edge verdict.
    result["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"

out=(json.dumps(result,indent=2,sort_keys=True)+"\n").encode()
(OUT/"source_gate_result.json").write_bytes(out)
print(out.decode())
