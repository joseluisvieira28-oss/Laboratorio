"""Source-only audit: do original OFFICIAL daily 1m mark archives repair February 2023 gaps?"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,zipfile
from datetime import datetime,timezone
from pathlib import Path
from research.convex_sol_bnb_gates_v01 import mark_1m_proxy_sensitivity as mark
from research.convex_multialt_4tf_20261013 import multialt_matrix as archives
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src

def daily_mark(symbol,date):
    if symbol not in ("SOLUSDT","BNBUSDT"):raise ValueError("SYMBOL_SCOPE_INVALID")
    if not re.fullmatch(r"2023-02-\d{2}",date):raise ValueError("DATE_SCOPE_INVALID")
    url=f"https://data.binance.vision/data/futures/um/daily/markPriceKlines/{symbol}/1m/{symbol}-1m-{date}.zip"
    data=src.fetch(url,10_000_000)
    check=src.fetch(url+".CHECKSUM",1000).decode("utf8-sig").strip().split()[0].lower()
    got=hashlib.sha256(data).hexdigest()
    if got!=check:raise ValueError("DAILY_MARK_PUBLISHER_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        csvs=[s for s in z.namelist() if s.lower().endswith(".csv")]
        if len(csvs)!=1:raise ValueError("DAILY_MARK_MEMBER_COUNT_INVALID")
        rows=list(csv.reader(io.StringIO(z.read(csvs[0]).decode("utf8-sig"))))
    result={}
    for r in rows:
        if not r or not r[0].strip().isdigit():continue
        ts=src.ms(r[0]);op=float(r[1])
        if ts%60000 or not math.isfinite(op) or op<=0 or ts in result:
            raise ValueError("BAD_DAILY_MARK_SOURCE")
        result[ts]=op
    return result,{"url":url,"publisher_sha256":got,"rows":len(result)}

def source_only(symbol):
    if symbol not in ("SOLUSDT","BNBUSDT"):raise ValueError("NOT_FROZEN_PAIR")
    from research.convex_8alt_common_2023_25.common_3yr import apply_locked_3year_window
    apply_locked_3year_window()
    funding_csv,funding_sha=archives.fetch_archive(symbol,"fundingRate","2023-02")
    event_rates=src.funding_records(funding_csv)
    monthly,month_sha=mark.get_verified_mark_minute(symbol,"2023-02")
    missing=sorted(set(event_rates)-set(monthly))
    if len(missing)!=3:
        raise ValueError(f"THREE_EXPECTED_MONTHLY_MISSING_EVENTS_CHANGED:{len(missing)}")
    all_dates=sorted({datetime.fromtimestamp(t/1000,timezone.utc).strftime("%Y-%m-%d") for t in missing})
    provenance=[]
    repaired={}
    for date in all_dates:
        found,proof=daily_mark(symbol,date)
        provenance.append(proof)
        for ts in missing:
            if datetime.fromtimestamp(ts/1000,timezone.utc).strftime("%Y-%m-%d")==date:
                if ts in found:repaired[ts]=found[ts]
    return {"symbol":symbol,
            "monthly_missing_event_timestamps":missing,
            "monthly_missing_event_iso_utc":[datetime.fromtimestamp(t/1000,timezone.utc).isoformat() for t in missing],
            "verified_monthly_mark_sha256":month_sha,
            "verified_monthly_funding_sha256":funding_sha,
            "daily_sources":provenance,
            "exact_minute_bars_recovered_from_official_daily":{str(k):v for k,v in repaired.items()},
            "status":"OFFICIAL_DAILY_1M_SOURCE_RECOVERY_PASS_NOT_EXACT_FUNDING_MARK" if len(repaired)==3 else "OFFICIAL_DAILY_1M_SOURCE_GAP_UNRESOLVED",
            "actual_settlement_mark_proven":False,"historical_alpha_outcome_tested":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=("SOLUSDT","BNBUSDT"))
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    out={"symbol":a.symbol,"status":"SOURCE_BLOCKED"}
    try:out=source_only(a.symbol)
    except Exception as exc:out["block_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"F1C_DAILY_SOURCE.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("F1C_SOURCE_FINAL",json.dumps(out,sort_keys=True),flush=True)
    if out["status"]!="OFFICIAL_DAILY_1M_SOURCE_RECOVERY_PASS_NOT_EXACT_FUNDING_MARK":
        raise SystemExit(2)
if __name__=="__main__":main()
