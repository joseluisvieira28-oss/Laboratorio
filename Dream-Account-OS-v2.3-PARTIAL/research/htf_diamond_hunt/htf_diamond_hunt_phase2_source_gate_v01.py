from __future__ import annotations

import csv, hashlib, io, json, sys, time, urllib.request, urllib.error, zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator

CAMPAIGN_ID='HTF-DIAMOND-HUNT-001'
PHASE='PHASE_2_DONCHIAN_FAMILY_TEMPORAL_VALIDATION'
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','XRPUSDT','DOGEUSDT')
YEARS=(2019,2020)
MONTHS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13))
INTERVAL='1m'; MINUTE_MS=60_000; BAR15_MS=900_000
START_MS=1546300800000; END_MS=1609459200000
BASE_URL='https://data.binance.vision/data/spot/monthly/klines'
UA='HTF-DIAMOND-HUNT-001 Phase2 source gate/1.0'
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research'/'local_data'/'htf_diamond_hunt_phase2_source_v01'
CANON=OUT/'canonical_15m'; RAW_META=OUT/'raw_meta'
RECEIPT=OUT/'HTF_DIAMOND_HUNT_001_PHASE2_SOURCE_GATE_V0.1.json'
FREEZE=ROOT/'research'/'htf_diamond_hunt'/'HTF_DIAMOND_HUNT_001_PHASE2_VALIDATION_FREEZE_V0.1.json'


def sha256_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def canonical_hash(o:object)->str: return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def get_optional(url:str,retries:int=4)->bytes|None:
    last=None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA})
            with urllib.request.urlopen(req,timeout=90) as r:
                if r.status!=200: raise RuntimeError(f'HTTP {r.status}: {url}')
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            last=e
        except Exception as e: last=e
        if attempt+1<retries: time.sleep(2**attempt)
    raise RuntimeError(f'download failed after {retries} attempts:{url}:{last}')

def parse_checksum(b:bytes,name:str)->str:
    line=b.decode('utf-8',errors='strict').strip().splitlines()[0].strip(); parts=line.replace('*',' ').split()
    if not parts or len(parts[0])!=64: raise ValueError(f'invalid checksum:{name}:{line[:120]}')
    if len(parts)>1 and name not in ' '.join(parts[1:]): raise ValueError(f'checksum filename mismatch:{name}')
    return parts[0].lower()

def iter_zip_rows(zb:bytes,expected_csv:str)->Iterator[tuple[int,float,float,float,float,float]]:
    with zipfile.ZipFile(io.BytesIO(zb)) as zf:
        names=[n for n in zf.namelist() if not n.endswith('/')]
        member=expected_csv if expected_csv in names else (names[0] if len(names)==1 and names[0].endswith('.csv') else None)
        if member is None: raise ValueError(f'csv member mismatch:{expected_csv}:{names[:5]}')
        with zf.open(member) as raw:
            reader=csv.reader(io.TextIOWrapper(raw,encoding='utf-8',newline=''))
            for row in reader:
                if not row: continue
                try: t=int(row[0])
                except ValueError:
                    if row[0].strip().lower() in {'open_time','open time'}: continue
                    raise
                if len(row)<6: raise ValueError('schema too short')
                yield t,float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5])

@dataclass
class Audit:
    symbol:str; first_available_month:str|None=None; last_available_month:str|None=None
    pre_listing_unavailable_months:int=0; available_archive_count:int=0; checksum_verified_count:int=0
    raw_row_count:int=0; duplicate_timestamp_count:int=0; non_monotonic_timestamp_count:int=0
    out_of_window_row_count:int=0; complete_15m_count:int=0; incomplete_15m_bucket_count:int=0
    detected_minute_gap_count:int=0; canonical_csv_sha256:str=''; first_raw_open_time:int|None=None; last_raw_open_time:int|None=None

def aggregate(symbol:str,payloads:list[tuple[str,bytes]],audit:Audit)->None:
    CANON.mkdir(parents=True,exist_ok=True); p=CANON/f'{symbol}_15m.csv'; h=hashlib.sha256()
    prev=None; bucket=None; rows=[]
    def emit(w):
        nonlocal rows,bucket
        if bucket is None or not rows: return
        exp=[bucket+i*MINUTE_MS for i in range(15)]; obs=[r[0] for r in rows]
        if len(rows)==15 and obs==exp:
            line=[bucket,repr(rows[0][1]),repr(max(r[2] for r in rows)),repr(min(r[3] for r in rows)),repr(rows[-1][4]),repr(sum(r[5] for r in rows)),15]
            sio=io.StringIO(newline=''); csv.writer(sio,lineterminator='\n').writerow(line); h.update(sio.getvalue().encode()); w.writerow(line); audit.complete_15m_count+=1
        else: audit.incomplete_15m_bucket_count+=1
        rows=[]
    with p.open('w',encoding='utf-8',newline='') as fh:
        w=csv.writer(fh,lineterminator='\n'); header=['open_time','open','high','low','close','volume','minute_count']; w.writerow(header); h.update((','.join(header)+'\n').encode())
        for ym,zb in payloads:
            for r in iter_zip_rows(zb,f'{symbol}-{INTERVAL}-{ym}.csv'):
                t=r[0]; audit.raw_row_count+=1
                if audit.first_raw_open_time is None: audit.first_raw_open_time=t
                audit.last_raw_open_time=t
                if not (START_MS<=t<END_MS): audit.out_of_window_row_count+=1; continue
                if prev is not None:
                    if t==prev: audit.duplicate_timestamp_count+=1
                    elif t<prev: audit.non_monotonic_timestamp_count+=1
                    elif t>prev+MINUTE_MS: audit.detected_minute_gap_count+=1
                prev=t; b=(t//BAR15_MS)*BAR15_MS
                if bucket is None: bucket=b
                if b!=bucket: emit(w); bucket=b
                rows.append(r)
        emit(w)
    audit.canonical_csv_sha256=h.hexdigest()

def main()->int:
    f=json.loads(FREEZE.read_text()); assert f['status']=='FROZEN_BEFORE_PHASE2_SOURCE_ACCESS_OR_OUTCOMES'; assert f['validation_dataset']['allowed_source_years']==[2019,2020]
    OUT.mkdir(parents=True,exist_ok=True); CANON.mkdir(parents=True,exist_ok=True); RAW_META.mkdir(parents=True,exist_ok=True)
    records=[]; audits={}
    try:
        for symbol in SYMBOLS:
            a=Audit(symbol); payloads=[]; seen=False; meta=[]
            for ym in MONTHS:
                name=f'{symbol}-{INTERVAL}-{ym}.zip'; url=f'{BASE_URL}/{symbol}/{INTERVAL}/{name}'; cu=url+'.CHECKSUM'
                z=get_optional(url); cb=get_optional(cu)
                if z is None and cb is None:
                    if seen: raise ValueError(f'post-listing monthly archive missing:{symbol}:{ym}')
                    a.pre_listing_unavailable_months+=1; meta.append({'symbol':symbol,'month':ym,'status':'PRE_LISTING_UNAVAILABLE'}); continue
                if (z is None)!=(cb is None): raise ValueError(f'archive/checksum availability mismatch:{symbol}:{ym}')
                assert z is not None and cb is not None
                seen=True; a.first_available_month=a.first_available_month or ym; a.last_available_month=ym
                ps=parse_checksum(cb,name); ls=sha256_bytes(z)
                if ps!=ls: raise ValueError(f'checksum mismatch:{symbol}:{ym}')
                rec={'symbol':symbol,'month':ym,'status':'AVAILABLE_VERIFIED','archive_name':name,'archive_url':url,'checksum_url':cu,'byte_count':len(z),'provider_sha256':ps,'local_sha256':ls}
                records.append(rec); meta.append(rec); payloads.append((ym,z)); print(f'{symbol} {ym} PASS bytes={len(z)}',flush=True)
            if not seen: raise ValueError(f'no official monthly archive in validation window:{symbol}')
            a.available_archive_count=len(payloads); a.checksum_verified_count=len(payloads); aggregate(symbol,payloads,a)
            if a.duplicate_timestamp_count or a.non_monotonic_timestamp_count or a.out_of_window_row_count: raise ValueError(f'integrity failure:{symbol}:{asdict(a)}')
            audits[symbol]=asdict(a); (RAW_META/f'{symbol}_SOURCE_META.json').write_text(json.dumps(meta,indent=2,sort_keys=True))
        pre={'campaign_id':CAMPAIGN_ID,'phase':PHASE,'provider':'Binance public data','market':'Spot','raw_interval':'1m','allowed_years':[2019,2020],'listing_aware':True,'records':sorted(records,key=lambda r:(r['symbol'],r['month'])),'symbol_audits':audits}
        fp=canonical_hash(pre)
        receipt={'status':'SOURCE_DATA_PASS',**pre,'available_archive_count':len(records),'provider_checksum_verified_count':len(records),'source_fingerprint':fp,'signal_calculation_performed':False,'market_return_calculation_performed':False,'outcome_evaluation_performed':False,'access_2021_performed':False,'access_2022_performed':False,'access_2023_performed':False,'access_2024_performed':False,'access_2025_performed':False,'access_2026_performed':False,'live_trading':False,'exchange_mutation':False}
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)); print(json.dumps({'status':'SOURCE_DATA_PASS','available_archive_count':len(records),'source_fingerprint':fp,'audits':audits,'outcome_evaluation_performed':False},indent=2,sort_keys=True)); return 0
    except Exception as exc:
        r={'status':'BLOCKED_PRE_OUTCOME_SOURCE_GATE','reason':f'{type(exc).__name__}: {exc}','campaign_id':CAMPAIGN_ID,'phase':PHASE,'signal_calculation_performed':False,'market_return_calculation_performed':False,'outcome_evaluation_performed':False,'access_2021_performed':False,'access_2022_performed':False,'access_2023_performed':False,'access_2024_performed':False,'access_2025_performed':False,'access_2026_performed':False,'live_trading':False,'exchange_mutation':False}; RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)); print(json.dumps(r,indent=2,sort_keys=True),file=sys.stderr); return 2

if __name__=='__main__': raise SystemExit(main())
