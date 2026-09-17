#!/usr/bin/env python3
"""CED-1D-V1 V3 source recovery v0.2 — canonical USD-M Futures route.

SOURCE-ONLY / OUTCOME-BLIND. 2021-2024 only.
This v0.2 supersedes only the provider-route field of v0.1 after recovery of
canonical Phase 2 authority bytes proving the market is Binance USD-M Futures.
No hypothesis, period, universe, or economic rule is changed.
"""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.request, zipfile
from pathlib import Path

SYMBOLS=["ADAUSDT","AVAXUSDT","BNBUSDT","BTCUSDT","DOGEUSDT","ETHUSDT","LINKUSDT","LTCUSDT","SOLUSDT","XRPUSDT"]
YEARS={2021,2022,2023,2024}
EXPECTED=480
BASE="https://data.binance.vision/data/futures/um/monthly/klines"
UA="CED-1D-V1-V3-BYTE-RECOVERY/0.2 source-only usd-m"

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()

def month_year(month:str)->int:
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])",month): raise RuntimeError(f"invalid month: {month}")
    return int(month[:4])

def load_registry(path:Path):
    obj=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj,list): raise RuntimeError('registry must be JSON array')
    selected=[]
    for row in obj:
        if not isinstance(row,dict): raise RuntimeError('registry contains non-object row')
        symbol=str(row.get('symbol','')); month=str(row.get('month','')); y=month_year(month)
        if y not in YEARS: continue
        if symbol not in SYMBOLS: raise RuntimeError(f'unexpected Discovery symbol: {symbol}')
        selected.append(row)
    if len(selected)!=EXPECTED: raise RuntimeError(f'registry Discovery population != {EXPECTED}: {len(selected)}')
    out={}
    for row in selected:
        key=(str(row['symbol']),str(row['month']))
        if key in out: raise RuntimeError(f'duplicate registry key: {key}')
        if row.get('status')!='PASS' or row.get('classification')!='PASS': raise RuntimeError(f'historical source row not PASS: {key}')
        if row.get('provider_checksum_match') is not True: raise RuntimeError(f'historical provider checksum not PASS: {key}')
        hs=[str(row.get(k,'')).lower() for k in ('local_sha256','provider_sha256')]
        if any(not re.fullmatch(r'[0-9a-f]{64}',x) for x in hs): raise RuntimeError(f'invalid historical SHA256: {key}')
        if hs[0]!=hs[1]: raise RuntimeError(f'historical local/provider SHA mismatch: {key}')
        z=row.get('zip_sha256')
        if z is not None and str(z).lower()!=hs[0]: raise RuntimeError(f'historical zip/local SHA mismatch: {key}')
        out[key]=row
    exp={(s,f'{y:04d}-{m:02d}') for s in SYMBOLS for y in sorted(YEARS) for m in range(1,13)}
    if set(out)!=exp: raise RuntimeError('registry coverage mismatch')
    return out

def fetch(url:str,path:Path):
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=120) as r: path.write_bytes(r.read())

def parse_checksum(text:str, expected_filename:str)->str:
    lines=text.strip().splitlines()
    if len(lines)!=1: raise RuntimeError('malformed provider checksum file')
    parts=lines[0].split()
    if not parts or not re.fullmatch(r'[0-9a-fA-F]{64}',parts[0]): raise RuntimeError('malformed provider SHA256')
    if len(parts)>=2 and Path(parts[-1].lstrip('*')).name!=expected_filename: raise RuntimeError('provider checksum filename mismatch')
    return parts[0].lower()

def run(registry_path:Path,out:Path)->int:
    reg=load_registry(registry_path); out.mkdir(parents=True,exist_ok=True)
    raw=out/'RAW'; rows=[]; failure=None
    for symbol in SYMBOLS:
        (raw/symbol).mkdir(parents=True,exist_ok=True)
        for year in sorted(YEARS):
            for mi in range(1,13):
                month=f'{year:04d}-{mi:02d}'; hist=reg[(symbol,month)]
                expected=str(hist['local_sha256']).lower(); name=f'{symbol}-1m-{month}.zip'
                url=f'{BASE}/{symbol}/1m/{name}'; zp=raw/symbol/name; cp=raw/symbol/(name+'.CHECKSUM')
                rec={'symbol':symbol,'month':month,'filename':name,'expected_sha256':expected,'provider_route':'BINANCE_USD_M_FUTURES_MONTHLY_KLINES'}
                try:
                    fetch(url,zp); fetch(url+'.CHECKSUM',cp)
                    provider=parse_checksum(cp.read_text(encoding='utf-8'),name); local=sha256_file(zp)
                    rec.update(provider_sha256_now=provider,local_sha256_now=local,provider_checksum_matches_download=provider==local,byte_exact_matches_historical=(local==expected==str(hist['provider_sha256']).lower()))
                    with zipfile.ZipFile(zp) as zf: rec['zip_crc_pass']=zf.testzip() is None
                    rec['status']='PASS' if rec['provider_checksum_matches_download'] and rec['byte_exact_matches_historical'] and rec['zip_crc_pass'] else 'FAIL'
                except Exception as e:
                    rec['status']='FAIL'; rec['error']=f'{type(e).__name__}: {e}'
                rows.append(rec)
                if rec['status']!='PASS': failure=rec; break
            if failure: break
        if failure: break
    status='BYTE_EXACT_RECOVERY_PASS' if failure is None and len(rows)==EXPECTED and all(r['status']=='PASS' for r in rows) else 'BYTE_EXACT_RECOVERY_BLOCKED'
    receipt={'status':status,'provider_route':'BINANCE_USD_M_FUTURES_MONTHLY_KLINES','completed_records':len(rows),'expected_records':EXPECTED,'first_failure':failure,'records':rows,'year_2025_accessed':False,'year_2026_accessed':False,'outcomes_computed':False,'live_trading_authorized':False,'exchange_mutation_authorized':False}
    (out/'byte_exact_recovery_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding='utf-8')
    print(status); return 0 if status=='BYTE_EXACT_RECOVERY_PASS' else 4

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--registry',required=True); ap.add_argument('--output',required=True)
    a=ap.parse_args(); raise SystemExit(run(Path(a.registry),Path(a.output)))
