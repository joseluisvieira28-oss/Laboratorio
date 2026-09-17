#!/usr/bin/env python3
import hashlib, json, sys, time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

ROOT=Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001')
AUTH_PATH=ROOT/'LIFECYCLE_SOURCE_AUTHORITY_V0.2.json'
SPEC_PATH=ROOT/'LIFECYCLE_SOURCE_TECHNICAL_SPEC_V0.2.json'
AUTH=json.loads(AUTH_PATH.read_text())
SPEC=json.loads(SPEC_PATH.read_text())
OUT=Path('artifacts/btc_dvol_futures_lifecycle_source_v02'); OUT.mkdir(parents=True,exist_ok=True)
BASE='https://history.deribit.com/api/v2'
S=requests.Session(); S.headers.update({'User-Agent':'SRC-Crypto-Lab-DVOL-LifecycleSource/0.2','Accept':'application/json'})
CORE=AUTH['lifecycle_trade_acquisition']['required_core_fields']
AUX=AUTH['lifecycle_trade_acquisition']['required_aux_fields']
LOWER_MS=int(datetime(2023,3,27,tzinfo=timezone.utc).timestamp()*1000)
PROTECTED_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
UPPER_MS=PROTECTED_MS-1


def h(b): return hashlib.sha256(b).hexdigest()
def utc_dt(ms): return datetime.fromtimestamp(ms/1000,tz=timezone.utc)

def request(path,params,allow_instrument_miss=False):
    waits=[1,2,4]; last=None
    for attempt in range(3):
        try:
            r=S.get(BASE+path,params=params,timeout=35); raw=r.content; digest=h(raw)
            if r.status_code==429 or 500<=r.status_code<600:
                last=RuntimeError(f'HTTP {r.status_code} {path} sha256={digest}')
                if attempt<2: time.sleep(waits[attempt]); continue
                raise last
            try: obj=r.json()
            except Exception as e: raise RuntimeError(f'non-JSON HTTP {r.status_code} {path} sha256={digest}: {e}')
            err=obj.get('error') if isinstance(obj,dict) else None
            if err:
                msg=str(err.get('message','')).lower() if isinstance(err,dict) else str(err).lower()
                code=err.get('code') if isinstance(err,dict) else None
                data=err.get('data') if isinstance(err,dict) else None
                wrong=(code==-32602 and isinstance(data,dict) and str(data.get('param','')).lower()=='instrument_name' and str(data.get('reason','')).lower()=='wrong format')
                miss=allow_instrument_miss and (code in (11050,10004) or ('instrument' in msg and ('not found' in msg or 'invalid' in msg)) or wrong)
                if miss:
                    return None,{'endpoint':path,'status':r.status_code,'sha256':digest,'http_bytes':len(raw),'candidate_miss':True}
                raise RuntimeError(f'API error {path} status={r.status_code} sha256={digest} error={err}')
            if r.status_code!=200: raise RuntimeError(f'HTTP {r.status_code} {path} sha256={digest}')
            return obj,{'endpoint':path,'status':r.status_code,'sha256':digest,'http_bytes':len(raw)}
        except requests.RequestException as e:
            last=e
            if attempt<2: time.sleep(waits[attempt]); continue
            raise
    raise last or RuntimeError('unreachable request failure')

def wednesdays(start_s,end_s):
    d=date.fromisoformat(start_s); e=date.fromisoformat(end_s)
    if d.weekday()!=2 or e.weekday()!=2: raise RuntimeError('candidate bounds not Wednesday')
    while d<=e:
        yield d; d+=timedelta(days=7)

def instrument_name(d): return 'BTCDVOL_USDC-'+d.strftime('%d%b%y').upper()

def discover_contracts():
    cfg=AUTH['candidate_instrument_discovery']; accepted=[]; misses=[]; receipts=[]
    for d in wednesdays(cfg['candidate_start'],cfg['candidate_end']):
        name=instrument_name(d)
        obj,rc=request('/public/get_instrument',{'instrument_name':name},allow_instrument_miss=True)
        rc['candidate']=name; receipts.append(rc)
        if obj is None:
            misses.append(name); continue
        rec=(obj or {}).get('result') or {}
        creation=rec.get('creation_timestamp'); expiry=rec.get('expiration_timestamp')
        numeric=isinstance(creation,(int,float)) and isinstance(expiry,(int,float))
        overlap=numeric and int(creation)<int(expiry) and int(creation)<=UPPER_MS and int(expiry)>=LOWER_MS
        valid=(rec.get('instrument_name')==name and rec.get('kind')=='future' and rec.get('price_index')=='btcdvol_usdc' and overlap and int(expiry)<PROTECTED_MS)
        if not valid:
            accepted.append({'instrument_name':name,'accepted':False,'rejection':'EXACT_METADATA_ACCEPTANCE_FAIL_V02','creation_timestamp':creation,'expiration_timestamp':expiry,'kind':rec.get('kind'),'price_index':rec.get('price_index')})
            continue
        accepted.append({'instrument_name':name,'accepted':True,'creation_timestamp':int(creation),'expiration_timestamp':int(expiry),'observed_start_timestamp':max(int(creation),LOWER_MS),'observed_end_timestamp':min(int(expiry),UPPER_MS),'kind':'future','price_index':'btcdvol_usdc','contract_size':rec.get('contract_size'),'min_trade_amount':rec.get('min_trade_amount'),'tick_size':rec.get('tick_size')})
        time.sleep(0.015)
    return [x for x in accepted if x['accepted']],[x for x in accepted if not x['accepted']],misses,receipts

def trade_slice(name,a,b):
    if a<LOWER_MS or a>=PROTECTED_MS or b>=PROTECTED_MS or b<a: raise RuntimeError(f'unsafe trade request {name} {a}-{b}')
    obj,rc=request('/public/get_last_trades_by_instrument_and_time',{'instrument_name':name,'start_timestamp':a,'end_timestamp':b,'count':1000,'sorting':'asc'})
    trades=((obj or {}).get('result') or {}).get('trades') or []
    rc.update({'instrument_name':name,'start_ms':a,'end_ms':b,'returned_count':len(trades)})
    if len(trades)==1000:
        if b-a<=1000: raise RuntimeError(f'unresolved 1000-record overflow <=1s for {name} {a}-{b}')
        mid=(a+b)//2; l,lr=trade_slice(name,a,mid); r,rr=trade_slice(name,mid+1,b); return l+r,[rc]+lr+rr
    return trades,[rc]

def acquire_life(meta):
    name=meta['instrument_name']; start=meta['observed_start_timestamp']; end=meta['observed_end_timestamp']
    if start<LOWER_MS or end>=PROTECTED_MS or end<start: raise RuntimeError(f'unsafe observed lifecycle {name}')
    step=86400000; t=start; rows=[]; receipts=[]
    while t<=end:
        e=min(t+step-1,end); x,rr=trade_slice(name,t,e); rows.extend(x); receipts.extend(rr); t=e+1; time.sleep(0.01)
    dedup={}
    for i,x in enumerate(rows):
        key=str(x.get('trade_id',f'MISSING-{i}')); ts=x.get('timestamp')
        if not isinstance(ts,(int,float)) or int(ts)<start or int(ts)>end or int(ts)>=PROTECTED_MS: raise RuntimeError(f'out-of-bounds trade timestamp {name}: {ts}')
        dedup[key]=x
    ordinary=[x for x in dedup.values() if x.get('block_trade_id') is None and x.get('combo_id') is None]
    active_days=sorted({utc_dt(int(x['timestamp'])).date().isoformat() for x in ordinary})
    first=min((int(x['timestamp']) for x in ordinary),default=None); last=max((int(x['timestamp']) for x in ordinary),default=None)
    core_den=max(1,len(ordinary)*len(CORE)); aux_den=max(1,len(ordinary)*len(AUX))
    core_present=sum(1 for x in ordinary for k in CORE if x.get(k) is not None); aux_present=sum(1 for x in ordinary for k in AUX if x.get(k) is not None)
    return {'instrument_name':name,'creation_timestamp':meta['creation_timestamp'],'expiration_timestamp':meta['expiration_timestamp'],'observed_start_timestamp':start,'observed_end_timestamp':end,'lower_boundary_clipped':meta['creation_timestamp']<LOWER_MS,'ordinary_public_trade_count':len(ordinary),'unique_active_utc_days':len(active_days),'first_ordinary_trade_timestamp':first,'last_ordinary_trade_timestamp':last,'core_field_present_cells':core_present,'core_field_total_cells':core_den,'aux_field_present_cells':aux_present,'aux_field_total_cells':aux_den,'request_count':len(receipts),'request_receipts':receipts}

def quarter(exp_ms):
    d=utc_dt(exp_ms); return f'{d.year}-Q{((d.month-1)//3)+1}'

def main():
    result={'lab_id':AUTH['lab_id'],'source_gate_id':AUTH['source_gate_id'],'runner':'lifecycle_source_gate_v02.py','access_2025':False,'access_2026':False,'outcomes_opened':False,'basis_opened':False,'convergence_opened':False,'strategy_pnl_opened':False,'live_trading':False,'exchange_mutation':False,'merge_to_main':False}
    try:
        contracts,rejected,misses,meta_receipts=discover_contracts(); lives=[]
        for i,m in enumerate(contracts):
            lives.append(acquire_life(m)); print(f'SOURCE_PROGRESS {i+1}/{len(contracts)} {m["instrument_name"]}',flush=True)
        g=AUTH['source_viability_gates_frozen']; qdef=g['qualifying_contract_definition']
        for x in lives:
            x['qualifying_source_contract']=(x['ordinary_public_trade_count']>=qdef['minimum_ordinary_public_trades'] and x['unique_active_utc_days']>=qdef['minimum_unique_active_utc_days']); x['expiration_calendar_quarter']=quarter(x['expiration_timestamp'])
        qualifying=[x for x in lives if x['qualifying_source_contract']]
        total_trades=sum(x['ordinary_public_trade_count'] for x in lives); active_days=sum(x['unique_active_utc_days'] for x in lives)
        core_present=sum(x['core_field_present_cells'] for x in lives); core_total=max(1,sum(x['core_field_total_cells'] for x in lives)); aux_present=sum(x['aux_field_present_cells'] for x in lives); aux_total=max(1,sum(x['aux_field_total_cells'] for x in lives))
        quarters=sorted({x['expiration_calendar_quarter'] for x in qualifying}); metadata_integrity=(len(contracts)/(len(contracts)+len(rejected))) if (contracts or rejected) else 0.0
        checks={'confirmed_contracts_ge_min':len(contracts)>=g['minimum_confirmed_contracts'],'qualifying_contracts_ge_min':len(qualifying)>=g['minimum_qualifying_contracts'],'aggregate_active_contract_days_ge_min':active_days>=g['minimum_aggregate_active_contract_days'],'qualifying_quarters_ge_min':len(quarters)>=g['minimum_distinct_calendar_quarters_among_qualifying_contracts'],'core_field_coverage_ge_min':(core_present/core_total)>=g['core_field_coverage_minimum'],'aux_field_coverage_ge_min':(aux_present/aux_total)>=g['aux_field_coverage_minimum'],'metadata_integrity_rate_ge_min':metadata_integrity>=g['exact_metadata_integrity_rate']}
        classification='LIFECYCLE_SOURCE_DATA_PASS' if all(checks.values()) else 'LIFECYCLE_SOURCE_DATA_INSUFFICIENT'
        clean=[]
        for x in lives:
            clean.append({k:v for k,v in x.items() if k not in ('core_field_present_cells','core_field_total_cells','aux_field_present_cells','aux_field_total_cells')})
        result.update({'classification':classification,'candidate_wednesdays_tested':len(meta_receipts),'candidate_miss_count':len(misses),'metadata_rejection_count':len(rejected),'confirmed_contract_count':len(contracts),'lower_boundary_clipped_contract_count':sum(1 for x in lives if x['lower_boundary_clipped']),'qualifying_contract_count':len(qualifying),'aggregate_ordinary_public_trade_count':total_trades,'aggregate_active_contract_days':active_days,'qualifying_expiration_quarters':quarters,'core_field_coverage':core_present/core_total,'aux_field_coverage':aux_present/aux_total,'metadata_integrity_rate':metadata_integrity,'gate_checks':checks,'contracts':clean,'candidate_misses':misses,'metadata_rejections':rejected,'metadata_request_receipts':meta_receipts})
    except Exception as e:
        result.update({'classification':'LIFECYCLE_SOURCE_ACQUISITION_TECHNICAL_FAILURE','error':repr(e)})
    p=OUT/'lifecycle_source_gate_v02_result.json'; p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    manifest={'authority_sha256':h(AUTH_PATH.read_bytes()),'technical_spec_sha256':h(SPEC_PATH.read_bytes()),'result_sha256':h(p.read_bytes())}; (OUT/'manifest_v02.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('contracts','metadata_request_receipts','candidate_misses','metadata_rejections')},indent=2,sort_keys=True))
    return 2 if result['classification']=='LIFECYCLE_SOURCE_ACQUISITION_TECHNICAL_FAILURE' else 0

if __name__=='__main__': sys.exit(main())
