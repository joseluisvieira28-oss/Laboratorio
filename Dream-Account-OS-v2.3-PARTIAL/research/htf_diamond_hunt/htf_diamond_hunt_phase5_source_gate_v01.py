from __future__ import annotations
import csv, hashlib, io, json, sys, time, urllib.request, urllib.error, zipfile
from collections import defaultdict
from pathlib import Path

SYMS=('BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','XRPUSDT','DOGEUSDT')
MONTHS=tuple(f'{y}-{m:02d}' for y in (2023,2024) for m in range(1,13))
START=1672531200000;END=1735689600000;MIN=60_000;BAR15=900_000
PBASE='https://data.binance.vision/data/futures/um/monthly/klines'
FBASE='https://data.binance.vision/data/futures/um/monthly/fundingRate'
UA='HTF-DIAMOND-HUNT-001 Phase5 source gate/1.0'
ROOT=Path(__file__).resolve().parents[2];FREEZE=ROOT/'research/htf_diamond_hunt/HTF_DIAMOND_HUNT_001_PHASE5_FORWARD_HOLDOUT_FREEZE_V0.1.json'
OUT=ROOT/'research/local_data/htf_diamond_hunt_phase5_source_v01';PCAN=OUT/'canonical_15m';FCAN=OUT/'canonical_funding';RECEIPT=OUT/'HTF_DIAMOND_HUNT_001_PHASE5_SOURCE_GATE_V0.1.json'

def sha(b):return hashlib.sha256(b).hexdigest()
def chash(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def get(url,retries=4):
    last=None
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=120) as r:return r.read()
        except Exception as e:last=e
        if k+1<retries:time.sleep(2**k)
    raise RuntimeError(f'download failed {url}: {last}')
def csum(b,name):
    p=b.decode().strip().splitlines()[0].replace('*',' ').split()
    if not p or len(p[0])!=64:raise ValueError(f'bad checksum:{name}')
    return p[0].lower()
def price_rows(zb,expected):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        names=[n for n in z.namelist() if not n.endswith('/')]; member=expected if expected in names else (names[0] if len(names)==1 else None)
        if member is None:raise ValueError(f'price member mismatch {expected}')
        with z.open(member) as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding='utf-8',newline=''))
            for x in r:
                if not x:continue
                try:t=int(x[0])
                except ValueError:
                    if x[0].strip().lower() in ('open_time','open time'):continue
                    raise
                if START<=t<END:yield t,float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])
def funding_rows(zb,expected):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        names=[n for n in z.namelist() if not n.endswith('/')];member=expected if expected in names else (names[0] if len(names)==1 else None)
        if member is None:raise ValueError(f'funding member mismatch {expected}')
        rows=list(csv.reader(io.TextIOWrapper(z.open(member),encoding='utf-8',newline='')))
    if not rows:return []
    hdr=[x.strip().lower() for x in rows[0]]
    def ix(cands):
        for c in cands:
            if c in hdr:return hdr.index(c)
        return None
    ti=ix(('calc_time','fundingtime','funding_time','funding time'));ri=ix(('last_funding_rate','fundingrate','funding_rate','funding rate'))
    if ti is None or ri is None:raise ValueError(f'unknown funding schema {hdr}')
    out=[]
    for x in rows[1:]:
        if not x:continue
        t=int(float(x[ti]));r=float(x[ri])
        if START<=t<END:out.append((t,r))
    return out
def aggregate15(allrows,path):
    buckets=defaultdict(list);prev=None;gaps=dups=0
    for row in allrows:
        t=row[0]
        if prev is not None:
            if t<=prev:dups+=1
            elif t>prev+MIN:gaps+=1
        prev=t;buckets[(t//BAR15)*BAR15].append(row)
    complete=inc=0
    with path.open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['open_time','open','high','low','close','volume','minute_count'])
        for b in sorted(buckets):
            a=buckets[b];exp=[b+i*MIN for i in range(15)]
            if len(a)!=15 or [x[0] for x in a]!=exp:inc+=1;continue
            w.writerow([b,repr(a[0][1]),repr(max(x[2] for x in a)),repr(min(x[3] for x in a)),repr(a[-1][4]),repr(sum(x[5] for x in a)),15]);complete+=1
    return complete,inc,gaps,dups

def main():
    f=json.loads(FREEZE.read_text());assert f['status']=='FROZEN_BEFORE_PHASE5_SOURCE_ACCESS_OR_OUTCOMES';assert f['dataset']['allowed_source_years']==[2023,2024];assert f['dataset']['forbidden_source_years']==[2025,2026]
    OUT.mkdir(parents=True,exist_ok=True);PCAN.mkdir(exist_ok=True);FCAN.mkdir(exist_ok=True);price_records=[];fund_records=[];aud={}
    try:
        for s in SYMS:
            rows=[];fund=[]
            for ym in MONTHS:
                pn=f'{s}-1m-{ym}.zip';pu=f'{PBASE}/{s}/1m/{pn}';pb=get(pu);pcb=get(pu+'.CHECKSUM');ps=csum(pcb,pn);pl=sha(pb)
                if ps!=pl:raise ValueError(f'price checksum mismatch:{s}:{ym}')
                rr=list(price_rows(pb,pn.replace('.zip','.csv')));rows.extend(rr);price_records.append({'symbol':s,'month':ym,'archive_name':pn,'archive_url':pu,'local_sha256':pl,'provider_sha256':ps,'row_count':len(rr)})
                fn=f'{s}-fundingRate-{ym}.zip';fu=f'{FBASE}/{s}/{fn}';fb=get(fu);fcb=get(fu+'.CHECKSUM');fs=csum(fcb,fn);fl=sha(fb)
                if fs!=fl:raise ValueError(f'funding checksum mismatch:{s}:{ym}')
                fr=funding_rows(fb,fn.replace('.zip','.csv'));fund.extend(fr);fund_records.append({'symbol':s,'month':ym,'archive_name':fn,'archive_url':fu,'local_sha256':fl,'provider_sha256':fs,'event_count':len(fr)})
                print(s,ym,'PRICE',len(rr),'FUND',len(fr),flush=True)
            rows.sort();fund.sort()
            pp=PCAN/f'{s}_15m.csv';complete,inc,gaps,dups=aggregate15(rows,pp)
            if dups:raise ValueError(f'nonmonotonic/duplicate price:{s}:{dups}')
            if len({t for t,_ in fund})!=len(fund):raise ValueError(f'duplicate funding:{s}')
            fp=FCAN/f'{s}_funding.csv'
            with fp.open('w',newline='') as fh:
                w=csv.writer(fh,lineterminator='\n');w.writerow(['funding_time_ms','funding_rate']);w.writerows((t,repr(r)) for t,r in fund)
            aud[s]={'raw_minute_count':len(rows),'complete_15m_count':complete,'incomplete_15m_count':inc,'detected_minute_gap_count':gaps,'canonical_15m_sha256':sha(pp.read_bytes()),'funding_event_count':len(fund),'canonical_funding_sha256':sha(fp.read_bytes())}
        pre={'campaign_id':'HTF-DIAMOND-HUNT-001','phase':'PHASE_5_EXACT_RULE_FORWARD_HOLDOUT','provider':'Binance public data','market':'USD-M perpetual futures','allowed_years':[2023,2024],'price_records':sorted(price_records,key=lambda x:(x['symbol'],x['month'])),'funding_records':sorted(fund_records,key=lambda x:(x['symbol'],x['month'])),'audits':aud}
        fp=chash(pre);out={'status':'SOURCE_DATA_PASS',**pre,'source_fingerprint':fp,'signal_calculation_performed':False,'return_calculation_performed':False,'outcome_evaluation_performed':False,'access_2025_performed':False,'access_2026_performed':False}
        RECEIPT.write_text(json.dumps(out,indent=2,sort_keys=True));print(json.dumps({'status':'SOURCE_DATA_PASS','source_fingerprint':fp,'audits':aud},indent=2,sort_keys=True));return 0
    except Exception as e:
        out={'status':'BLOCKED_PRE_OUTCOME_SOURCE_GATE','reason':f'{type(e).__name__}: {e}','outcome_evaluation_performed':False,'access_2025_performed':False,'access_2026_performed':False};RECEIPT.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
