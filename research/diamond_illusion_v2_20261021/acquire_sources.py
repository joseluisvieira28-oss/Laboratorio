import pathlib,urllib.request,concurrent.futures,hashlib,json,datetime,time
P=pathlib.Path(__file__).parent;S=P/'source_archives';S.mkdir(exist_ok=True)
pinned={x['file']:x for x in json.loads((P/'source_manifest.json').read_text())} if (P/'source_manifest.json').exists() else {}
items=[]
for year,interval in [(2024,'1d'),(2025,'1m'),(2025,'1d')]:
 for month in range(1,13):
  name=f'BTCUSDT-{interval}-{year}-{month:02}.zip';items.append((name,'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/'+interval+'/'+name))
def get(x):
 name,url=x;dest=P/'etf_source_2025' if '1d-2025' in name else S;dest.mkdir(exist_ok=True);f=dest/name
 for attempt in range(3):
  try:
   if not f.exists():
    req=urllib.request.Request(url,headers={'User-Agent':'Crypto-Lab-ReadOnly-Audit/2'});b=urllib.request.urlopen(req,timeout=120).read();f.write_bytes(b)
   b=f.read_bytes();cs=urllib.request.urlopen(url+'.CHECKSUM',timeout=60).read().decode();f.with_name(name+'.CHECKSUM').write_text(cs);expected=cs.split()[0];actual=hashlib.sha256(b).hexdigest();assert expected==actual
   if name in pinned:assert actual==pinned[name]['sha256']
   return {'file':name,'path':f.relative_to(P).as_posix(),'url':url,'bytes':len(b),'sha256':actual,'provider_checksum':expected,'verified':True,'year':int(name[-11:-7])}
  except Exception as e:
   if attempt==2:return {'file':name,'url':url,'error':str(e),'verified':False}
   time.sleep(1)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 result=list(ex.map(get,items))
(P/'source_manifest.json').write_text(json.dumps(result,indent=2));print('ARCHIVES',len(result),'OK',sum(x.get('verified',False) for x in result),'BYTES',sum(x.get('bytes',0) for x in result));print([x for x in result if not x.get('verified')])
# Contract specification only. No ticker, BBO, mark price, index or funding current outcome endpoints.
if (P/'contract_metadata.json').exists():
 print('Retaining frozen contract metadata.');raise SystemExit(0)
url='https://contract.mexc.com/api/v1/contract/detail?symbol=BTC_USDT'
try:
 b=urllib.request.urlopen(url,timeout=45).read();d=json.loads(b);data=d.get('data');data=next((x for x in data if x.get('symbol')=='BTC_USDT'),None) if isinstance(data,list) else data
 keep=['symbol','contractSize','minVol','volUnit','volScale','priceUnit','priceScale','minLeverage','maxLeverage','makerFeeRate','takerFeeRate','apiAllowed','state','minNotional','minCost']
 out={'url':url,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata_only':True,'http_sha256':hashlib.sha256(b).hexdigest(),'success':d.get('success'),'parameters':{k:data.get(k) for k in keep if k in data},'warning':'public default rates are not account or historical fee certification'}
except Exception as e:out={'url':url,'error':str(e),'metadata_only':True}
(P/'contract_metadata.json').write_text(json.dumps(out,indent=2));print('SPEC',out)
