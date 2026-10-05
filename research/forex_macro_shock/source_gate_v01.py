"""Outcome-blind public source capability probe. No strategy/outcome evaluation."""
import concurrent.futures,hashlib,json,lzma,struct,time,urllib.request,urllib.error,urllib.parse
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evidence'
RAW=OUT/'raw'
BASE='https://api.mexc.com/api/v1/contract'
SYMBOLS=['EUR_USDT','GBP_USDT','JPY_USDT','CHF_USDT']
# Source-only validation dates are burned; never part of a later event sample.
PROBE_DATES=['2025-04-29','2026-10-02']
FX={'EUR_USDT':'EURUSD','GBP_USDT':'GBPUSD','JPY_USDT':'USDJPY','CHF_USDT':'USDCHF'}

def fetch(label,url):
    u=urllib.parse.urlparse(url)
    market_paths=['detail','ticker','depth','deals','index_price','fair_price','kline']
    allowed=u.scheme=='https' and ((u.netloc=='api.mexc.com' and any(u.path==('/api/v1/contract/'+x) or u.path.startswith('/api/v1/contract/'+x+'/') for x in market_paths)) or (u.netloc in ['datafeed.dukascopy.com','www.dukascopy.com'] and u.path.startswith('/datafeed/')))
    if not allowed:raise PermissionError(url)
    RAW.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat(); t=time.perf_counter()
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'CryptoLab-Forex-SourceGate/0.1'})
        with urllib.request.urlopen(req,timeout=30) as r:
            data=r.read();status=r.status;headers=dict(r.headers);final=r.url
    except urllib.error.HTTPError as e:
        data=e.read();status=e.code;headers=dict(e.headers);final=e.url
    except Exception as e:
        return {'label':label,'url':url,'started_at_utc':started,'error':str(e),'latency_ms':(time.perf_counter()-t)*1000}
    digest=hashlib.sha256(data).hexdigest()
    path=RAW/(digest+'.bin')
    if path.exists() and path.read_bytes()!=data:raise RuntimeError('HASH_COLLISION')
    if not path.exists():path.write_bytes(data)
    return {'label':label,'url':url,'final_url':final,'started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'status':status,'latency_ms':(time.perf_counter()-t)*1000,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'headers':headers,'raw_path':str(path.relative_to(ROOT))}

def json_data(r):
    if r.get('status')!=200:raise ValueError('HTTP_NOT_200')
    return json.loads((ROOT/r['raw_path']).read_bytes())

def main():
    tasks=[('mexc_detail',BASE+'/detail')]
    for s in SYMBOLS:
        tasks.append((s+'_ticker_query',BASE+'/ticker?symbol='+s))
        for endpoint in ['depth','deals','index_price','fair_price']:
            tasks.append((s+'_'+endpoint,BASE+'/'+endpoint+'/'+s))
        for day in PROBE_DATES:
            st=int(datetime.fromisoformat(day+'T00:00:00+00:00').timestamp())
            tasks.append((s+'_kline_'+day,BASE+'/kline/'+s+'?interval=Min1&start='+str(st)+'&end='+str(st+3600)))
    for pair in FX.values():
        for day in PROBE_DATES:
            dt=datetime.fromisoformat(day)
            tasks.append((pair+'_www_ticks_'+day,f'https://www.dukascopy.com/datafeed/{pair}/{dt.year}/{dt.month-1:02d}/{dt.day:02d}/00h_ticks.bi5'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        receipts=list(pool.map(lambda p:fetch(*p),tasks))
    by={r['label']:r for r in receipts}; metadata=[]; checks=[]
    try:
        j=json_data(by['mexc_detail'])
        if j.get('success') is not True:raise ValueError('MEXC_SUCCESS_FALSE')
        metadata=[{k:x.get(k) for k in ['symbol','displayNameEn','baseCoin','quoteCoin','contractSize','state','createTime','openingTime','indexOrigin','apiAllowed','isZeroFeeSymbol','priceUnit','volUnit','minVol']} for x in j['data'] if x.get('symbol') in SYMBOLS]
    except Exception as e:checks.append({'label':'mexc_detail','valid':False,'reason':str(e)})
    for label,r in by.items():
        if label=='mexc_detail':continue
        c={'label':label,'valid':False}
        try:
            if '_ticks_' in label:
                if r.get('status')!=200:raise ValueError('HTTP_NOT_200')
                decoded=lzma.decompress((ROOT/r['raw_path']).read_bytes())
                if len(decoded)%20:raise ValueError('INVALID_TICK_RECORD_LENGTH')
                rows=list(struct.iter_unpack('>3I2f',decoded)); ts=[x[0] for x in rows]
                if not ts:raise ValueError('EMPTY_TICKS')
                # Do not report or calculate returns, levels, directions or event outcomes.
                c.update(records=len(rows),resolution='millisecond timestamps; irregular ticks',first_offset_ms=min(ts),last_offset_ms=max(ts),max_intertick_gap_ms=max([b-a for a,b in zip(ts,ts[1:])],default=0),monotonic=ts==sorted(ts),bid_ask_positive_uncrossed=all(x[1]>=x[2]>0 for x in rows),within_hour=all(0<=t<3600000 for t in ts))
                c['valid']=c['monotonic'] and c['bid_ask_positive_uncrossed'] and c['within_hour']
            else:
                j=json_data(r)
                if j.get('success') is not True:raise ValueError('MEXC_SUCCESS_FALSE')
                d=j.get('data')
                if '_kline_' in label:
                    day=label.split('_kline_')[1];st=int(datetime.fromisoformat(day+'T00:00:00+00:00').timestamp());ts=d.get('time',[]) if isinstance(d,dict) else []
                    wanted=list(range(st,st+3600,60));present=set(ts)
                    c.update(requested_day=day,rows=len(ts),expected_minutes=60,exact_minutes_present=sum(t in present for t in wanted),first_timestamp=min(ts) if ts else None,last_timestamp=max(ts) if ts else None,duplicate_timestamps=len(ts)-len(present))
                    c['valid']=all(t in present for t in wanted) and len(ts)==len(present)
                elif '_depth' in label:
                    c.update(bid_levels=len(d.get('bids',[])),ask_levels=len(d.get('asks',[])),data_timestamp=d.get('timestamp'),version=d.get('version'));c['valid']=c['bid_levels']>0 and c['ask_levels']>0
                elif '_deals' in label:
                    c.update(records=len(d) if isinstance(d,list) else 0);c['valid']=c['records']>0
                else:c.update(payload_type=type(d).__name__,fields=list(d) if isinstance(d,dict) else [],data_timestamp=d.get('timestamp') if isinstance(d,dict) else None);c['valid']=bool(d)
        except Exception as e:c['reason']=str(e)
        checks.append(c)
    report={'candidate_id':'FOREX-MACRO-SHOCK-001','probe_version':'0.1','retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'mode':'SOURCE_CAPABILITY_ONLY','burned_source_dates':PROBE_DATES,'sample_event_prices_opened':False,'returns_computed':False,'pnl_computed':False,'consensus_accessed':False,'metadata':metadata,'checks':checks,'requests':receipts,'quote_identity_warning':'MEXC quote USDT != Dukascopy USD; JPY/CHF reference needs bid/ask reciprocal, not symbol renaming','historical_orderbook_claim':False,'orders':False,'account_reads':False,'private_endpoints':False}
    OUT.mkdir(exist_ok=True);(OUT/'SOURCE_CAPABILITY_RECEIPT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps({'metadata':metadata,'checks':checks},indent=2))
if __name__=='__main__':main()
