#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, sys, urllib.request, zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import source_audit as raw

UTC=dt.timezone.utc
LAB_ID='OPTIONS-SPOTPERP-001'
VERSION='V2.1-OOS-2025-SOURCE-V0.1'
AUTHORITY_COMMIT='bc7d397f7d6d896a0ef3fc25b93e4678e64f8ae2'
START=dt.datetime(2025,1,1,tzinfo=UTC)
END_EXCLUSIVE=dt.datetime(2026,1,1,tzinfo=UTC)
MIN_VALID_SOURCE_DAYS=80
# Full BTC history required to continue the exact expanding-median RV20 state into 2025.
BTC_START=(2021,4)
BTC_END=(2025,12)


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()


def deribit_months():
    cur=START
    while cur<END_EXCLUSIVE:
        nxt=dt.datetime(cur.year+1,1,1,tzinfo=UTC) if cur.month==12 else dt.datetime(cur.year,cur.month+1,1,tzinfo=UTC)
        yield int(cur.timestamp()*1000),int(nxt.timestamp()*1000)-1
        cur=nxt


def btc_months():
    y,m=BTC_START
    while (y,m)<=BTC_END:
        yield y,m
        if m==12:y,m=y+1,1
        else:m+=1


def ts_ms(v:int)->tuple[int,str]:
    if 1_000_000_000_000<=v<10_000_000_000_000:return v,'milliseconds'
    if 1_000_000_000_000_000<=v<10_000_000_000_000_000:return v//1000,'microseconds'
    raise RuntimeError(f'FAIL-CLOSED unexpected Binance timestamp magnitude {v}')


def download_btc(out:Path):
    d=out/'raw_binance_btcusdt_1d';d.mkdir(parents=True,exist_ok=True);entries=[]
    for y,m in btc_months():
        name=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip';url=f'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/{name}';p=d/name
        with urllib.request.urlopen(url,timeout=90) as r:p.write_bytes(r.read())
        with zipfile.ZipFile(p) as zf:
            members=[x for x in zf.namelist() if not x.endswith('/')]
            if len(members)!=1:raise RuntimeError(f'FAIL-CLOSED BTC zip members {name}')
            with zf.open(members[0]) as fh: rows=[x.decode().strip() for x in fh if x.strip()]
            if not rows:raise RuntimeError(f'FAIL-CLOSED empty BTC archive {name}')
            a=int(rows[0].split(',')[0]);b=int(rows[-1].split(',')[0]);ams,au=ts_ms(a);bms,bu=ts_ms(b)
            if au!=bu:raise RuntimeError(f'FAIL-CLOSED mixed timestamp units {name}')
            if dt.datetime.fromtimestamp(bms/1000,tz=UTC).year>=2026:raise RuntimeError('FAIL-CLOSED 2026 BTC row')
        entries.append({'file':name,'url':url,'sha256':sha256_file(p),'bytes':p.stat().st_size,'timestamp_unit':au,'first_open_raw':a,'last_open_raw':b,'first_open_ms':ams,'last_open_ms':bms})
    return entries


def run(out:Path):
    out.mkdir(parents=True,exist_ok=True);(out/'raw').mkdir(exist_ok=True)
    raw.LAB_ID=LAB_ID;raw.VERSION=VERSION;raw.USER_AGENT=f'{LAB_ID}/{VERSION} source-only'
    raw.START=START;raw.END_EXCLUSIVE=END_EXCLUSIVE;raw.HOLDOUT_START_MS=int(END_EXCLUSIVE.timestamp()*1000);raw.COUNT=10000;raw.MIN_VALID_DAYS=MIN_VALID_SOURCE_DAYS
    state=raw.AuditAccumulator(out/'_ids.sqlite3');pages=[];counter=[0];completed=0
    try:
        for a,b in deribit_months():
            trades=raw.fetch_complete_window(a,b,out/'raw',counter,pages);state.consume(trades);completed+=1
        audit=state.finalize()
    finally:state.close()
    btc=download_btc(out)
    checks={'source_fetch_complete':completed==12,'no_duplicate_trade_ids':audit['duplicate_trade_ids']==0,'no_timestamp_violations':audit['timestamp_violations']==0,'valid_signal_coverage_days_ge_80':audit['valid_signal_coverage_days']>=MIN_VALID_SOURCE_DAYS,'btc_full_history_present':len(btc)==57,'year_2026_accessed':False,'outcomes_computed':False}
    hard=[checks[k] for k in ('source_fetch_complete','no_duplicate_trade_ids','no_timestamp_violations','valid_signal_coverage_days_ge_80','btc_full_history_present')]
    status='SOURCE_AUDIT_PASS' if all(hard) else 'SOURCE_AUDIT_BLOCKED'
    manifest={'lab_id':LAB_ID,'version':VERSION,'authority_commit':AUTHORITY_COMMIT,'stage':'V21_2025_OOS_SOURCE_ONLY','status':status,'requested_period':{'start':START.isoformat(),'end_exclusive':END_EXCLUSIVE.isoformat()},'oos_2025_authorized':True,'oos_2025_accessed':True,'year_2026_accessed':False,'source_fetch_complete':completed==12,'raw_pages':pages,'btc_price_raw_archives':btc,'skew_values_computed':False,'signals_computed':False,'forward_returns_computed':False,'pnl_computed':False}
    report={'lab_id':LAB_ID,'version':VERSION,'status':status,'checks':checks,'audit':audit,'outcome_metrics_computed':False}
    (out/'v21_oos_source_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True));(out/'v21_oos_source_audit_report.json').write_text(json.dumps(report,indent=2,sort_keys=True))
    print(status);print('VALID_SOURCE_DAYS=',audit['valid_signal_coverage_days']);print('BTC_ARCHIVES=',len(btc));print('2025 SOURCE ONLY / 2026 LOCKED / NO OUTCOMES')
    return 0 if status=='SOURCE_AUDIT_PASS' else 2

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();raise SystemExit(run(Path(a.output)))