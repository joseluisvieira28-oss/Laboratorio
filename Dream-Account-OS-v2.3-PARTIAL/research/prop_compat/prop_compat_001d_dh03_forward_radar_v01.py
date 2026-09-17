from __future__ import annotations
import hashlib, json, subprocess, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

from research.htf_diamond_hunt import htf_diamond_hunt_scale_transfers_v01 as core

FREEZE_COMMIT='fb32edc03cc6d52112fb79fa5206b1352c5ac236'
SYMBOLS=list(core.SYMBOLS)
FIFTEEN=900_000
BAR12=43_200_000
LOOKBACK=40
ATR_LEN=28
UA='PROP-COMPAT-001D DH03 forward radar/1.0'
OUT=Path(__file__).resolve().parents[2]/'research'/'local_data'/'prop_compat_001d'

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

def fetch_recent_15m(symbol:str, now_ms:int, need:int=2600):
    rows={}; end=now_ms
    while len(rows)<need:
        qs=urllib.parse.urlencode({'symbol':symbol,'interval':'15m','limit':1500,'endTime':end})
        data=get_json('https://fapi.binance.com/fapi/v1/klines?'+qs)
        if not data: break
        for x in data:
            ot=int(x[0]); ct=int(x[6])
            if ct>=now_ms: continue
            rows[ot]=core.Bar(ot,float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5]),ct)
        first=min(int(x[0]) for x in data)
        if first<=0 or first>=end: break
        end=first-1
        if len(data)<1500: break
    out=[rows[k] for k in sorted(rows)]
    if len(out)<2000: raise RuntimeError(f'INSUFFICIENT_15M_WARMUP:{symbol}:{len(out)}')
    # Only retain the minimum tail needed for exact current 12H state; no outcome replay.
    return out[-2600:]

def inspect_symbol(symbol:str, candles, fms:int, now_ms:int):
    bars,incomplete=core.aggregate(candles,BAR12)
    bars=[b for b in bars if b.open_time+BAR12<=now_ms]
    if len(bars)<LOOKBACK+ATR_LEN+2:
        raise RuntimeError(f'INSUFFICIENT_12H_WARMUP:{symbol}:{len(bars)}')
    atr=core.atr_series(bars,ATR_LEN)
    eligible=[]
    for i in range(max(LOOKBACK,ATR_LEN),len(bars)):
        close_event=bars[i].open_time+BAR12
        if close_event<=fms: continue
        prior=max(x.high for x in bars[i-LOOKBACK:i])
        a=atr[i]
        signal=bool(a is not None and bars[i].close>prior)
        eligible.append((i,close_event,prior,a,signal))
    if not eligible:
        return {'symbol':symbol,'status':'RADAR_ARMED_NO_ELIGIBLE_SIGNAL_YET','latest_complete_12h_close_utc':iso_ms(bars[-1].open_time+BAR12),'warmup_15m_count':len(candles),'complete_12h_count':len(bars),'incomplete_12h_buckets_ignored':incomplete}
    # Forward-only: report only the first post-freeze signal event, or armed state through latest eligible bar. Never scan/score pre-freeze history.
    sigs=[x for x in eligible if x[4]]
    if not sigs:
        return {'symbol':symbol,'status':'RADAR_ARMED_NO_ELIGIBLE_SIGNAL_YET','post_freeze_complete_signal_bars_observed':len(eligible),'latest_eligible_12h_close_utc':iso_ms(eligible[-1][1]),'warmup_15m_count':len(candles),'complete_12h_count':len(bars)}
    i,ce,prior,a,_=sigs[0]; b=bars[i]
    stop=b.low-0.25*float(a)
    next_open_time=b.open_time+BAR12
    next_bar=next((x for x in bars if x.open_time==next_open_time),None)
    return {'symbol':symbol,'status':'ELIGIBLE_FORWARD_SIGNAL_DETECTED','signal_bar_open_utc':iso_ms(b.open_time),'signal_bar_close_utc':iso_ms(ce),'donchian_prior40_high':prior,'signal_close':b.close,'signal_low':b.low,'atr28':float(a),'planned_entry_bar_open_utc':iso_ms(next_open_time),'entry_open_observed':None if next_bar is None else next_bar.open,'stop_formula_value':stop,'target_formula':'entry_open + 3*(entry_open-stop)','note':'READ_ONLY_SHADOW_NO_ORDER'}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fms=freeze_ms(); now_ms=int(time.time()*1000)
    if now_ms<=fms: raise RuntimeError('CLOCK_NOT_AFTER_FREEZE')
    results=[]; errors=[]
    for s in SYMBOLS:
        try: results.append(inspect_symbol(s,fetch_recent_15m(s,now_ms),fms,now_ms))
        except Exception as e: errors.append({'symbol':s,'error':str(e)})
    status='SOURCE_OR_STATE_BLOCKED' if errors else ('ELIGIBLE_FORWARD_SIGNAL_DETECTED' if any(x['status']=='ELIGIBLE_FORWARD_SIGNAL_DETECTED' for x in results) else 'RADAR_ARMED_NO_ELIGIBLE_SIGNAL_YET')
    rec={'document_id':'PROP_COMPAT_001D_DH03_FORWARD_RADAR_SNAPSHOT_V0.1','campaign_id':'PROP-COMPAT-001D','status':status,'freeze_commit':FREEZE_COMMIT,'freeze_commit_utc':iso_ms(fms),'snapshot_utc':iso_ms(now_ms),'setup_id':'DH-03-HO1','source':'BINANCE_USD_M_PUBLIC_FAPI_15M_READ_ONLY','results':results,'errors':errors,'historical_2026_performance_backfill':False,'orders_created':False,'exchange_authentication':False,'wallet_used':False,'webhook_created':False,'governance':{'forward_only':True,'warmup_state_only':True,'post_outcome_tuning':False,'live_trading':False,'merge_to_main':False}}
    raw=json.dumps(rec,sort_keys=True,separators=(',',':')).encode(); rec['fingerprint']=hashlib.sha256(raw).hexdigest()
    p=OUT/'PROP_COMPAT_001D_DH03_FORWARD_RADAR_SNAPSHOT_V0.1.json'; p.write_text(json.dumps(rec,indent=2,sort_keys=True)); print(json.dumps({'status':status,'errors':errors,'signal_symbols':[x['symbol'] for x in results if x['status']=='ELIGIBLE_FORWARD_SIGNAL_DETECTED'],'fingerprint':rec['fingerprint']},sort_keys=True));
    if errors: raise SystemExit(2)

if __name__=='__main__': main()
