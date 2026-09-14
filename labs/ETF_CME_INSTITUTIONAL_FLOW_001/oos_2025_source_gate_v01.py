#!/usr/bin/env python3
import csv, hashlib, io, json, os, re, sys, urllib.parse, urllib.request, zipfile
from datetime import datetime

LAB="ETF-CME-INSTFLOW-001"
DATASET="6dca-aqww"
CODE="133741"
CFTC_BASE=f"https://publicreporting.cftc.gov/resource/{DATASET}.csv"
OUT=os.environ.get("OUT_DIR","artifacts/etf_cme_oos_2025_source_gate_v01")
os.makedirs(OUT,exist_ok=True)
issues=[]

# Fetch one prior-state row plus all 2025 CFTC observations. No outcomes are computed here.
where=f"cftc_contract_market_code='{CODE}' AND report_date_as_yyyy_mm_dd between '2024-12-01T00:00:00.000' and '2025-12-31T23:59:59.999'"
params={"$limit":"5000","$order":"report_date_as_yyyy_mm_dd ASC","$where":where}
url=CFTC_BASE+"?"+urllib.parse.urlencode(params)
req=urllib.request.Request(url,headers={"User-Agent":"ETF-CME-INSTFLOW-001-OOS-2025/0.1 source-audit"})
with urllib.request.urlopen(req,timeout=120) as r: cftc_raw=r.read()
open(os.path.join(OUT,"cftc_133741_2024prior_2025.csv"),"wb").write(cftc_raw)
cftc_sha=hashlib.sha256(cftc_raw).hexdigest()
rows=list(csv.DictReader(io.StringIO(cftc_raw.decode("utf-8-sig"))))
required=["report_date_as_yyyy_mm_dd","yyyy_report_week_ww","cftc_contract_market_code","open_interest_all","noncomm_positions_long_all","noncomm_positions_short_all"]
fields=list(rows[0].keys()) if rows else []
missing=[f for f in required if f not in fields]
if missing: issues.append({"type":"CFTC_SCHEMA_MISSING_FIELDS","fields":missing})
parsed=[]
for i,row in enumerate(rows,1):
    try:
        d=datetime.fromisoformat(row["report_date_as_yyyy_mm_dd"].replace("Z","+00:00")).date()
        m=re.fullmatch(r"(\d{4}) Report Week (\d{2})",row["yyyy_report_week_ww"].strip())
        if not m: raise ValueError("invalid report week label")
        ry,rw=int(m.group(1)),int(m.group(2))
        code=row["cftc_contract_market_code"].strip(); oi=int(float(row["open_interest_all"])); nl=int(float(row["noncomm_positions_long_all"])); ns=int(float(row["noncomm_positions_short_all"]))
    except Exception as e:
        issues.append({"type":"CFTC_PARSE_FAILURE","row":i,"error":str(e)}); continue
    if code!=CODE: issues.append({"type":"WRONG_MARKET_CODE","row":i,"value":code})
    if oi<=0 or nl<0 or ns<0: issues.append({"type":"INVALID_POSITION_FIELDS","row":i})
    if d.year not in (2024,2025): issues.append({"type":"PROTECTED_PERIOD_ACCESS","date":d.isoformat()})
    parsed.append((d,ry,rw,oi,nl,ns))
rows_2025=[x for x in parsed if x[0].year==2025]
rows_2024=[x for x in parsed if x[0].year==2024]
if len(rows_2025)<40: issues.append({"type":"INSUFFICIENT_2025_CFTC_SAMPLE","rows":len(rows_2025),"minimum":40})
if not rows_2024: issues.append({"type":"MISSING_PRIOR_STATE_ROW"})
# Keep only the immediately preceding 2024 observation as prior state.
prior=max(rows_2024,key=lambda x:x[0]) if rows_2024 else None
seq=([prior] if prior else [])+rows_2025
week_gaps=[]
for a,b in zip(seq,seq[1:]):
    _,ay,aw,*_=a; _,by,bw,*_=b
    ok=(by==ay and bw==aw+1) or (by==ay+1 and bw==1 and aw in (52,53))
    if not ok: week_gaps.append({"from":f"{ay:04d}-{aw:02d}","to":f"{by:04d}-{bw:02d}"})
if week_gaps: issues.append({"type":"MISSING_REPORT_WEEK_SEQUENCE","gaps":week_gaps})
if len({x[0] for x in rows_2025})!=len(rows_2025): issues.append({"type":"DUPLICATE_2025_REPORT_DATE"})

# Fetch official Binance Vision monthly BTCUSDT 1d archives for 2025 only.
btc_dates={}; btc_month_sha={}; btc_archive_sha=[]
for month in range(1,13):
    ym=f"2025-{month:02d}"
    burl=f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-{ym}.zip"
    try:
        breq=urllib.request.Request(burl,headers={"User-Agent":"ETF-CME-INSTFLOW-001-OOS-2025/0.1 source-audit"})
        with urllib.request.urlopen(breq,timeout=120) as r: braw=r.read()
    except Exception as e:
        issues.append({"type":"BINANCE_ARCHIVE_FETCH_FAILURE","month":ym,"error":str(e)}); continue
    bsha=hashlib.sha256(braw).hexdigest(); btc_month_sha[ym]=bsha; btc_archive_sha.append(bsha)
    open(os.path.join(OUT,f"BTCUSDT-1d-{ym}.zip"),"wb").write(braw)
    try:
        z=zipfile.ZipFile(io.BytesIO(braw)); names=z.namelist();
        if len(names)!=1: raise ValueError(f"expected 1 csv, got {len(names)}")
        txt=z.read(names[0]).decode("utf-8")
        for j,row in enumerate(csv.reader(io.StringIO(txt)),1):
            if not row: continue
            try:
                ts=int(row[0]); open_px=float(row[1])
                sec=ts/1_000_000 if ts>10**14 else ts/1000
                d=datetime.utcfromtimestamp(sec).date()
            except Exception as e:
                issues.append({"type":"BINANCE_PARSE_FAILURE","month":ym,"row":j,"error":str(e)}); continue
            if d.year!=2025: issues.append({"type":"BINANCE_PROTECTED_PERIOD_ACCESS","date":d.isoformat()})
            if d in btc_dates: issues.append({"type":"BINANCE_DUPLICATE_DATE","date":d.isoformat()})
            btc_dates[d]=open_px
    except Exception as e:
        issues.append({"type":"BINANCE_ARCHIVE_PARSE_FAILURE","month":ym,"error":str(e)})

expected_days=365
if len(btc_dates)!=expected_days:
    issues.append({"type":"BTC_DAILY_COVERAGE_MISMATCH","rows":len(btc_dates),"expected":expected_days})
if btc_dates:
    if min(btc_dates).isoformat()!="2025-01-01": issues.append({"type":"BTC_START_MISMATCH","date":min(btc_dates).isoformat()})
    if max(btc_dates).isoformat()!="2025-12-31": issues.append({"type":"BTC_END_MISMATCH","date":max(btc_dates).isoformat()})

status="SOURCE_DATA_GATE_PASS" if not issues else "SOURCE_DATA_GATE_BLOCKED"
receipt={
  "lab":LAB,"replication_id":"ETF-CME-INSTFLOW-001-OOS-2025-V0.1","stage":"2025_OOS_SOURCE_DATA_GATE_ONLY","status":status,
  "cftc":{"dataset_id":DATASET,"contract_code":CODE,"raw_sha256":cftc_sha,"prior_state_date":prior[0].isoformat() if prior else None,"rows_2025":len(rows_2025),"date_min_2025":min([x[0] for x in rows_2025]).isoformat() if rows_2025 else None,"date_max_2025":max([x[0] for x in rows_2025]).isoformat() if rows_2025 else None,"missing_report_week_sequence":week_gaps},
  "btc":{"source":"Binance Vision official BTCUSDT spot 1d monthly archives","daily_rows":len(btc_dates),"expected_daily_rows":expected_days,"date_min":min(btc_dates).isoformat() if btc_dates else None,"date_max":max(btc_dates).isoformat() if btc_dates else None,"monthly_sha256":btc_month_sha,"combined_archive_sha256":hashlib.sha256("".join(btc_archive_sha).encode()).hexdigest() if btc_archive_sha else None},
  "issues":issues,"outcomes_computed":False,"returns_computed":False,"pnl_computed":False,"signal_values_computed":False,"year_2025_accessed":True,"year_2025_access_scope":"source gate only under frozen OOS authorization","year_2026_accessed":False
}
json.dump(receipt,open(os.path.join(OUT,"source_data_gate_receipt.json"),"w",encoding="utf-8"),indent=2,sort_keys=True)
print(json.dumps(receipt,indent=2,sort_keys=True))
sys.exit(0 if status=="SOURCE_DATA_GATE_PASS" else 2)
