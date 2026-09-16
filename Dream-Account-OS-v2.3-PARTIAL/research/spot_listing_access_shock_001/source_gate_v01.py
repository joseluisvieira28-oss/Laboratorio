import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / 'FROZEN_PROTOCOL_V01.json'
OUTDIR = HERE / 'source_evidence'
OUT = OUTDIR / 'SLAS_SOURCE_GATE_V01.json'
S3 = 'https://s3-ap-northeast-1.amazonaws.com/data.binance.vision'
DV = 'https://data.binance.vision'
SPOT_ROOT = 'data/spot/monthly/klines/'
FUT_ROOT = 'data/futures/um/monthly/klines/'
YEARS = (2023, 2024)
BOUNDARY_MONTH = '2022-12'
UA = {'User-Agent': 'Mozilla/5.0 SLAS-BINANCE-SPOT-AFTER-PERP-001/1.0'}

GUARDS = {
    'mode': 'SOURCE_GATE_ONLY',
    'market_price_values_parsed': False,
    'ohlc_parsed': False,
    'returns_computed': False,
    'pnl_computed': False,
    'funding_opened': False,
    'year_2025_requested': False,
    'year_2026_requested': False,
    'live_trading': False,
    'exchange_mutation': False,
    'orders': False,
}

class SourceBlocked(RuntimeError): pass
class IntegrityFailure(RuntimeError): pass

def lname(tag): return tag.rsplit('}',1)[-1]

def get(url, attempts=4, allow_404=False):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=35) as r: return r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code==404: return None
            last=e
        except Exception as e: last=e
        time.sleep(0.35*(2**i))
    raise last

def parse_xml(raw):
    try: return ET.fromstring(raw)
    except Exception as e: raise SourceBlocked(f'XML_PARSE:{type(e).__name__}') from e

def root_symbols(root_prefix):
    out=[]; marker=None; pages=0
    while True:
        q={'prefix':root_prefix,'delimiter':'/','max-keys':'1000'}
        if marker: q['marker']=marker
        root=parse_xml(get(S3+'?'+urllib.parse.urlencode(q))); pages+=1
        if any(lname(x.tag)=='Contents' for x in root.iter()):
            raise SourceBlocked('ROOT_LISTING_RETURNED_OBJECT_CONTENTS')
        prefixes=[]
        for cp in root.iter():
            if lname(cp.tag)!='CommonPrefixes': continue
            p=next((c.text for c in cp if lname(c.tag)=='Prefix'),None)
            if p: prefixes.append(p)
        for p in prefixes:
            sym=p[len(root_prefix):-1] if p.startswith(root_prefix) and p.endswith('/') else ''
            if re.fullmatch(r'[A-Z0-9]{2,40}USDT',sym): out.append(sym)
        trunc=next((x.text for x in root.iter() if lname(x.tag)=='IsTruncated'),'false')=='true'
        if not trunc: break
        nm=next((x.text for x in root.iter() if lname(x.tag)=='NextMarker' and x.text),None)
        marker=nm or (prefixes[-1] if prefixes else None)
        if not marker or pages>20: raise SourceBlocked('ROOT_PAGINATION_FAILURE')
    return sorted(set(out)),pages

def bounded_keys(prefix):
    allowed = (BOUNDARY_MONTH in prefix) or ('-2023-' in prefix) or ('-2024-' in prefix)
    if not allowed: raise RuntimeError(f'UNBOUNDED_OR_PROTECTED_PREFIX:{prefix}')
    root=parse_xml(get(S3+'?'+urllib.parse.urlencode({'prefix':prefix,'max-keys':'1000'})))
    keys=[]
    for c in root.iter():
        if lname(c.tag)!='Contents': continue
        k=next((x.text for x in c if lname(x.tag)=='Key'),None)
        if not k: continue
        if '-2025-' in k: GUARDS['year_2025_requested']=True; raise RuntimeError('PROTECTED_2025_KEY')
        if '-2026-' in k: GUARDS['year_2026_requested']=True; raise RuntimeError('PROTECTED_2026_KEY')
        keys.append(k)
    return keys

def monthly_keys(root_prefix,symbol):
    months=[]
    b=f'{root_prefix}{symbol}/1m/{symbol}-1m-{BOUNDARY_MONTH}'
    for k in bounded_keys(b):
        if k.endswith('.zip'): months.append(BOUNDARY_MONTH)
    for y in YEARS:
        p=f'{root_prefix}{symbol}/1m/{symbol}-1m-{y}-'
        for k in bounded_keys(p):
            m=re.fullmatch(re.escape(f'{root_prefix}{symbol}/1m/{symbol}-1m-')+r'(20\d\d-\d\d)\.zip',k)
            if m and int(m.group(1)[:4]) in YEARS: months.append(m.group(1))
    return sorted(set(months))

def path(root_prefix,symbol,ym):
    if ym[:4] not in {'2022','2023','2024'}: raise RuntimeError('PROTECTED_YEAR_PATH')
    return f'{root_prefix}{symbol}/1m/{symbol}-1m-{ym}.zip'

def parse_checksum(raw,name):
    if raw is None: return None
    parts=raw.decode('utf-8','replace').strip().split()
    if not parts: raise IntegrityFailure(f'EMPTY_CHECKSUM:{name}')
    dg=parts[0].lower()
    if not re.fullmatch(r'[0-9a-f]{64}',dg): raise IntegrityFailure(f'BAD_CHECKSUM:{name}')
    return dg

def verified_zip(root_prefix,symbol,ym):
    p=path(root_prefix,symbol,ym); name=p.rsplit('/',1)[-1]
    cb=get(f'{DV}/{p}.CHECKSUM',allow_404=True)
    if cb is None: return None
    official=parse_checksum(cb,name); z=get(f'{DV}/{p}')
    actual=hashlib.sha256(z).hexdigest()
    if actual!=official: raise IntegrityFailure(f'SHA256_MISMATCH:{p}')
    return {'bytes':z,'sha256':actual,'path':p}

def first_timestamp(zbytes):
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        bad=z.testzip()
        if bad: raise IntegrityFailure(f'ZIP_CRC:{bad}')
        names=[n for n in z.namelist() if not n.endswith('/')]
        if len(names)!=1: raise IntegrityFailure('ZIP_MEMBER_COUNT')
        with z.open(names[0]) as f:
            w=io.TextIOWrapper(f,encoding='utf-8-sig',errors='replace',newline='')
            for row in csv.reader(w):
                if not row: continue
                x=str(row[0]).strip()
                if x.lower() in {'open_time','opentime'}: continue
                if not re.fullmatch(r'\d{10,18}',x): raise IntegrityFailure('FIRST_FIELD_NOT_TIMESTAMP')
                n=int(x)
                sec=n/1_000_000 if n>10**14 else n/1000 if n>10**11 else float(n)
                return datetime.fromtimestamp(sec,tz=timezone.utc)
    raise IntegrityFailure('NO_DATA_ROW')

def excluded_multiplier(sym):
    base=sym[:-4]
    return base.startswith('1000') or base.startswith('10000') or base.startswith('1000000')

def classify(sym):
    try:
        if excluded_multiplier(sym): return {'kind':'excluded_multiplier','symbol':sym}
        sm=monthly_keys(SPOT_ROOT,sym)
        # A December-2022 archive proves this was already a continuously observable spot market at the research boundary.
        if BOUNDARY_MONTH in sm: return {'kind':'boundary_old_spot','symbol':sym}
        research_spot=[m for m in sm if m[:4] in {'2023','2024'}]
        if not research_spot: return {'kind':'no_spot_event','symbol':sym}
        spot_month=research_spot[0]
        sz=verified_zip(SPOT_ROOT,sym,spot_month)
        if not sz: return {'kind':'technical','symbol':sym,'reason':'SPOT_ZIP_MISSING_AFTER_INDEX'}
        spot_ts=first_timestamp(sz['bytes'])
        if spot_ts.year not in YEARS: return {'kind':'technical','symbol':sym,'reason':'SPOT_FIRST_TS_OUTSIDE_WINDOW'}

        fm=monthly_keys(FUT_ROOT,sym)
        prior=[m for m in fm if m<=spot_month]
        if not prior:
            return {'kind':'reject','symbol':sym,'spot_event':spot_ts.isoformat().replace('+00:00','Z'),'reason':'NO_PREEXISTING_EXACT_USDT_PERP'}
        fut_month=prior[0]
        fz=verified_zip(FUT_ROOT,sym,fut_month)
        if not fz: return {'kind':'technical','symbol':sym,'reason':'FUT_ZIP_MISSING_AFTER_INDEX'}
        fut_ts=first_timestamp(fz['bytes'])
        age=spot_ts-fut_ts
        if age < timedelta(hours=24):
            return {'kind':'reject','symbol':sym,'spot_event':spot_ts.isoformat().replace('+00:00','Z'),'futures_first_observable':fut_ts.isoformat().replace('+00:00','Z'),'perp_age_hours':age.total_seconds()/3600,'reason':'PERP_AGE_LT_24H'}
        return {
            'kind':'qualified','symbol':sym,
            'event_timestamp_utc':spot_ts.isoformat().replace('+00:00','Z'),
            'event_year':spot_ts.year,
            'spot_first_month':spot_month,'spot_zip_path':sz['path'],'spot_zip_sha256':sz['sha256'],
            'futures_first_observable_utc':fut_ts.isoformat().replace('+00:00','Z'),
            'futures_proof_month':fut_month,'futures_zip_path':fz['path'],'futures_zip_sha256':fz['sha256'],
            'perp_age_hours_at_event':age.total_seconds()/3600,
        }
    except SourceBlocked as e: return {'kind':'source_blocked','symbol':sym,'reason':str(e)}
    except IntegrityFailure as e: return {'kind':'technical','symbol':sym,'reason':str(e)}
    except Exception as e: return {'kind':'technical','symbol':sym,'reason':f'{type(e).__name__}:{e}'}

def main():
    p=json.loads(PROTOCOL.read_text())
    assert p['status']=='FROZEN_PRE_OUTCOME'
    assert p['source']['discovery_years']==[2023,2024]
    assert p['source']['no_2025_access_before_discovery_pass'] is True
    assert p['source']['no_2026_access_before_independent_validation_pass'] is True
    try:
        symbols,pages=root_symbols(SPOT_ROOT)
    except Exception as e:
        rec={'classification':'SOURCE_ACCESS_BLOCKED','reason':f'{type(e).__name__}:{e}','guards':GUARDS}
        OUTDIR.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({'receipt':rec,'qualified_events':[]},indent=2,sort_keys=True)+'\n'); print(json.dumps(rec,indent=2)); return
    q=[]; rejected=[]; technical=[]; source_blocks=[]; counts={}
    with ThreadPoolExecutor(max_workers=28) as ex:
        futs={ex.submit(classify,s):s for s in symbols}
        for f in as_completed(futs):
            r=f.result(); k=r['kind']; counts[k]=counts.get(k,0)+1
            if k=='qualified': q.append(r)
            elif k=='reject': rejected.append(r)
            elif k=='technical': technical.append(r)
            elif k=='source_blocked': source_blocks.append(r)
    q=sorted(q,key=lambda x:(x['event_timestamp_utc'],x['symbol']))
    yc={str(y):sum(1 for x in q if x['event_year']==y) for y in YEARS}
    mins=p['source_gate']
    if source_blocks: classification='SOURCE_ACCESS_BLOCKED'
    elif technical: classification='TECHNICAL_FAILURE'
    elif len(q)<mins['qualified_events_min'] or len({x['symbol'] for x in q})<mins['distinct_symbols_min'] or yc['2023']<mins['events_2023_min'] or yc['2024']<mins['events_2024_min']:
        classification='INSUFFICIENT_SOURCE_SAMPLE'
    else: classification='SOURCE_DATA_PASS'
    rec={
        'classification':classification,
        'root_spot_exact_usdt_symbols':len(symbols),'root_pages':pages,
        'qualified_events':len(q),'qualified_distinct_symbols':len({x['symbol'] for x in q}),
        'qualified_year_counts':yc,'counts_by_kind':counts,
        'technical_count':len(technical),'source_block_count':len(source_blocks),
        'source_minimums':mins,'guards':GUARDS,
        'next_action':'Open Discovery outcomes only if SOURCE_DATA_PASS; otherwise close/fail-closed without changing thresholds.'
    }
    doc={'lab_id':p['lab_id'],'mve_id':p['mve_id'],'receipt':rec,'qualified_events':q,'rejections':sorted(rejected,key=lambda x:(x.get('spot_event',''),x['symbol'])),'technical':technical,'source_blocks':source_blocks}
    OUTDIR.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=='__main__': main()
