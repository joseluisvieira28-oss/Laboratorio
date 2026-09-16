#!/usr/bin/env python3
import hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = Path('artifacts/btc_dvol_futures_termstructure_source_v01')
BASE.mkdir(parents=True, exist_ok=True)
AUTH = json.loads(Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001/SOURCE_AUTHORITY_V0.1.json').read_text())
ADD = json.loads(Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001/SOURCE_DENSITY_GATE_ADDENDUM_V0.1.json').read_text())
HISTORY = 'https://history.deribit.com/api/v2'
LIVE = 'https://www.deribit.com/api/v2'
UA = 'SRC-Crypto-Lab-DVOL-SourceGate/0.1'
S = requests.Session(); S.headers.update({'User-Agent': UA, 'Accept': 'application/json'})

CORE = ADD['source_density_pass_rule']['core_trade_fields']
AUX = ADD['source_density_pass_rule']['aux_trade_fields']
META = ADD['source_density_pass_rule']['required_metadata_fields']


def ms(s):
    return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()*1000)

def sha(b): return hashlib.sha256(b).hexdigest()

def safe_get(url, params, timeout=30):
    r = S.get(url, params=params, timeout=timeout)
    raw = r.content
    h = sha(raw)
    if r.status_code != 200:
        raise RuntimeError(f'HTTP {r.status_code} for {r.url}; sha256={h}')
    try: obj = r.json()
    except Exception as e: raise RuntimeError(f'non-JSON response for {r.url}; sha256={h}: {e}')
    if isinstance(obj, dict) and obj.get('error'):
        raise RuntimeError(f"API error for {r.url}; sha256={h}; error={obj['error']}")
    return obj, h, len(raw), r.url

def query_trade_slice(a,b,depth=0):
    params={'currency':'USDC','kind':'future','start_timestamp':a,'end_timestamp':b,'count':1000,'sorting':'asc'}
    obj,h,n,url=safe_get(HISTORY+'/public/get_last_trades_by_currency_and_time',params)
    trades=((obj or {}).get('result') or {}).get('trades') or []
    receipt={'start_ms':a,'end_ms':b,'http_bytes':n,'sha256':h,'returned_count':len(trades),'url_without_query':HISTORY+'/public/get_last_trades_by_currency_and_time'}
    if len(trades)==1000:
        if b-a<=1000: raise RuntimeError(f'unresolved 1000-record overflow at <=1s slice {a}-{b}')
        mid=(a+b)//2
        left,lr=query_trade_slice(a,mid,depth+1); right,rr=query_trade_slice(mid+1,b,depth+1)
        return left+right,[receipt]+lr+rr
    return trades,[receipt]

def metadata(name):
    errors=[]
    for base in (HISTORY,LIVE):
        try:
            obj,h,n,url=safe_get(base+'/public/get_instrument',{'instrument_name':name})
            rec=(obj or {}).get('result') or {}
            return rec, {'source':base,'sha256':h,'http_bytes':n}
        except Exception as e: errors.append(str(e))
    raise RuntimeError(f'metadata unavailable for {name}: {errors}')

def window_summary(a_s,b_s):
    a,b=ms(a_s),ms(b_s)
    step=15*60*1000
    alltr=[]; receipts=[]
    t=a
    while t<b:
        e=min(t+step-1,b)
        tr,rr=query_trade_slice(t,e)
        alltr.extend(tr); receipts.extend(rr)
        t=e+1
        time.sleep(0.03)
    byid={str(x.get('trade_id',f"missing-{i}")):x for i,x in enumerate(alltr)}
    dvol=[x for x in byid.values() if str(x.get('instrument_name','')).startswith('BTCDVOL_USDC-')]
    instruments=sorted(set(str(x.get('instrument_name')) for x in dvol if x.get('instrument_name')))
    core_total=max(1,len(dvol)*len(CORE)); aux_total=max(1,len(dvol)*len(AUX))
    core_present=sum(1 for x in dvol for k in CORE if k in x and x[k] is not None)
    aux_present=sum(1 for x in dvol for k in AUX if k in x and x[k] is not None)
    # retain no prices, amounts, index levels, mark levels, or directions; only presence/coverage/timestamps/names
    return {
      'window':[a_s,b_s], 'all_usdc_future_trades_seen':len(byid), 'btcdvol_trade_count':len(dvol),
      'unique_btcdvol_instruments':instruments,
      'btcdvol_trade_timestamps_ms':[int(x['timestamp']) for x in dvol if x.get('timestamp') is not None],
      'core_field_coverage': core_present/core_total if dvol else 0.0,
      'aux_field_coverage': aux_present/aux_total if dvol else 0.0,
      'request_receipts':receipts
    }

def source_index_checks():
    chart_obj,chart_h,chart_n,_=safe_get(LIVE+'/public/get_index_chart_data',{'index_name':'btcdvol_usdc','range':'all'})
    pts=(chart_obj or {}).get('result') or []
    timestamps=[int(p[0]) for p in pts if isinstance(p,list) and len(p)>=2]
    years=sorted(set(datetime.fromtimestamp(t/1000,tz=timezone.utc).year for t in timestamps))
    # values are intentionally not retained
    deliv_obj,deliv_h,deliv_n,_=safe_get(LIVE+'/public/get_delivery_prices',{'index_name':'btcdvol_usdc','offset':0,'count':1000})
    dres=(deliv_obj or {}).get('result') or {}; data=dres.get('data') or []
    dates=[str(x.get('date')) for x in data if x.get('date')]
    pre2025=[d for d in dates if d[:4].isdigit() and int(d[:4])<2025]
    return {
      'chart':{'sha256':chart_h,'http_bytes':chart_n,'point_count':len(timestamps),'min_timestamp_ms':min(timestamps) if timestamps else None,'max_timestamp_ms':max(timestamps) if timestamps else None,'years_present':years},
      'delivery':{'sha256':deliv_h,'http_bytes':deliv_n,'records_total_reported':dres.get('records_total'),'dates_returned':dates,'pre2025_date_count':len(pre2025)}
    }

def main():
    result={'lab_id':AUTH['lab_id'],'source_gate_id':AUTH['source_gate_id'],'access_2025':False,'access_2026':False,'outcomes_opened':False,'strategy_pnl_opened':False,'live_trading':False,'exchange_mutation':False,'merge_to_main':False}
    try:
        wins=[window_summary(a,b) for a,b in AUTH['fixed_probe_windows_utc']]
        names=sorted(set(n for w in wins for n in w['unique_btcdvol_instruments']))
        meta={}; meta_receipts={}
        for n in names:
            rec,rc=metadata(n)
            meta[n]={k:rec.get(k) for k in META}
            meta_receipts[n]=rc
        idx=source_index_checks()
        agg=sum(w['btcdvol_trade_count'] for w in wins)
        core_num=sum(w['btcdvol_trade_count']*len(CORE)*w['core_field_coverage'] for w in wins)
        core_den=max(1,agg*len(CORE)); aux_num=sum(w['btcdvol_trade_count']*len(AUX)*w['aux_field_coverage'] for w in wins); aux_den=max(1,agg*len(AUX))
        metadata_ok=bool(names) and all(all(meta[n].get(k) is not None for k in META) for n in names)
        rules=ADD['source_density_pass_rule']
        checks={
          'all_four_probe_windows_nonempty':len(wins)==4 and all(w['btcdvol_trade_count']>0 for w in wins),
          'aggregate_trades_ge_min':agg>=rules['minimum_aggregate_btcdvol_trades_across_four_windows'],
          'min_unique_instrument_each_window':all(len(w['unique_btcdvol_instruments'])>=rules['minimum_unique_btcdvol_instruments_per_probe_window'] for w in wins),
          'core_field_coverage_ge_min':(core_num/core_den)>=rules['minimum_core_field_coverage'],
          'aux_field_coverage_ge_min':(aux_num/aux_den)>=rules['minimum_aux_field_coverage'],
          'metadata_100pct':metadata_ok,
          'index_has_2023_2024':2023 in idx['chart']['years_present'] and 2024 in idx['chart']['years_present'],
          'delivery_has_pre2025':idx['delivery']['pre2025_date_count']>=1
        }
        result.update({'classification':'SOURCE_DATA_PASS' if all(checks.values()) else 'SOURCE_DATA_INSUFFICIENT_OR_BLOCKED','probe_windows':wins,'aggregate_btcdvol_trade_count':agg,'unique_btcdvol_instruments':names,'metadata':meta,'metadata_receipts':meta_receipts,'index_source_checks':idx,'gate_checks':checks})
    except Exception as e:
        result.update({'classification':'SOURCE_ACQUISITION_TECHNICAL_FAILURE','error':repr(e)})
    p=BASE/'source_gate_result.json'; p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    manifest={'authority_sha256':sha(Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001/SOURCE_AUTHORITY_V0.1.json').read_bytes()),'addendum_sha256':sha(Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001/SOURCE_DENSITY_GATE_ADDENDUM_V0.1.json').read_bytes()),'result_sha256':sha(p.read_bytes())}
    (BASE/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result['classification']!='SOURCE_ACQUISITION_TECHNICAL_FAILURE' else 2

if __name__=='__main__': sys.exit(main())
