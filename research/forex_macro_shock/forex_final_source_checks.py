import sys,concurrent.futures,json,urllib.request,urllib.error,hashlib,ssl
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).parent))
import source_gate_v01 as s
tasks=[('MEXC_legacy_old','https://contract.mexc.com/api/v1/contract/kline/EUR_USDT?interval=Min1&start=1745884800&end=1745888400'),('MEXC_Min5_old',s.BASE+'/kline/EUR_USDT?interval=Min5&start=1745884800&end=1745888400')]
for day in ['2026-09-08','2026-09-09','2026-09-16']:
 st=int(datetime.fromisoformat(day+'T00:00:00+00:00').timestamp());tasks.append(('MEXC_'+day,s.BASE+'/kline/EUR_USDT?interval=Min1&start='+str(st)+'&end='+str(st+3600)))
def get(x):
 label,url=x;start=datetime.now(timezone.utc).isoformat()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CryptoLab-Forex-SourceGate/0.1'}),timeout=30) as r:b=r.read();status=r.status;h=dict(r.headers)
 except urllib.error.HTTPError as e:b=e.read();status=e.code;h=dict(e.headers)
 except Exception as e:return {'label':label,'url':url,'error':str(e),'started_at_utc':start}
 p=s.RAW/(hashlib.sha256(b).hexdigest()+'.bin');p.write_bytes(b)
 r={'label':label,'url':url,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'headers':h,'started_at_utc':start,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'raw_path':str(p.relative_to(s.ROOT))}
 try:
  j=json.loads(b);ts=j.get('data',{}).get('time',[]);r['timestamp_check']={'success':j.get('success'),'rows':len(ts),'first':min(ts) if ts else None,'last':max(ts) if ts else None}
 except Exception as e:r['parse_error']=str(e)
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:rs=list(p.map(get,tasks))
(s.OUT/'FINAL_SOURCE_CHECKS_V01.json').write_text(json.dumps({'requests':rs,'sample_event_prices_opened':False,'burned_source_dates':['2025-04-29','2026-09-08','2026-09-09','2026-09-16']},indent=2),encoding='utf-8')
print(json.dumps([{k:r.get(k) for k in ['label','status','error','timestamp_check','parse_error']} for r in rs],indent=2))
