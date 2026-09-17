from __future__ import annotations
import hashlib, json, subprocess, time, urllib.parse, urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

FREEZE_COMMIT='fb32edc03cc6d52112fb79fa5206b1352c5ac236'
SYMBOLS=['BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','XRPUSDT','DOGEUSDT']
FIFTEEN=900_000
BAR12=43_200_000
LOOKBACK=40
ATR_LEN=28
UA='PROP-COMPAT-001D DH03 forward radar/1.0'
OUT=Path(__file__).resolve().parents[2]/'research'/'local_data'/'prop_compat_001d'

@dataclass(frozen=True)
class Bar:
    open_time:int
    open:float
    high:float
    low:float
    close:float
    volume:float
    close_time:int

def iso_ms(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat().replace('+00:00','Z')

def freeze_ms()->int:
    s=subprocess.check_output(['git','show','-s','--format=%cI',FREEZE_COMMIT],text=True).strip()
    return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()*1000)

def get_json(url:str):
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=30) as r:
        if r.status!=200: raise RuntimeError(f'HTTP_{r.status}:{url}')
        return json.loads(r.read())

def aggregate(candles:list[Bar],bar_ms:int):
    expected_n=bar_ms//FIFTEEN
    buckets=defaultdict(list)
    for c in candles:
        b=c.open_time-(c.open_time%bar_ms); buckets[b].append(c)
    out=[]; incomplete=0
    for b in sorted(buckets):
        rows=sorted(buckets[b],key=lambda x:x.open_time)
        expected=[b+i*FIFTEEN for i in range(expected_n)]
        if len(rows)!=expected_n or [x.open_time for x in rows]!=expected:
            incomplete+=1; continue
        out.append(Bar(b,rows[0].open,max(x.high for x in rows),min(x.low for x in rows),rows[-1].close,sum(x.volume for x in rows),b+bar_ms-1))
    return out,incomplete

def atr_series(bars:list[Bar],length:int):
    out=[None]*len(bars)
    if len(bars)<=length:return out
    trs=[None]
    for i in range(1,len(bars)):
        c,p=bars[i],bars[i-1]
        trs.append(max(c.high-c.low,abs(c.high-p.close),abs(c.low-p.close)))
    seed=[float(x) for x in trs[1:length+1] if x is not None]
    if len(seed)!=length:return out
    value=mean(seed); out[length]=value
    for i in range(length+1,len(bars)):
        value=((value*(length-1))+float(trs[i]))/length; out[i]=value
    return out

def fetch_recent_15m(symbol:str,now_ms:int,need:int=2600):
    rows={}; end=now_ms
    while len(rows)<need:
        qs=urllib.parse.urlencode({'symbol':symbol,'interval':'15m','limit':1500,'endTime':end})
        data=get_json('https://fapi.binance.com/fapi/v1/klines?'+qs)
        if not data:break
        for x in data:
            ot=int(x[0]); ct=int(x[6])
            if ct>=now_ms:continue
            rows[ot]=Bar(ot,float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5]),ct)
        first=min(int(x[0]) for x in data)
        if first<=0 or first>=end:break
        end=first-1
        if len(data)<1500:break
    out=[rows[k] for k in sorted(rows)]
    if len(out)<2000:raise RuntimeError(f'INSUFFICIENT_15M_WARMUP:{symbol}:{len(out)}')
    return out[-2600:]

def inspect_symbol(symbol:str,candles,fms:int,now_ms:int):
    bars,incomplete=aggregate(candles,BAR12)
    bars=[b for b in bars if b.open_time+BAR12<=now_ms]
    if len(bars)<LOOKBACK+ATR_LEN+2:raise RuntimeError(f'INSUFFICIENT_12H_WARMUP:{symbol}:{len(bars)}')
    atr=atr_series(bars,ATR_LEN); eligible=[]
    for i in range(max(LOOKBACK,ATR_LEN),len(bars)):
        close_event=bars[i].open_time+BAR12
        if close_event<=fms:continue
        prior=max(x.high for x in bars[i-LOOKBACK:i]); a=atr[i]
        eligible.append((i,close_event,prior,a,bool(a is not None and bars[i].close>prior)))
    if not eligible:
        return {'symbol':symbol,'status':'RADAR_ARMED_NO_ELIGIBLE_SIGNAL_YET','latest_complete_12h_close_utc':iso_ms(bars[-1].open_time+BAR12),'warmup_15m_count':len(candles),'complete_12h_count':len(bars),'incomplete_12h_buckets_ignored':incomplete}
    sigs=[x for x in eligible if x[4]]
    if not sigs:
        return {'symbol':symbol,'status':'RADAR_ARMED_NO_ELIGIBLE_SIGNAL_YET','post_freeze_complete_signal_bars_observed':len(eligible),'latest_eligible_12h_close_utc':iso_ms(eligible[-1][1]),'warmup_15m_count':len(candles),'complete_12h_count':len(bars)}
    i,ce,prior,a,_=sigs[0]; b=bars[i]; stop=b.low-0.25*float(a); next_open_time=b.open_time+BAR12
    next_bar=next((x for x in bars if x.open_time==next_open_time),None)
    return {'symbol':symbol,'status':'ELIGIBLE_FORWARD_SIGNAL_DETECTED','signal_bar_open_utc':iso_ms(b.open_time),'signal_bar_close_utc':iso_ms(ce),'donchian_prior40_high':prior,'signal_close':b.close,'signal_low':b.low,'atr28':float(a),'planned_entry_bar_open_utc':iso_ms(next_open_time),'entry_open_observed':None if next_bar is None else next_bar.open,'stop_formula_value':stop,'target_formula':'entry_open + 3*(entry_open-stop)','note':'READ_ONLY_SHADOW_NO_ORDER'}

def main():
    OUT.mkdir(parents=True,exist_ok=True); fms=freeze_ms(); now_ms=int(time.time()*1000)
    if now_ms<=fms:raise RuntimeError('CLOCK_NOT_AFTER_FREEZE')
    results=[]; errors=[]
    for s in SYMBOLS:
        try:results.append(inspect_symbol(s,fetch_recent_15m(s,now_ms),fms,now_ms))
        except Exception as e:errors.append({'symbol':s,'error':str(e)})
    status='SOURCE_OR_STATE_BLOCKED' if errors else ('ELIGIBLE_FORWARD_SIGNAL_DETECTED' if any(x['status']=='ELIGIBLE_FORWARD_SIGNAL_DETECTED' for x in results) else 'RADAR_ARMED_NO_ELIGIBLE_SIGNAL_YET')
    rec={'document_id':'PROP_COMPAT_001D_DH03_FORWARD_RADAR_SNAPSHOT_V0.1','campaign_id':'PROP-COMPAT-001D','status':status,'freeze_commit':FREEZE_COMMIT,'freeze_commit_utc':iso_ms(fms),'snapshot_utc':iso_ms(now_ms),'setup_id':'DH-03-HO1','source':'BINANCE_USD_M_PUBLIC_FAPI_15M_READ_ONLY','implementation_note':'Self-contained exact copies of the frozen 15m-to-12H aggregation and Wilder ATR28 formulas; technical dependency correction only, after prior run failed before source access.','results':results,'errors':errors,'historical_2026_performance_backfill':False,'orders_created':False,'exchange_authentication':False,'wallet_used':False,'webhook_created':False,'governance':{'forward_only':True,'warmup_state_only':True,'post_outcome_tuning':False,'live_trading':False,'merge_to_main':False}}
    raw=json.dumps(rec,sort_keys=True,separators=(',',':')).encode(); rec['fingerprint']=hashlib.sha256(raw).hexdigest(); p=OUT/'PROP_COMPAT_001D_DH03_FORWARD_RADAR_SNAPSHOT_V0.1.json'; p.write_text(json.dumps(rec,indent=2,sort_keys=True)); print(json.dumps({'status':status,'errors':errors,'signal_symbols':[x['symbol'] for x in results if x['status']=='ELIGIBLE_FORWARD_SIGNAL_DETECTED'],'fingerprint':rec['fingerprint']},sort_keys=True));
    if errors:raise SystemExit(2)

if __name__=='__main__':main()
