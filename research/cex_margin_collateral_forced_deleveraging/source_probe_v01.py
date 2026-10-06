"""Public source-only census; no market outcomes or private endpoints."""
import concurrent.futures, datetime, hashlib, json, pathlib, re, time, urllib.request
ROOT=pathlib.Path(__file__).parent
START=1704067200000; END=1767225600000
PAT=re.compile(r'collateral|leverage.*margin|margin.*tier|position.*limit|margin.*remov|remov.*margin|risk.*limit',re.I)
def fetch(url):
    attempts=[]
    for attempt in range(2):
        try:
            with urllib.request.urlopen(url,timeout=20) as r:
                raw=r.read(); obj=json.loads(raw)
                if obj.get('code')!='000000': raise ValueError(str(obj.get('code')))
                return obj, {'url':url,'status':r.status,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'attempts':attempts}
        except Exception as e: attempts.append(type(e).__name__+': '+str(e))
    return None,{'url':url,'errors':attempts}
def scan(cat):
    pages=[]; rows=[]; reached=False
    for page in range(1,101):
        u=f'https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId={cat}&pageNo={page}&pageSize=50'
        d,receipt=fetch(u);pages.append(receipt)
        if d is None: break
        cs=d.get('data',{}).get('catalogs',[])
        a=next((c.get('articles',[]) for c in cs if c['catalogId']==cat),[])
        if not a: reached=True;break
        rows.extend(x for x in a if START<=x['releaseDate']<END)
        print('catalog',cat,'page',page,'last',datetime.datetime.fromtimestamp(a[-1]['releaseDate']/1000,datetime.timezone.utc).isoformat(),flush=True)
        if min(x['releaseDate'] for x in a)<START: reached=True;break
    return {'catalog':cat,'reached_lower_bound':reached,'pages':pages,'articles':rows}
def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: catalogs=list(pool.map(scan,[48,49,161,157]))
    allrows={x['code']:x for c in catalogs for x in c['articles']}
    candidates=[x for x in allrows.values() if PAT.search(x['title'])]
    data={'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'market_outcomes_opened':False,'catalogs':catalogs,'candidates':candidates}
    (ROOT/'SOURCE_CATALOG_RECEIPT.json').write_text(json.dumps(data,indent=2))
    print('CENSUS',len(allrows),'candidates',len(candidates),'complete',all(c['reached_lower_bound'] for c in catalogs),flush=True)
    def detail(x):
        u='https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode='+x['code'];d,r=fetch(u)
        return {'catalog_entry':x,'transport':r,'data':d.get('data') if d else None,'adjudication':'PENDING_SOURCE_PROVENANCE_NOT_ACCEPTED'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: details=list(pool.map(detail,candidates))
    (ROOT/'SOURCE_DETAIL_RECEIPT.json').write_text(json.dumps(details,indent=2))
    print('DETAILS',len(details),'success',sum(x['data'] is not None for x in details),flush=True)
if __name__=='__main__': main()
