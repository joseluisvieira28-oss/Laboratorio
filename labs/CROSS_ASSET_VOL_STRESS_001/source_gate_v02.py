from __future__ import annotations
import csv, hashlib, json, math, os, re, urllib.parse, urllib.request
from collections import defaultdict
from datetime import datetime

LAB_ID='CROSS-ASSET-VOL-STRESS-001'
MVE_ID='CAVS-VXSETTLE-W1-001'
YEARS=list(range(2018,2025))
OUT='artifacts/cross_asset_vol_stress_source_v02'
RAW=os.path.join(OUT,'raw')
os.makedirs(RAW,exist_ok=True)

BASE='https://www-api.cboe.com/us/futures/market_statistics/final_settlement_prices/values/futures/'
EXPECTED_PRODUCT='VX - Cboe Volatility Index (VX) Futures'

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def fetch_year(year:int)->tuple[bytes,str]:
    if year not in YEARS:
        raise RuntimeError('PROTECTED_OR_UNAUTHORIZED_YEAR')
    url=BASE+'?'+urllib.parse.urlencode({'year':str(year)})
    if '2025' in url or '2026' in url:
        raise RuntimeError('PROTECTED_YEAR_URL')
    req=urllib.request.Request(url,headers={
        'User-Agent':'Mozilla/5.0',
        'Accept':'application/json,text/plain,*/*',
        'Referer':f'https://www.cboe.com/us/futures/market_statistics/final_settlement_prices/{year}/'
    })
    with urllib.request.urlopen(req,timeout=45) as r:
        b=r.read()
        if len(b)<100:
            raise RuntimeError(f'SOURCE_TOO_SMALL:{year}')
        return b,url

def normalize_date(v)->str:
    s=str(v or '').strip()
    # Provider may use YYYY-MM-DD or timestamp-like values.
    m=re.search(r'(20\d{2})-(\d{2})-(\d{2})',s)
    if m:
        return '-'.join(m.groups())
    for fmt in ('%m/%d/%Y','%m/%d/%y'):
        try:
            return datetime.strptime(s,fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    raise RuntimeError(f'UNPARSEABLE_EXPIRE_DATE:{s}')

def parse_price(v)->float:
    if isinstance(v,(int,float)) and not isinstance(v,bool):
        x=float(v)
    else:
        s=str(v or '').replace(',','').replace('$','').strip()
        if not s:
            raise RuntimeError('EMPTY_PRICE')
        x=float(s)
    if not math.isfinite(x) or x<=0:
        raise RuntimeError(f'INVALID_PRICE:{v}')
    return x

def response_data(obj):
    # Current frontend contract uses top-level data; retain a narrow compatibility
    # for a provider wrapper that nests the same object under result.
    if isinstance(obj,dict) and isinstance(obj.get('data'),list):
        return obj['data']
    if isinstance(obj,dict) and isinstance(obj.get('data'),dict):
        d=obj['data']
        for k in ('data','products','rows'):
            if isinstance(d.get(k),list):
                return d[k]
    if isinstance(obj,dict) and isinstance(obj.get('result'),list):
        return obj['result']
    if isinstance(obj,list):
        return obj
    raise RuntimeError('UNEXPECTED_RESPONSE_SHAPE')

def product_label(p:dict)->str:
    return str(p.get('product') or p.get('name') or '').strip()

def is_vx_product(label:str)->bool:
    if label==EXPECTED_PRODUCT:
        return True
    norm=' '.join(label.upper().split())
    return norm.startswith('VX -') and 'VOLATILITY INDEX' in norm and 'FUTURES' in norm and 'MINI' not in norm

raw_meta={}
all_rows=[]
provider_diagnostics=[]
for y in YEARS:
    b,url=fetch_year(y)
    fn=f'cboe_vx_final_settlement_api_{y}.json'
    open(os.path.join(RAW,fn),'wb').write(b)
    try:
        obj=json.loads(b.decode('utf-8-sig'))
    except Exception as e:
        raise RuntimeError(f'JSON_PARSE_FAILURE:{y}:{type(e).__name__}')

    # If provider exposes selectedYear/year, it must not contradict the requested year.
    selected=None
    if isinstance(obj,dict):
        for k in ('selectedYear','selected_year','year'):
            if k in obj and obj[k] not in (None,''):
                selected=str(obj[k])
                break
    if selected is not None and str(y) not in selected:
        raise RuntimeError(f'RESPONSE_YEAR_MISMATCH:{y}:{selected}')

    products=response_data(obj)
    matches=[p for p in products if isinstance(p,dict) and is_vx_product(product_label(p))]
    if len(matches)!=1:
        labels=[product_label(p) for p in products if isinstance(p,dict)]
        raise RuntimeError(f'VX_PRODUCT_MATCH_COUNT:{y}:{len(matches)}:labels={labels[:30]}')
    vx=matches[0]
    monthly=vx.get('monthly_settlement_prices') or []
    weekly=vx.get('weekly_settlement_prices') or []
    if not isinstance(monthly,list) or not isinstance(weekly,list):
        raise RuntimeError(f'INVALID_SETTLEMENT_LISTS:{y}')
    rows=[]
    for frequency,seq in (('monthly',monthly),('weekly',weekly)):
        for r in seq:
            if not isinstance(r,dict):
                raise RuntimeError(f'INVALID_SETTLEMENT_RECORD:{y}')
            d=normalize_date(r.get('expire_date'))
            if not d.startswith(str(y)+'-'):
                raise RuntimeError(f'DATE_OUTSIDE_REQUESTED_YEAR:{y}:{d}')
            x=parse_price(r.get('price'))
            symbol=str(r.get('symbol_name') or '').strip()
            method=str(r.get('calculation_method') or '').strip()
            if not symbol:
                raise RuntimeError(f'MISSING_SYMBOL:{y}:{d}')
            row={'year':y,'date':d,'symbol_name':symbol,'settlement':x,'calculation_method':method,'frequency':frequency}
            rows.append(row)
            all_rows.append(row)
    raw_meta[str(y)]={
        'url':url,'file':fn,'byte_count':len(b),'sha256':sha(b),
        'provider_product_label':product_label(vx),'monthly_count':len(monthly),'weekly_count':len(weekly),'parsed_count':len(rows),
        'selected_year_field':selected
    }
    provider_diagnostics.append({'year':y,'monthly_count':len(monthly),'weekly_count':len(weekly),'sample':rows[:3]})

by_date=defaultdict(list)
for r in all_rows:
    by_date[r['date']].append(r)

canonical=[]
conflicts=[]
identical_duplicate_records=0
for d in sorted(by_date):
    rr=by_date[d]
    vals=sorted({round(float(r['settlement']),10) for r in rr})
    if len(vals)>1:
        conflicts.append({'date':d,'records':rr})
        continue
    if len(rr)>1:
        identical_duplicate_records += len(rr)-1
    canonical.append({
        'date':d,'settlement':float(vals[0]),
        'symbols':sorted({r['symbol_name'] for r in rr}),
        'frequencies':sorted({r['frequency'] for r in rr}),
        'calculation_methods':sorted({r['calculation_method'] for r in rr if r['calculation_method']})
    })

counts={str(y):sum(1 for r in canonical if r['date'].startswith(str(y)+'-')) for y in YEARS}
checks={
    'no_conflicting_same_date_values':len(conflicts)==0,
    'each_year_ge_45':all(counts[str(y)]>=45 for y in YEARS),
    'total_ge_320':len(canonical)>=320,
    'access_2025':False,'access_2026':False,
    'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False
}
classification='SOURCE_DATA_PASS' if all(v is True for v in checks.values()) else 'SOURCE_DATA_FAILURE'

header=['date','settlement','symbols','frequencies','calculation_methods']
lines=[','.join(header)]
for r in canonical:
    # Values are provider identifiers without commas in expected schema; JSON-encode list fields to avoid ambiguity.
    lines.append(','.join([
        r['date'],f"{r['settlement']:.10f}",
        json.dumps(r['symbols'],separators=(':', ';')).replace(',', ';'),
        json.dumps(r['frequencies'],separators=(':', ';')).replace(',', ';'),
        json.dumps(r['calculation_methods'],separators=(':', ';')).replace(',', ';')
    ]))
canonical_bytes=('\n'.join(lines)+'\n').encode()
open(os.path.join(OUT,'vx_final_settlements_2018_2024.csv'),'wb').write(canonical_bytes)

base_manifest={
    'lab_id':LAB_ID,'mve_id':MVE_ID,'classification':classification,'source_contract_version':'V0.2',
    'years':YEARS,'raw_meta':raw_meta,'raw_record_count':len(all_rows),'canonical_count':len(canonical),
    'counts_by_year':counts,'identical_duplicate_records_canonicalized':identical_duplicate_records,
    'conflicts':conflicts,'canonical_sha256':sha(canonical_bytes),'checks':checks,
    'provider_diagnostics':provider_diagnostics,
    'network_access_performed':True,'exchange_mutation_performed':False,'orders_submitted':False,'outcome_evaluation_performed':False
}
manifest_material=json.dumps(base_manifest,sort_keys=True,separators=(',',':')).encode()
base_manifest['manifest_sha256']=sha(manifest_material)
open(os.path.join(OUT,'CROSS_ASSET_VOL_STRESS_001_SOURCE_GATE_V0.2.json'),'w',encoding='utf-8').write(json.dumps(base_manifest,indent=2,sort_keys=True))
print(json.dumps(base_manifest,indent=2))
if classification!='SOURCE_DATA_PASS':
    raise SystemExit(2)
