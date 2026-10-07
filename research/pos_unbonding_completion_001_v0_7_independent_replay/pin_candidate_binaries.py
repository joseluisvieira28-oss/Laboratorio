import json,pathlib,urllib.request,hashlib,concurrent.futures,datetime
P=pathlib.Path(__file__).resolve().parent; dest=P.parent.parent.parent/'coreum-replay-binaries';dest.mkdir(exist_ok=True)
o=json.loads((P/'historical_version_inventory.json').read_text())
def fetch(v):
 a=next(x for x in v['assets'] if x['name']=='cored-linux-amd64');r={'tag':v['tag'],'source_commit':v['source_commit'],'url':a['browser_download_url'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executed':False}
 try:
  p=dest/(v['tag']+'-cored-linux-amd64');h=hashlib.sha256();n=0
  with urllib.request.urlopen(urllib.request.Request(r['url'],headers={'User-Agent':'Laboratorio-Coreum-Replay-V07'}),timeout=45) as response,p.open('wb') as f:
   while True:
    b=response.read(1024*1024)
    if not b:break
    f.write(b);h.update(b);n+=len(b)
  r.update(status='DOWNLOADED',sha256=h.hexdigest(),bytes=n,size_matches_release=n==a['size'],local_file=str(p))
 except Exception as e:r.update(status='FAILED',error=str(e))
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(fetch,[x for x in o['versions'] if x['tag'] in ['v1.0.0','v2.0.2','v3.0.3']]))
(P/'binary_receipts.json').write_text(json.dumps({'candidates_not_proven_activation_sequence':True,'records':r},indent=2));print(json.dumps(r,indent=2))
