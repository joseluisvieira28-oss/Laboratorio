import concurrent.futures,urllib.request,json,hashlib,datetime,pathlib
base='https://www.binance.com/en/support/announcement/detail/e71da970ed29453c96018af9bf107311'
urls=[
'https://web.archive.org/cdx/search/cdx?url='+base+'&output=json&filter=statuscode:200&filter=mimetype:text/html&to=20251128062959&collapse=digest',
'https://data.binance.vision/data/futures/um/daily/metrics/ACTUSDT/ACTUSDT-metrics-2025-04-01.zip',
'https://data.binance.vision/data/futures/um/daily/markPriceKlines/ACTUSDT/1m/ACTUSDT-1m-2025-04-01.zip',
'https://data.binance.vision/data/futures/um/daily/indexPriceKlines/ACTUSDT/1m/ACTUSDT-1m-2025-04-01.zip',
'https://data.binance.vision/data/futures/um/monthly/fundingRate/ACTUSDT/ACTUSDT-fundingRate-2025-04.zip',
'https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=e71da970ed29453c96018af9bf107311',
'https://announcements.bybit.com/en/article/risk-limit-adjustment-for-xnyusdt-perpetual-contract-blt09ebc41170874c39/'
]
def run(u):
 out={'url':u,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  req=urllib.request.Request(u,method='HEAD' if 'data.binance.vision' in u else 'GET')
  with urllib.request.urlopen(req,timeout=20) as r:
   out.update(status=r.status,headers=dict(r.headers))
   if req.method=='GET':
    b=r.read();out.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    if 'article/detail/query' in u:
     d=json.loads(b)['data'];out['revision_metadata']={k:d.get(k) for k in ['publishDate','lastUpdateTime','version','code']}
    elif 'cdx' in u:out['body']=b.decode()
    else:
     pathlib.Path('/tmp/bybit_source.html').write_bytes(b);out['saved_scratch']='/tmp/bybit_source.html'
 except Exception as e:out['error']=type(e).__name__+': '+str(e)
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:rows=list(p.map(run,urls))
path=pathlib.Path(__file__).parent/'PROVENANCE_CAPABILITY_RECEIPT.json';path.write_text(json.dumps(rows,indent=2));print(json.dumps([{k:v for k,v in x.items() if k!='headers'} for x in rows],indent=2))
