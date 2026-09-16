from __future__ import annotations
import csv, hashlib, io, json, os, re, urllib.parse, urllib.request
from datetime import datetime

LAB_ID='ETF-CREATION-FLOW-001'
MVE_ID='ECF-IBIT-SHARES-1D-001'
DATES=['2024-03-28','2024-06-28','2024-09-30','2024-12-30']
BASE='https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf'
OUT='artifacts/etf_creation_flow_source_probe_v01'
os.makedirs(OUT, exist_ok=True)

def sha(b: bytes)->str: return hashlib.sha256(b).hexdigest()

def fetch(url:str)->bytes:
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Accept':'text/csv,text/plain,*/*'})
    with urllib.request.urlopen(req, timeout=45) as r:
        b=r.read()
        if len(b)<50: raise RuntimeError('TOO_SMALL')
        return b

def parse_payload(b:bytes):
    txt=b.decode('utf-8-sig','replace')
    lines=txt.splitlines()
    asof=None; shares=None
    for line in lines[:20]:
        row=next(csv.reader([line])) if line.strip() else []
        if not row: continue
        key=row[0].strip().lower()
        if key.startswith('fund holdings as of') and len(row)>1:
            raw=row[1].strip()
            for fmt in ('%b %d, %Y','%b %d %Y','%Y-%m-%d'):
                try:
                    asof=datetime.strptime(raw,fmt).strftime('%Y-%m-%d'); break
                except ValueError: pass
        if key.startswith('shares outstanding') and len(row)>1:
            raw=row[1].replace(',','').strip()
            try: shares=float(raw)
            except ValueError: pass
    return asof,shares,txt[:500]

routes={
 'ajax': lambda d: BASE+'/1467271812596.ajax?'+urllib.parse.urlencode({'fileType':'csv','fileName':'IBIT_holdings','dataType':'fund','asOfDate':d.replace('-','')}),
 'latest_query': lambda d: BASE+'/latest-holdings.csv?'+urllib.parse.urlencode({'asOfDate':d.replace('-','')})
}
results=[]
for route,fn in routes.items():
    for d in DATES:
        rec={'route':route,'requested_date':d,'url':fn(d)}
        try:
            b=fetch(rec['url']); asof,shares,preview=parse_payload(b)
            rec.update({'http_ok':True,'byte_count':len(b),'sha256':sha(b),'returned_asof':asof,'shares_outstanding':shares,'exact_date_match':asof==d,'numeric_shares':shares is not None,'preview':preview})
        except Exception as e:
            rec.update({'http_ok':False,'error':type(e).__name__+':'+str(e),'exact_date_match':False,'numeric_shares':False})
        results.append(rec)

route_summary={}
for route in routes:
    rr=[r for r in results if r['route']==route]
    exact=[r for r in rr if r.get('exact_date_match') and r.get('numeric_shares')]
    qs=sorted({(int(r['requested_date'][:4]),(int(r['requested_date'][5:7])-1)//3+1) for r in exact})
    route_summary[route]={'exact_count':len(exact),'distinct_quarters':len(qs),'pass':len(exact)>=3 and len(qs)>=3}
passed=[k for k,v in route_summary.items() if v['pass']]
classification='SOURCE_FEASIBILITY_PASS' if passed else 'SOURCE_FEASIBILITY_BLOCKED'
receipt={
 'lab_id':LAB_ID,'mve_id':MVE_ID,'classification':classification,'passed_routes':passed,'route_summary':route_summary,'probes':results,
 'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'access_2025':False,'access_2026':False,'outcome_evaluation_performed':False
}
raw=json.dumps(receipt,sort_keys=True,indent=2).encode()
open(os.path.join(OUT,'ETF_CREATION_FLOW_001_SOURCE_FEASIBILITY_V0.1.json'),'wb').write(raw)
print(json.dumps(receipt,indent=2))
if classification!='SOURCE_FEASIBILITY_PASS': raise SystemExit(2)
