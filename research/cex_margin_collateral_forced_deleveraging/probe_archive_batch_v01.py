import concurrent.futures,urllib.request,json,pathlib,hashlib,datetime
p=pathlib.Path(__file__).parent;d=json.loads((p/'SOURCE_CATALOG_RECEIPT.json').read_text())
# Earliest 12 margin/collateral policy leads, selected solely by publication metadata.
a=sorted(d['candidates'],key=lambda x:(x['releaseDate'],x['code']))[:12]
def f(x):
 u='https://web.archive.org/cdx/search/cdx?url=www.binance.com/en/support/announcement/detail/'+x['code']+'&output=json&filter=statuscode:200&filter=mimetype:text/html&to=20251231235959'
 o={'article_code':x['code'],'title':x['title'],'publication_ms':x['releaseDate'],'url':u,'accepted_pre_effective_provenance':False}
 try:
  with urllib.request.urlopen(u,timeout=15) as r:
   b=r.read();o.update(status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),cdx=json.loads(b))
 except Exception as e:o['error']=type(e).__name__+': '+str(e)
 return o
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(f,a))
(p/'ARCHIVE_BATCH_RECEIPT.json').write_text(json.dumps({'selection':'earliest 12 candidate publications; no outcomes; diagnostic only, not complete archive census','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows},indent=2));print(json.dumps([{'code':x['article_code'],'status':x.get('status'),'captures':len(x.get('cdx',[]))-1 if x.get('cdx') else 0,'error':x.get('error')} for x in rows]))
