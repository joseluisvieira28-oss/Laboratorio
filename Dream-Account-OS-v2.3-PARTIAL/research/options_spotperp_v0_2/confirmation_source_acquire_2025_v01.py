#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, sys, urllib.request, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "options_spotperp_v0_1"
sys.path.insert(0, str(PARENT))
import source_audit as raw

UTC = dt.timezone.utc
LAB_ID = "OPTIONS-SPOTPERP-002"
VERSION = "CONFIRMATION-SOURCE-V0.1"
AUTHORITY_COMMIT = "6f47b388b2c7e0a19df41200472e50caed4f58a6"
START = dt.datetime(2025,1,1,tzinfo=UTC)
END_EXCLUSIVE = dt.datetime(2026,1,1,tzinfo=UTC)
MIN_VALID_SOURCE_DAYS = 80
BINANCE_MONTHS = [(2024,12)] + [(2025,m) for m in range(1,13)]


def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def months():
    cur=START
    while cur<END_EXCLUSIVE:
        nxt = dt.datetime(cur.year+1,1,1,tzinfo=UTC) if cur.month==12 else dt.datetime(cur.year,cur.month+1,1,tzinfo=UTC)
        yield int(cur.timestamp()*1000), int(nxt.timestamp()*1000)-1
        cur=nxt


def binance_spot_timestamp_to_ms(value: int) -> tuple[int, str]:
    """Normalize Binance public SPOT archive timestamps without changing source-time semantics.

    Binance public SPOT archives use milliseconds before 2025-01-01 and
    microseconds from 2025-01-01 onward. Fail closed on any unexpected order
    of magnitude instead of guessing.
    """
    if 1_000_000_000_000 <= value < 10_000_000_000_000:
        return value, 'milliseconds'
    if 1_000_000_000_000_000 <= value < 10_000_000_000_000_000:
        return value // 1000, 'microseconds'
    raise RuntimeError(f'FAIL-CLOSED: unexpected Binance SPOT timestamp magnitude: {value}')


def download_binance(out: Path):
    d=out/'raw_binance_btcusdt_1d'; d.mkdir(parents=True,exist_ok=True)
    entries=[]
    for y,m in BINANCE_MONTHS:
        name=f'BTCUSDT-1d-{y:04d}-{m:02d}.zip'
        url=f'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/{name}'
        p=d/name
        with urllib.request.urlopen(url,timeout=90) as r: p.write_bytes(r.read())
        with zipfile.ZipFile(p) as zf:
            members=[n for n in zf.namelist() if not n.endswith('/')]
            if len(members)!=1: raise RuntimeError(f'unexpected Binance ZIP members: {name}')
            rows=[]
            with zf.open(members[0]) as fh:
                for line in fh:
                    s=line.decode('utf-8').strip()
                    if s: rows.append(s)
            if not rows: raise RuntimeError(f'empty Binance archive: {name}')
            first_raw=int(rows[0].split(',')[0]); last_raw=int(rows[-1].split(',')[0])
            first_ms, first_unit=binance_spot_timestamp_to_ms(first_raw)
            last_ms, last_unit=binance_spot_timestamp_to_ms(last_raw)
            if first_unit != last_unit:
                raise RuntimeError(f'FAIL-CLOSED: mixed Binance timestamp units inside archive: {name}')
            if dt.datetime.fromtimestamp(last_ms/1000,tz=UTC).year>=2026:
                raise RuntimeError('FAIL-CLOSED: 2026 Binance row present')
        entries.append({
            'file':name,'url':url,'sha256':sha256_file(p),'bytes':p.stat().st_size,
            'timestamp_unit':first_unit,
            'first_open_raw':first_raw,'last_open_raw':last_raw,
            'first_open_ms':first_ms,'last_open_ms':last_ms,
        })
    return entries


def run(out: Path):
    out.mkdir(parents=True,exist_ok=True); (out/'raw').mkdir(exist_ok=True)
    # Reuse only the proven Deribit fetch/parser implementation; move its hard stop to 2026 for this separately authorized OOS source stage.
    raw.LAB_ID=LAB_ID; raw.VERSION=VERSION; raw.USER_AGENT=f'{LAB_ID}/{VERSION} source-only'
    raw.START=START; raw.END_EXCLUSIVE=END_EXCLUSIVE; raw.HOLDOUT_START_MS=int(END_EXCLUSIVE.timestamp()*1000)
    raw.COUNT=10000; raw.MIN_VALID_DAYS=MIN_VALID_SOURCE_DAYS
    state=raw.AuditAccumulator(out/'_ids.sqlite3')
    pages=[]; counter=[0]; completed=0
    try:
        for a,b in months():
            trades=raw.fetch_complete_window(a,b,out/'raw',counter,pages)
            state.consume(trades); completed+=1
        audit=state.finalize()
    finally:
        state.close()
    btc=download_binance(out)
    checks={
        'source_fetch_complete': completed==12,
        'no_duplicate_trade_ids': audit['duplicate_trade_ids']==0,
        'no_timestamp_violations': audit['timestamp_violations']==0,
        'valid_signal_coverage_days_ge_80': audit['valid_signal_coverage_days']>=MIN_VALID_SOURCE_DAYS,
        'required_btc_archives_present': len(btc)==13,
        'year_2026_accessed': False,
        'outcomes_computed': False,
    }
    status='SOURCE_AUDIT_PASS' if all(v is True for k,v in checks.items() if k not in {'year_2026_accessed','outcomes_computed'}) and checks['year_2026_accessed'] is False and checks['outcomes_computed'] is False else 'SOURCE_AUDIT_BLOCKED'
    manifest={
        'lab_id':LAB_ID,'version':VERSION,'authority_commit':AUTHORITY_COMMIT,'stage':'CONFIRMATION_2025_SOURCE_ONLY','status':status,
        'requested_period':{'start':START.isoformat(),'end_exclusive':END_EXCLUSIVE.isoformat()},'confirmation_2025_authorized':True,
        'confirmation_2025_accessed':True,'year_2026_accessed':False,'source_fetch_complete':completed==12,'raw_pages':pages,
        'btc_price_raw_archives':btc,'skew_values_computed':False,'signals_computed':False,'forward_returns_computed':False,'pnl_computed':False,
    }
    report={'lab_id':LAB_ID,'version':VERSION,'status':status,'checks':checks,'audit':audit,'outcome_metrics_computed':False}
    (out/'confirmation_source_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
    (out/'confirmation_source_audit_report.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print(status); print('VALID_SOURCE_DAYS=',audit['valid_signal_coverage_days']); print('2025 SOURCE AUTHORIZED / 2026 LOCKED / NO OUTCOMES')
    return 0 if status=='SOURCE_AUDIT_PASS' else 2

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); raise SystemExit(run(Path(a.output)))
