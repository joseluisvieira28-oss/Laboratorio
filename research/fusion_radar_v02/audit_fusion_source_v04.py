#!/usr/bin/env python3
"""Read-only independent audit of Fusion AVAX20/BTC20 2022-2023.
Verify 74 cached Binance ZIPs against companion CHECKSUM files and the
operator manifest; reconstruct all 730 source signals and hourly proxy
prices, comparing to CSV and JSON. No network, orders or holdout access.
This does NOT attest archive publication at historical signal times, fills
or profitable independent out-of-sample trading.
"""
import argparse, calendar, csv, datetime as dt, hashlib, io, json, math, re, sys, zipfile
from pathlib import Path

START=dt.date(2022,1,1)
UTC=dt.timezone.utc
MONTHS=[(2021,12)]+[(y,m) for y in (2022,2023) for m in range(1,13)]
SPECS=(("spot","BTCUSDT","1d"),("futures_um","AVAXUSDT","1d"),
       ("futures_um","AVAXUSDT","1h"))
BASE="https://data.binance.vision/data/"

class AuditError(Exception): pass

def gate(ok, reason):
    if not ok: raise AuditError(reason)

def sha(b): return hashlib.sha256(b).hexdigest()

def checks(folder):
    candles={}; manifest=[]
    for kind,symbol,tf in SPECS:
        key=(kind,symbol,tf)
        candles[key]={}
        for year,month in MONTHS:
            if tf=="1h" and (year,month)==(2021,12): continue
            ym=f"{year:04d}-{month:02d}"
            name=f"{symbol}-{tf}-{ym}.zip"
            file=folder/f"{kind}__{name}"
            checksum=folder/f"{kind}__{name}.CHECKSUM"
            gate(file.is_file() and checksum.is_file(),"MISSING_ARCHIVE:"+name)
            raw=file.read_bytes()
            gate(0<len(raw)<=6_000_000,"ZIP_SIZE:"+name)
            digest=sha(raw)
            try: line=checksum.read_bytes().decode("ascii").strip()
            except UnicodeError: raise AuditError("BAD_CHECKSUM_ENCODING:"+name)
            match=re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?([^\s]+)",line)
            gate(match is not None and match.group(2)==name,"CHECKSUM_FORMAT:"+name)
            gate(match.group(1).lower()==digest,"CHECKSUM_MISMATCH:"+name)
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    entries=[e for e in z.infolist() if not e.is_dir()]
                    gate(len(entries)==1 and entries[0].filename==name[:-4]+".csv",
                         "ZIP_CONTENTS:"+name)
                    gate(entries[0].file_size<=22_000_000,"UNCOMPRESSED_SIZE:"+name)
                    content=z.read(entries[0]).decode("utf-8-sig")
            except (zipfile.BadZipFile,UnicodeError) as e:
                raise AuditError("BAD_ZIP_OR_TEXT:"+name+":"+str(e))
            seen=0
            for row in csv.reader(io.StringIO(content)):
                if not row or row[0].strip().lower() in ("open_time","open time"):continue
                gate(len(row)>=7,"BAD_KLINE_ROW:"+name)
                try:
                    ms=int(row[0]);end=int(row[6]);op=float(row[1]);cl=float(row[4])
                    timestamp=dt.datetime.fromtimestamp(ms/1000,UTC)
                except (ValueError,OverflowError,OSError) as e:
                    raise AuditError("BAD_KLINE_VALUE:"+name+":"+str(e))
                duration=(24 if tf=="1d" else 1)*3_600_000
                gate(timestamp.year==year and timestamp.month==month and
                     ms%duration==0 and end==ms+duration-1,"KLINE_CLOCK:"+name)
                gate(math.isfinite(op) and math.isfinite(cl) and op>0 and cl>0,
                     "BAD_PRICE:"+name)
                gate(timestamp not in candles[key],"DUPLICATE_KLINE:"+name)
                candles[key][timestamp]=(op,cl)
                seen+=1
            gate(seen==calendar.monthrange(year,month)[1]*(24 if tf=="1h" else 1),
                 "INCOMPLETE_MONTH:"+name)
            category=kind.replace("_","/")
            url=f"{BASE}{category}/monthly/klines/{symbol}/{tf}/{name}"
            manifest.append({"source_url":url,"zip_sha256":digest,"candles":seen})
    return candles,manifest

def time_at(day,h=0):return dt.datetime(day.year,day.month,day.day,h,tzinfo=UTC)
def sign(x,y):return (y>x)-(y<x)
def similar(x,y):return math.isfinite(x) and math.isfinite(y) and abs(x-y)<=max(1e-7,abs(y)*1e-9)

def audit(folder,rows,report):
    gate(report.get("period_start")=="2022-01-01" and
         report.get("period_end_exclusive")=="2024-01-01",
         "PROTECTED_WINDOW_CHANGE")
    gate(len(rows)==730,"WRONG_ROW_COUNT")
    candles,manifest=checks(folder)
    gate(len(manifest)==74 and report.get("source_manifest")==manifest,
         "MANIFEST_MISMATCH")
    avaxd=candles[("futures_um","AVAXUSDT","1d")]
    avaxh=candles[("futures_um","AVAXUSDT","1h")]
    btc=candles[("spot","BTCUSDT","1d")]
    arms=("baseline_trade","fusion_trade","opposite_context_trade")
    counts=dict.fromkeys(arms,0)
    sums={case:dict.fromkeys(arms,0.) for case in ("BASE14","STRESS20")}
    for i,row in enumerate(rows):
        day=START+dt.timedelta(days=i)
        try:
            old=day-dt.timedelta(days=21);new=day-dt.timedelta(days=1)
            a=sign(avaxd[time_at(old)][1],avaxd[time_at(new)][1])
            b=sign(btc[time_at(old)][1],btc[time_at(new)][1])
            entry=avaxh[time_at(day,1)][0];exit=avaxh[time_at(day,2)][0]
        except KeyError:raise AuditError("CAUSAL_BAR_MISSING:"+str(day))
        gross=a*(exit/entry-1)*10000
        gate(row.get("date")==day.isoformat() and
             row.get("avax20")==str(a) and row.get("btc20")==str(b),
             "SIGNAL_MISMATCH:"+str(day))
        try: csv_gross=float(row["gross_bps"])
        except (KeyError,ValueError): raise AuditError("BAD_CSV_GROSS:"+str(day))
        gate(similar(csv_gross,gross),"PRICE_REPLAY_MISMATCH:"+str(day))
        masks=dict(baseline_trade=bool(a),fusion_trade=bool(a and a==b),
                   opposite_context_trade=bool(a and a==-b))
        for arm,active in masks.items():
            gate(row.get(arm)==str(active),"MASK_MISMATCH:"+str(day)+":"+arm)
            if active:
                counts[arm]+=1
                for cost,amount in (("BASE14",14),("STRESS20",20)):
                    sums[cost][arm]+=gross-amount
    for case in sums:
        for arm in arms:
            got=report.get("results",{}).get(case,{}).get(arm,{})
            gate(got.get("n_trades")==counts[arm] and
                 isinstance(got.get("total_net_bps_on_1_unit_daily_notional"),(int,float)) and
                 similar(sums[case][arm],float(got["total_net_bps_on_1_unit_daily_notional"])),
                 "REPORT_TOTAL_MISMATCH:"+case+":"+arm)
    return {
      "status":"LOCAL_ARCHIVES_AND_CSV_REPLAY_MATCH",
      "verified_local_zip_checksum_pairs":74,
      "reconstructed_calendar_days":730,
      "trade_counts":counts,
      "net_bps_totals":{k:{a:round(v,6) for a,v in s.items()} for k,s in sums.items()},
      "publication_timestamp_as_of_original_decision":"UNPROVEN",
      "remote_origin_signature":"UNPROVEN_LOCAL_COMPANION_CHECKSUM_ONLY",
      "broker_fills_funding_bid_ask_capacity":"UNPROVEN",
      "independent_out_of_sample_economic_edge":"UNPROVEN",
      "claim":"SOURCE_AND_ARITHMETIC_REPLAY_ONLY"
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir",type=Path,default=Path("historical_archives"))
    p.add_argument("--csv",type=Path,default=Path("results/AVAX_BTC_DAILY_2022_2023.csv"))
    p.add_argument("--json",type=Path,default=Path("results/AVAX_BTC_DEV_2022_2023.json"))
    p.add_argument("--receipt",type=Path,default=Path("results/FUSION_SOURCE_AUDIT_V04.json"))
    x=p.parse_args()
    try:
        with x.csv.open(encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            need=("date","avax20","btc20","gross_bps","baseline_trade",
                  "fusion_trade","opposite_context_trade")
            gate(reader.fieldnames is not None and all(c in reader.fieldnames for c in need),
                 "CSV_COLUMN_MISSING")
            rows=list(reader)
        report=json.loads(x.json.read_text(encoding="utf-8-sig"))
        receipt=audit(x.archive_dir,rows,report)
        receipt["inputs_sha256"]={"csv":sha(x.csv.read_bytes()),
                                  "json":sha(x.json.read_bytes())}
        x.receipt.parent.mkdir(exist_ok=True,parents=True)
        x.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"receipt":str(x.receipt),**receipt},ensure_ascii=False,indent=2))
        return 0
    except (AuditError,FileNotFoundError,PermissionError,json.JSONDecodeError) as e:
        print(json.dumps({"status":"FAIL_CLOSED","error":str(e)}),file=sys.stderr)
        return 2

if __name__=="__main__":sys.exit(main())
