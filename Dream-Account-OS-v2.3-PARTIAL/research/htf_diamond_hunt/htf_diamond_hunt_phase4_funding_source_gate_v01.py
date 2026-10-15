from __future__ import annotations
import csv, hashlib, io, json, sys, time, urllib.request, urllib.error, zipfile
from pathlib import Path

SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','XRPUSDT','DOGEUSDT')
YEARS=(2020,2021,2022)
MONTHS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13))
START_MS=1577836800000; END_MS=1672531200000
BASE='https://data.binance.vision/data/futures/um/monthly/fundingRate'
UA='HTF-DIAMOND-HUNT-001 Phase4 funding source gate/1.0'
ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/'research/htf_diamond_hunt/HTF_DIAMOND_HUNT_001_PHASE4_FUNDING_EXECUTION_FREEZE_V0.1.json'
OUT=ROOT/'research/local_data/htf_diamond_hunt_phase4_funding_source_v01'
CANON=OUT/'canonical_funding'; RECEIPT=OUT/'HTF_DIAMOND_HUNT_001_PHASE4_FUNDING_SOURCE_GATE_V0.1.json'

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def chash(o)->str:return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def get(url,retries=4):
    last=None
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=90) as r:return r.read()
        except urllib.error.HTTPError as e:
            if e.code==404:return None
            last=e
        except Exception as e:last=e
        if k+1<retries:time.sleep(2**k)
    raise RuntimeError(f'download failed {url}: {last}')
def checksum(b,name):
    p=b.decode().strip().splitlines()[0].replace('*',' ').split()
    if not p or len(p[0])!=64:raise ValueError(f'bad checksum {name}')
    return p[0].lower()
def parse_funding(zb:bytes,symbol:str,ym:str):
    expected=f'{symbol}-fundingRate-{ym}.csv'
    out=[]
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        names=[n for n in z.namelist() if not n.endswith('/')]
        member=expected if expected in names else (names[0] if len(names)==1 else None)
        if member is None:raise ValueError(f'funding member mismatch {symbol} {ym} {names[:3]}')
        text=io.TextIOWrapper(z.open(member),encoding='utf-8',newline='')
        rows=list(csv.reader(text))
    if not rows:return []
    hdr=[x.strip().lower() for x in rows[0]]
    has_header=any(x in hdr for x in ('calc_time','fundingtime','funding_time','last_funding_rate','fundingrate','funding_rate'))
    data=rows[1:] if has_header else rows
    if has_header:
        def ix(cands):
            for c in cands:
                if c in hdr:return hdr.index(c)
            return None
        ti=ix(('calc_time','fundingtime','funding_time','funding time'))
        ri=ix(('last_funding_rate','fundingrate','funding_rate','funding rate'))
        if ti is None or ri is None:raise ValueError(f'unknown funding header {hdr}')
    else:
        # Current Binance Vision fundingRate archives are headered. Fail closed on unknown legacy schema.
        raise ValueError(f'headerless funding schema not authorized {symbol} {ym}')
    for r in data:
        if not r:continue
        t=int(float(r[ti])); rate=float(r[ri])
        if START_MS<=t<END_MS:out.append((t,rate))
    return out

def main():
    f=json.loads(FREEZE.read_text());assert f['status']=='FROZEN_BEFORE_PHASE4_SOURCE_ACCESS_OR_OUTCOMES';assert f['dataset']['allowed_source_years']==[2020,2021,2022]
    OUT.mkdir(parents=True,exist_ok=True);CANON.mkdir(parents=True,exist_ok=True)
    recs=[]; audits={}
    try:
        for s in SYMBOLS:
            seen=False; events=[]; available=pre=0
            for ym in MONTHS:
                name=f'{s}-fundingRate-{ym}.zip'; url=f'{BASE}/{s}/{name}'; zb=get(url); cb=get(url+'.CHECKSUM')
                if zb is None and cb is None:
                    if seen:raise ValueError(f'post-listing funding archive missing {s} {ym}')
                    pre+=1;continue
                if (zb is None)!=(cb is None):raise ValueError(f'archive/checksum mismatch {s} {ym}')
                seen=True; available+=1; ps=checksum(cb,name); ls=sha(zb)
                if ps!=ls:raise ValueError(f'checksum mismatch {s} {ym}')
                ev=parse_funding(zb,s,ym); events.extend(ev)
                recs.append({'symbol':s,'month':ym,'archive_name':name,'provider_sha256':ps,'local_sha256':ls,'byte_count':len(zb),'event_count':len(ev)})
                print(s,ym,'PASS',len(ev),flush=True)
            if not seen:raise ValueError(f'no funding archive {s}')
            events.sort();
            if len({t for t,_ in events})!=len(events):raise ValueError(f'duplicate funding timestamp {s}')
            p=CANON/f'{s}_funding.csv'
            with p.open('w',newline='') as fh:
                w=csv.writer(fh,lineterminator='\n');w.writerow(['funding_time_ms','funding_rate']);w.writerows((t,repr(r)) for t,r in events)
            audits[s]={'available_archive_count':available,'pre_listing_unavailable_months':pre,'funding_event_count':len(events),'first_funding_time':events[0][0] if events else None,'last_funding_time':events[-1][0] if events else None,'canonical_sha256':sha(p.read_bytes())}
        pre={'campaign_id':'HTF-DIAMOND-HUNT-001','phase':'PHASE_4_FUNDING_ADJUSTED_MINUTE_PATH_VALIDATION','provider':'Binance public data','archive_family':'futures/um/monthly/fundingRate','allowed_years':[2020,2021,2022],'records':sorted(recs,key=lambda x:(x['symbol'],x['month'])),'audits':audits}
        fp=chash(pre); out={'status':'SOURCE_DATA_PASS',**pre,'source_fingerprint':fp,'outcome_evaluation_performed':False,'price_return_calculation_performed':False,'access_2023_performed':False,'access_2024_performed':False,'access_2025_performed':False,'access_2026_performed':False}
        RECEIPT.write_text(json.dumps(out,indent=2,sort_keys=True));print(json.dumps({'status':'SOURCE_DATA_PASS','source_fingerprint':fp,'audits':audits},indent=2,sort_keys=True));return 0
    except Exception as e:
        out={'status':'BLOCKED_PRE_OUTCOME_SOURCE_GATE','reason':f'{type(e).__name__}: {e}','outcome_evaluation_performed':False,'access_2023_performed':False,'access_2024_performed':False,'access_2025_performed':False,'access_2026_performed':False};RECEIPT.write_text(json.dumps(out,indent=2,sort_keys=True));print(json.dumps(out,indent=2),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
