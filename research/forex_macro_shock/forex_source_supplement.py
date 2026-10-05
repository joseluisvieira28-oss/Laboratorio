import sys,json,urllib.parse,importlib.util,concurrent.futures,lzma,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import source_gate_v01 as s
old=s.fetch
# Independently documented routes of the same provider, not performance substitutions.
def request(label,url):
    if url.startswith('https://www.dukascopy.com/datafeed/'):
        original=s.BASE
        # Implement public raw fetch with the same receipt schema, no credentials.
        import urllib.request,urllib.error,hashlib,time
        from datetime import datetime,timezone
        t=time.perf_counter();start=datetime.now(timezone.utc).isoformat()
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CryptoLab-Forex-SourceGate/0.1'}),timeout=30) as r:data=r.read();status=r.status;headers=dict(r.headers)
        except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
        except Exception as e:return {'label':label,'url':url,'error':str(e),'started_at_utc':start}
        p=s.RAW/(hashlib.sha256(data).hexdigest()+'.bin');p.write_bytes(data)
        return {'label':label,'url':url,'status':status,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'headers':headers,'started_at_utc':start,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'latency_ms':1000*(time.perf_counter()-t),'raw_path':str(p.relative_to(s.ROOT))}
    return old(label,url)
tasks=[(sym+'_ticker_correct',s.BASE+'/ticker?symbol='+sym) for sym in s.SYMBOLS]
tasks += [('duka_www_hour_2025','https://www.dukascopy.com/datafeed/EURUSD/2025/03/29/00h_ticks.bi5'),('duka_www_hour_2026','https://www.dukascopy.com/datafeed/EURUSD/2026/09/02/00h_ticks.bi5'),('duka_datafeed_day_2025','https://datafeed.dukascopy.com/datafeed/EURUSD/2025/03/29_ticks.bi5'),('duka_www_day_2025','https://www.dukascopy.com/datafeed/EURUSD/2025/03/29_ticks.bi5')]
for sym in s.SYMBOLS:
    tasks.append((sym+'_kline_2026_07_07',s.BASE+'/kline/'+sym+'?interval=Min1&start=1783382400&end=1783386000'))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:rs=list(p.map(lambda x:request(*x),tasks))
checks=[]
for r in rs:
    c={'label':r['label'],'status':r.get('status'),'valid':False}
    try:
        if r.get('status')!=200:raise ValueError(r.get('error','HTTP_NOT_200'))
        raw=(s.ROOT/r['raw_path']).read_bytes()
        if r['label'].startswith('duka'):
            decoded=lzma.decompress(raw);rows=list(struct.iter_unpack('>3I2f',decoded));ts=[x[0] for x in rows]
            c.update(records=len(rows),first_offset=min(ts),last_offset=max(ts),monotonic=ts==sorted(ts),positive_uncrossed=all(x[1]>=x[2]>0 for x in rows),max_gap_ms=max([b-a for a,b in zip(ts,ts[1:])],default=0));c['valid']=c['monotonic'] and c['positive_uncrossed']
        else:
            j=json.loads(raw);d=j.get('data');c.update(success=j.get('success'),fields=list(d) if isinstance(d,dict) else None)
            if '_kline_' in r['label']:
                ts=d.get('time',[]);c.update(rows=len(ts),first=min(ts) if ts else None,last=max(ts) if ts else None,exact_minutes_present=len(set(ts)&set(range(1783382400,1783386000,60))));c['valid']=c['exact_minutes_present']==60
            else:c['valid']=j.get('success') is True and bool(d)
    except Exception as e:c['reason']=str(e)
    checks.append(c)
j={'requests':rs,'checks':checks,'sample_event_prices_opened':False,'burned_source_dates':['2025-04-29','2026-07-07','2026-10-02'],'technical_correction':'ticker uses query parameter symbol; /ticker/{symbol} was a probe URL bug'}
(s.OUT/'SOURCE_SUPPLEMENT_RECEIPT_V01.json').write_text(json.dumps(j,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
