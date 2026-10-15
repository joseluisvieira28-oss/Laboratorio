from __future__ import annotations
import hashlib, html, json, math, os, re, urllib.request
from collections import defaultdict
from html.parser import HTMLParser

LAB_ID='CROSS-ASSET-VOL-STRESS-001'
MVE_ID='CAVS-VXSETTLE-W1-001'
YEARS=list(range(2018,2025))
OUT='artifacts/cross_asset_vol_stress_source_v01'
os.makedirs(OUT,exist_ok=True)
RAW=os.path.join(OUT,'raw'); os.makedirs(RAW,exist_ok=True)

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.x=[]
    def handle_data(self,d):
        if d and d.strip(): self.x.append(d.strip())

def fetch(url:str)->bytes:
    if '/2025/' in url or '/2026/' in url: raise RuntimeError('PROTECTED_YEAR_URL')
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html,application/xhtml+xml'})
    with urllib.request.urlopen(req,timeout=45) as r:
        b=r.read()
        if len(b)<1000: raise RuntimeError('SOURCE_TOO_SMALL')
        return b

def parse_year(b:bytes,year:int):
    s=b.decode('utf-8','replace')
    p=Text(); p.feed(s)
    text=' '.join(p.x)
    start=text.find('VX - Cboe Volatility Index (VX) Futures')
    if start<0: raise RuntimeError(f'VX_SECTION_NOT_FOUND:{year}')
    # VXM normally follows VX. If template differs, cap section length rather than parse other products.
    end=text.find('VXM -',start+1)
    section=text[start:end if end>start else min(len(text),start+50000)]
    # Normalize Unicode punctuation/nbsp emitted by site templates.
    section=html.unescape(section).replace('\xa0',' ')
    pat=re.compile(r'\b(VX(?:\d+)?/[A-Z]\d+)\s*-\s*(20\d{2}-\d{2}-\d{2})\s*:\s*([0-9][0-9,]*(?:\.[0-9]+)?)')
    rows=[]
    for contract,date,value in pat.findall(section):
        v=float(value.replace(',',''))
        rows.append({'year':year,'date':date,'contract':contract,'settlement':v})
    return rows, section[:2000]

raw_meta={}; parsed=[]; diagnostics=[]
for y in YEARS:
    url=f'https://www.cboe.com/us/futures/market_statistics/final_settlement_prices/{y}/'
    b=fetch(url)
    fn=f'cboe_final_settlement_prices_{y}.html'
    open(os.path.join(RAW,fn),'wb').write(b)
    rows,preview=parse_year(b,y)
    raw_meta[str(y)]={'url':url,'file':fn,'byte_count':len(b),'sha256':hashlib.sha256(b).hexdigest(),'parsed_record_count':len(rows)}
    diagnostics.append({'year':y,'parsed_record_count':len(rows),'section_preview':preview})
    parsed.extend(rows)

by_date=defaultdict(list)
for r in parsed:
    if not r['date'].startswith(str(r['year'])+'-'): raise RuntimeError('DATE_OUTSIDE_REQUESTED_YEAR')
    if not math.isfinite(r['settlement']) or r['settlement']<=0: raise RuntimeError('INVALID_SETTLEMENT')
    by_date[r['date']].append(r)

canonical=[]; identical_dupes=0; conflicts=[]
for d in sorted(by_date):
    rr=by_date[d]; vals=sorted({round(float(x['settlement']),10) for x in rr})
    if len(vals)>1:
        conflicts.append({'date':d,'records':rr}); continue
    if len(rr)>1: identical_dupes += len(rr)-1
    canonical.append({'date':d,'settlement':float(vals[0]),'contracts':sorted({x['contract'] for x in rr})})

counts={str(y):sum(1 for r in canonical if r['date'].startswith(str(y)+'-')) for y in YEARS}
checks={
 'no_conflicting_same_date_values':len(conflicts)==0,
 'each_year_ge_45':all(counts[str(y)]>=45 for y in YEARS),
 'total_ge_320':len(canonical)>=320,
 'access_2025':False,
 'access_2026':False,
 'btc_market_data_accessed':False,
 'returns_computed':False,
 'pnl_computed':False,
}
classification='SOURCE_DATA_PASS' if all(v is True for v in checks.values()) else 'SOURCE_DATA_FAILURE'
can_bytes=('date,settlement,contracts\n'+'\n'.join(f"{r['date']},{r['settlement']:.10f},{'|'.join(r['contracts'])}" for r in canonical)+'\n').encode()
open(os.path.join(OUT,'vx_settlements_2018_2024.csv'),'wb').write(can_bytes)
manifest={
 'lab_id':LAB_ID,'mve_id':MVE_ID,'classification':classification,'years':YEARS,'raw_meta':raw_meta,
 'canonical_count':len(canonical),'counts_by_year':counts,'identical_duplicate_records_canonicalized':identical_dupes,
 'conflicts':conflicts,'canonical_sha256':hashlib.sha256(can_bytes).hexdigest(),'checks':checks,
 'exchange_mutation_performed':False,'orders_submitted':False,'outcome_evaluation_performed':False,
 'diagnostics':diagnostics,
}
mb=json.dumps(manifest,sort_keys=True,indent=2).encode()
manifest['manifest_sha256']=hashlib.sha256(mb).hexdigest()
open(os.path.join(OUT,'CROSS_ASSET_VOL_STRESS_001_SOURCE_GATE_V0.1.json'),'w',encoding='utf-8').write(json.dumps(manifest,indent=2,sort_keys=True))
print(json.dumps(manifest,indent=2))
if classification!='SOURCE_DATA_PASS': raise SystemExit(2)
