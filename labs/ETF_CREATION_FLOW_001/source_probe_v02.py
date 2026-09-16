from __future__ import annotations
import hashlib,json,os,re,urllib.parse,urllib.request

LAB='ETF-CREATION-FLOW-001'; MVE='ECF-IBIT-SHARES-1D-001'
DATES=['2024-03-28','2024-06-28','2024-09-30','2024-12-30']
BASE='https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf/1467271812596.ajax'
OUT='artifacts/etf_creation_flow_source_probe_v02'; os.makedirs(OUT,exist_ok=True)

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json,text/javascript,*/*;q=0.1','X-Requested-With':'XMLHttpRequest','Referer':'https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf'})
    with urllib.request.urlopen(req,timeout=45) as r: return r.read(),dict(r.headers)

def json_from_bytes(b):
    t=b.decode('utf-8-sig','replace').strip()
    i=t.find('{'); j=t.rfind('}')
    if i<0 or j<i: raise ValueError('NO_JSON_OBJECT')
    return json.loads(t[i:j+1]),t

def walk(x,path='$'):
    if isinstance(x,dict):
        for k,v in x.items():
            yield path+'.'+str(k),k,v
            yield from walk(v,path+'.'+str(k))
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from walk(v,f'{path}[{i}]')

def num(v):
    if isinstance(v,(int,float)) and not isinstance(v,bool): return float(v)
    if isinstance(v,str):
        s=v.replace(',','').replace('$','').strip()
        try: return float(s)
        except: return None
    return None

probes=[]
for d in DATES:
    qs=urllib.parse.urlencode({'fileType':'json','tab':'all','asOfDate':d.replace('-','')})
    url=BASE+'?'+qs
    rec={'requested_date':d,'url':url}
    try:
        b,h=fetch(url); obj,text=json_from_bytes(b)
        share_hits=[]; date_hits=[]
        for path,k,v in walk(obj):
            kl=str(k).lower().replace('_',' ').replace('-',' ')
            if 'share' in kl and 'outstand' in kl:
                nv=num(v)
                share_hits.append({'path':path,'key':str(k),'value':v,'numeric':nv})
            sv=str(v) if isinstance(v,(str,int)) else ''
            if d in sv or d.replace('-','') in sv:
                date_hits.append({'path':path,'key':str(k),'value':v})
        exact_text=(d in text or d.replace('-','') in text)
        numeric=[x for x in share_hits if x['numeric'] is not None and x['numeric']>0]
        rec.update({'http_ok':True,'byte_count':len(b),'sha256':hashlib.sha256(b).hexdigest(),'content_type':h.get('Content-Type'),'top_level_keys':list(obj)[:40] if isinstance(obj,dict) else [],'requested_date_visible':bool(date_hits or exact_text),'date_hits':date_hits[:20],'shares_outstanding_hits':share_hits[:20],'numeric_share_hit_count':len(numeric),'pass':bool((date_hits or exact_text) and numeric)})
    except Exception as e:
        rec.update({'http_ok':False,'error':type(e).__name__+':'+str(e),'pass':False})
    probes.append(rec)

passes=[p for p in probes if p['pass']]
quarters={(int(p['requested_date'][:4]),(int(p['requested_date'][5:7])-1)//3+1) for p in passes}
classification='SOURCE_FEASIBILITY_PASS' if len(passes)>=3 and len(quarters)>=3 else 'SOURCE_FEASIBILITY_BLOCKED'
receipt={'lab_id':LAB,'mve_id':MVE,'classification':classification,'exact_pass_count':len(passes),'distinct_quarters':len(quarters),'probes':probes,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'access_2025':False,'access_2026':False,'outcome_evaluation_performed':False}
open(os.path.join(OUT,'ETF_CREATION_FLOW_001_SOURCE_FEASIBILITY_V0.2.json'),'w',encoding='utf-8').write(json.dumps(receipt,indent=2,sort_keys=True))
print(json.dumps(receipt,indent=2))
if classification!='SOURCE_FEASIBILITY_PASS': raise SystemExit(2)
