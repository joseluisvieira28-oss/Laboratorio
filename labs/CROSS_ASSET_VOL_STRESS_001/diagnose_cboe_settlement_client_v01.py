from __future__ import annotations
import hashlib,json,os,re,urllib.parse,urllib.request

OUT='artifacts/cross_asset_vol_stress_client_diag_v01'; os.makedirs(OUT,exist_ok=True)
PAGE='https://www.cboe.com/us/futures/market_statistics/final_settlement_prices/2018/'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html,application/javascript,*/*'})
    with urllib.request.urlopen(req,timeout=45) as r: return r.read()

html=fetch(PAGE)
text=html.decode('utf-8','replace')
srcs=sorted(set(re.findall(r'<script[^>]+src="([^"]+\.js)"',text)))
records=[]; hits=[]
patterns=('settlement','final_settlement','final-settlement','settlement_price','settlementPrice','futures/final','download.*csv','market_statistics')
for src in srcs:
    u=urllib.parse.urljoin(PAGE,src)
    b=fetch(u); t=b.decode('utf-8','replace')
    rec={'url':u,'byte_count':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    records.append(rec)
    low=t.lower()
    if any(re.search(p,low,re.I) for p in patterns):
        snippets=[]
        for needle in ('settlement','futures/final','csv','market_statistics'):
            pos=0
            while True:
                i=low.find(needle.lower(),pos)
                if i<0: break
                snippets.append(t[max(0,i-400):i+900])
                pos=i+len(needle)
                if len(snippets)>=30: break
            if len(snippets)>=30: break
        hits.append({'url':u,'snippets':snippets[:30]})

out={
 'classification':'CLIENT_ROUTE_DIAGNOSTIC_COMPLETE',
 'page_url':PAGE,'page_sha256':hashlib.sha256(html).hexdigest(),'script_count':len(srcs),'scripts':records,'hits':hits,
 'settlement_data_endpoint_requested':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,
 'access_2025':False,'access_2026':False,'outcome_evaluation_performed':False
}
open(os.path.join(OUT,'CBOE_SETTLEMENT_CLIENT_ROUTE_DIAGNOSTIC_V0.1.json'),'w',encoding='utf-8').write(json.dumps(out,indent=2))
print(json.dumps({'classification':out['classification'],'script_count':len(srcs),'hit_bundles':[h['url'] for h in hits]},indent=2))
