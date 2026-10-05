import sys,urllib.request,urllib.error,urllib.parse,re,json,hashlib,concurrent.futures,zipfile,io,lzma,struct
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import source_gate_v01 as s
def get(label,url,data=None,headers=None):
    start=datetime.now(timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'User-Agent':'CryptoLab-Forex-SourceGate/0.1',**(headers or {})}),timeout=30) as r:b=r.read();status=r.status;h=dict(r.headers)
    except urllib.error.HTTPError as e:b=e.read();status=e.code;h=dict(e.headers)
    except Exception as e:return {'label':label,'url':url,'error':str(e),'started_at_utc':start}
    p=s.RAW/(hashlib.sha256(b).hexdigest()+'.bin');p.write_bytes(b)
    return {'label':label,'url':url,'method':'POST_DOWNLOAD' if data else 'GET','status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'headers':h,'started_at_utc':start,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'raw_path':str(p.relative_to(s.ROOT))}
tasks=[]
for day in ['2025-04-29','2026-07-08','2026-08-04','2026-09-01']:
    st=int(datetime.fromisoformat(day+'T00:00:00+00:00').timestamp())
    tasks.append(('EUR_kline_'+day,s.BASE+'/kline/EUR_USDT?interval=Min1&start='+str(st)+'&end='+str(st+3600)))
tasks.append(('EUR_endonly_2025',s.BASE+'/kline/EUR_USDT?interval=Min1&end=1745888400'))
tasks.append(('USDTUSD_coinbase_2025','https://api.exchange.coinbase.com/products/USDT-USD/candles?granularity=60&start=2025-04-29T00:00:00Z&end=2025-04-29T01:00:00Z'))
for pair in ['GBPUSD','USDJPY','USDCHF']:
    tasks.append((pair+'_duka_www_2026',f'https://www.dukascopy.com/datafeed/{pair}/2026/09/02/00h_ticks.bi5'))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:rs=list(p.map(lambda x:get(*x),tasks))
checks=[]
for r in rs:
    c={'label':r['label'],'status':r.get('status')}
    try:
        if r.get('status')!=200:raise ValueError(r.get('error','HTTP_NOT_200'))
        b=(s.ROOT/r['raw_path']).read_bytes()
        if 'duka' in r['label']:
            rows=list(struct.iter_unpack('>3I2f',lzma.decompress(b)));ts=[x[0] for x in rows];c.update(records=len(rows),monotonic=ts==sorted(ts),positive_uncrossed=all(x[1]>=x[2]>0 for x in rows),first_offset_ms=min(ts),last_offset_ms=max(ts))
        else:
            j=json.loads(b);ts=[x[0] for x in j] if isinstance(j,list) else j.get('data',{}).get('time',[]);c.update(rows=len(ts),first=min(ts) if ts else None,last=max(ts) if ts else None)
    except Exception as e:c['reason']=str(e)
    checks.append(c)
# HistData download is a public free file request; no account and no payment.
u='https://www.histdata.com/download-free-forex-historical-data/?/ascii/tick-data-quotes/eurusd/2025/4'
r=get('histdata_page',u);rs.append(r)
try:
    b=(s.ROOT/r['raw_path']).read_text(errors='replace');form=re.search(r'<form id="file_down".*?</form>',b,re.S).group()
    vals=dict(re.findall(r'name="([^"]+)"[^>]+value="([^"]*)"',form))
    r=get('histdata_download','https://www.histdata.com/get.php',urllib.parse.urlencode(vals).encode(),{'Referer':u});rs.append(r)
    blob=(s.ROOT/r['raw_path']).read_bytes()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=z.namelist(); rows=[]
        # Inspect timestamps/schema only of burned source date, no strategy values.
        for n in names:
            if n.lower().endswith('.csv'):
                lines=z.read(n).decode(errors='replace').splitlines();rows.extend([x.split(',')[0] for x in lines if x.startswith('20250429')])
        checks.append({'label':'histdata_download','status':r['status'],'files':names,'burned_day_timestamp_rows':len(rows),'first_timestamp':min(rows) if rows else None,'last_timestamp':max(rows) if rows else None})
except Exception as e:checks.append({'label':'histdata_download','reason':str(e)})
report={'mode':'SOURCE_CAPABILITY_ONLY','sample_event_prices_opened':False,'requests':rs,'checks':checks,'burned_source_dates':['2025-04-29','2026-07-07','2026-07-08','2026-08-04','2026-09-01','2026-10-02']}
(s.OUT/'SOURCE_BOUNDARY_RECEIPT_V01.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
