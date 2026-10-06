import concurrent.futures,urllib.request,json,hashlib,pathlib
urls=[
'https://web.archive.org/cdx/search/cdx?url=www.binance.com/en/support/announcement/detail/4d5f22d4048345d4b7cbb7920d2af2ee&output=json&filter=statuscode:200&to=20250401102959',
'https://web.archive.org/cdx/search/cdx?url=www.binance.com/en/support/announcement/detail/0806a835368b409e8d5ebd84d9fdc4ed&output=json&filter=statuscode:200&to=20240610055959',
'https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=ea3fdf1c24c048dba00d8083f9248fd6',
'https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=14d6edbcf4254d86aeb5e9cfbceb2db6'
]
def f(u):
 out={'url':u}
 try:
  with urllib.request.urlopen(u,timeout=20) as r:
   b=r.read();out.update(status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
   if 'binance.com' in u and 'bapi' in u:
    d=json.loads(b)['data'];out.update(metadata={k:d.get(k) for k in ['publishDate','lastUpdateTime','version','code']})
   else:out['body']=b.decode()
 except Exception as e:out['error']=type(e).__name__+': '+str(e)
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:out=list(p.map(f,urls))
pathlib.Path('lab/research/cex_margin_collateral_forced_deleveraging/ARCHIVE_REVISION_RECEIPT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
