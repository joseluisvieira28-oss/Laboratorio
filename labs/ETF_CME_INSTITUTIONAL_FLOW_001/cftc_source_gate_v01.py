#!/usr/bin/env python3
import csv, hashlib, io, json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime

DATASET = "6dca-aqww"
BASE = f"https://publicreporting.cftc.gov/resource/{DATASET}.csv"
CODE = "133741"
START = "2018-01-01T00:00:00.000"
END = "2024-12-31T23:59:59.999"
MIN_ROWS = 300
REQUIRED = ["report_date_as_yyyy_mm_dd","yyyy_report_week_ww","cftc_contract_market_code","market_and_exchange_names","open_interest_all","noncomm_positions_long_all","noncomm_positions_short_all"]
out_dir = os.environ.get("OUT_DIR", "artifacts/etf_cme_source_gate_v01")
os.makedirs(out_dir, exist_ok=True)
where = f"cftc_contract_market_code='{CODE}' AND report_date_as_yyyy_mm_dd between '{START}' and '{END}'"
params = {"$limit":"5000","$order":"report_date_as_yyyy_mm_dd ASC","$where":where}
url = BASE + "?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent":"ETF-CME-INSTFLOW-001/0.1 source-audit"})
with urllib.request.urlopen(req, timeout=120) as r: raw = r.read()
raw_path = os.path.join(out_dir,"cftc_legacy_futures_133741_2018_2024.csv")
open(raw_path,"wb").write(raw)
raw_sha = hashlib.sha256(raw).hexdigest()
rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
fields = list(rows[0].keys()) if rows else []
missing_fields = [f for f in REQUIRED if f not in fields]
issues=[]
if missing_fields: issues.append({"type":"SCHEMA_MISSING_FIELDS","fields":missing_fields})
parsed=[]
for i,row in enumerate(rows,1):
    try:
        d=datetime.fromisoformat(row["report_date_as_yyyy_mm_dd"].replace("Z","+00:00")).date()
        m=re.fullmatch(r"(\d{4}) Report Week (\d{2})", row["yyyy_report_week_ww"].strip())
        if not m: raise ValueError("invalid report week label")
        report_year, report_week = int(m.group(1)), int(m.group(2))
        code=row["cftc_contract_market_code"].strip(); oi=int(float(row["open_interest_all"])); nl=int(float(row["noncomm_positions_long_all"])); ns=int(float(row["noncomm_positions_short_all"]))
    except Exception as e:
        issues.append({"type":"PARSE_FAILURE","row":i,"error":str(e)}); continue
    if code!=CODE: issues.append({"type":"WRONG_MARKET_CODE","row":i,"value":code})
    if oi<=0: issues.append({"type":"INVALID_OPEN_INTEREST","row":i,"value":oi})
    if nl<0 or ns<0: issues.append({"type":"INVALID_POSITION","row":i,"long":nl,"short":ns})
    if d.year<2018 or d.year>2024: issues.append({"type":"PROTECTED_PERIOD_OR_OUT_OF_RANGE","row":i,"date":d.isoformat()})
    parsed.append((d,report_year,report_week,oi,nl,ns,row.get("market_and_exchange_names","")))
seen={}
for d,*_ in parsed: seen[d]=seen.get(d,0)+1
duplicates=sorted([d.isoformat() for d,c in seen.items() if c>1])
if duplicates: issues.append({"type":"DUPLICATE_REPORT_DATES","dates":duplicates})
# Weekly continuity is defined by CFTC's own YYYY Report Week WW sequence, not exact 7 elapsed days.
# Holiday weeks can legitimately move the report date by +/-1 day while preserving consecutive report weeks.
week_sequence_gaps=[]
for a,b in zip(parsed, parsed[1:]):
    _, ay, aw, *_ = a; _, by, bw, *_ = b
    ok = (by==ay and bw==aw+1) or (by==ay+1 and bw==1 and aw in (52,53))
    if not ok:
        week_sequence_gaps.append({"from":f"{ay:04d}-{aw:02d}","to":f"{by:04d}-{bw:02d}"})
if week_sequence_gaps: issues.append({"type":"MISSING_REPORT_WEEK_SEQUENCE","gaps":week_sequence_gaps})
calendar_shift_diagnostics=[]
for a,b in zip(parsed,parsed[1:]):
    delta=(b[0]-a[0]).days
    if delta!=7: calendar_shift_diagnostics.append({"from":a[0].isoformat(),"to":b[0].isoformat(),"days":delta})
if len(parsed)<MIN_ROWS: issues.append({"type":"INSUFFICIENT_SAMPLE","rows":len(parsed),"minimum":MIN_ROWS})
by_year={str(y):0 for y in range(2018,2025)}
for d,*_ in parsed:
    if str(d.year) in by_year: by_year[str(d.year)]+=1
status="SOURCE_DATA_GATE_PASS" if not issues else "SOURCE_DATA_GATE_BLOCKED"
dates=sorted(seen)
receipt={"lab":"ETF-CME-INSTFLOW-001","stage":"SOURCE_DATA_GATE_ONLY","status":status,"source":"CFTC Public Reporting Environment / Legacy Futures Only","dataset_id":DATASET,"contract_code":CODE,"query_range":{"start":START,"end":END},"raw_sha256":raw_sha,"row_count":len(rows),"parsed_row_count":len(parsed),"minimum_required_rows":MIN_ROWS,"date_min":dates[0].isoformat() if dates else None,"date_max":dates[-1].isoformat() if dates else None,"rows_by_year":by_year,"duplicate_report_dates":duplicates,"missing_report_week_sequence":week_sequence_gaps,"calendar_shift_diagnostics_nonblocking":calendar_shift_diagnostics,"required_fields":REQUIRED,"missing_fields":missing_fields,"issues":issues,"continuity_definition":"CFTC yyyy_report_week_ww consecutive sequence; holiday date shifts non-blocking","outcomes_computed":False,"returns_computed":False,"pnl_computed":False,"signal_values_computed":False,"year_2025_accessed":False,"year_2026_accessed":False}
json.dump(receipt,open(os.path.join(out_dir,"source_data_gate_receipt.json"),"w",encoding="utf-8"),indent=2,sort_keys=True)
print(json.dumps(receipt,indent=2,sort_keys=True))
sys.exit(0 if status=="SOURCE_DATA_GATE_PASS" else 2)
