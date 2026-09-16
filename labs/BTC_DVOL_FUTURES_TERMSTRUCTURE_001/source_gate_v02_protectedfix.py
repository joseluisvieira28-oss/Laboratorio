#!/usr/bin/env python3
import hashlib, json, sys, time
from datetime import datetime
from pathlib import Path
import requests

OUT = Path('artifacts/btc_dvol_futures_termstructure_source_v02')
OUT.mkdir(parents=True, exist_ok=True)
AUTH_PATH = Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001/SOURCE_AUTHORITY_V0.1.json')
ADD_PATH = Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001/SOURCE_DENSITY_GATE_ADDENDUM_V0.1.json')
REM_PATH = Path('labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001/PROTECTED_PERIOD_BREACH_REMEDIATION_V0.1.json')
AUTH = json.loads(AUTH_PATH.read_text())
ADD = json.loads(ADD_PATH.read_text())
REM = json.loads(REM_PATH.read_text())
HISTORY = 'https://history.deribit.com/api/v2'
UA = 'SRC-Crypto-Lab-DVOL-SourceGate-ProtectedFix/0.2'
S = requests.Session(); S.headers.update({'User-Agent': UA, 'Accept': 'application/json'})
CORE = ADD['source_density_pass_rule']['core_trade_fields']
AUX = ADD['source_density_pass_rule']['aux_trade_fields']
META = ADD['source_density_pass_rule']['required_metadata_fields']


def ms(s): return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()*1000)
def sha_bytes(b): return hashlib.sha256(b).hexdigest()

def assert_protected_safe():
    for a,b in AUTH['fixed_probe_windows_utc']:
        ya=int(a[:4]); yb=int(b[:4])
        if ya not in (2023,2024) or yb not in (2023,2024):
            raise RuntimeError('frozen probe window escapes 2023-2024')
    if AUTH['source_window']['end'] >= '2025-01-01T00:00:00Z':
        raise RuntimeError('authority source_window escapes protected firewall')

def safe_get(path, params, timeout=30):
    url=HISTORY+path
    r=S.get(url,params=params,timeout=timeout); raw=r.content
    if r.status_code!=200: raise RuntimeError(f'HTTP {r.status_code} {path}; sha256={sha_bytes(raw)}')
    try: obj=r.json()
    except Exception as e: raise RuntimeError(f'non-JSON {path}; sha256={sha_bytes(raw)}; {e}')
    if isinstance(obj,dict) and obj.get('error'): raise RuntimeError(f'API error {path}: {obj["error"]}')
    return obj, {'endpoint':path,'sha256':sha_bytes(raw),'http_bytes':len(raw)}

def trade_slice(a,b):
    params={'currency':'USDC','kind':'future','start_timestamp':a,'end_timestamp':b,'count':1000,'sorting':'asc'}
    obj,rc=safe_get('/public/get_last_trades_by_currency_and_time',params)
    trades=((obj or {}).get('result') or {}).get('trades') or []
    rc.update({'start_ms':a,'end_ms':b,'returned_count':len(trades)})
    if len(trades)==1000:
        if b-a<=1000: raise RuntimeError(f'unresolved 1000-record overflow <=1s {a}-{b}')
        mid=(a+b)//2
        l,lr=trade_slice(a,mid); r,rr=trade_slice(mid+1,b)
        return l+r,[rc]+lr+rr
    return trades,[rc]

def window_summary(a_s,b_s):
    a,b=ms(a_s),ms(b_s); step=15*60*1000; rows=[]; receipts=[]; t=a
    while t<b:
        e=min(t+step-1,b)
        x,rr=trade_slice(t,e); rows.extend(x); receipts.extend(rr); t=e+1; time.sleep(0.02)
    byid={str(x.get('trade_id',f'missing-{i}')):x for i,x in enumerate(rows)}
    dvol=[x for x in byid.values() if str(x.get('instrument_name','')).startswith('BTCDVOL_USDC-')]
    names=sorted(set(str(x['instrument_name']) for x in dvol if x.get('instrument_name')))
    core_den=max(1,len(dvol)*len(CORE)); aux_den=max(1,len(dvol)*len(AUX))
    core=sum(1 for x in dvol for k in CORE if x.get(k) is not None)/core_den if dvol else 0.0
    aux=sum(1 for x in dvol for k in AUX if x.get(k) is not None)/aux_den if dvol else 0.0
    # No economic values are retained: no price, amount, direction, index_price or mark_price values.
    return {'window':[a_s,b_s],'btcdvol_trade_count':len(dvol),'unique_btcdvol_instruments':names,'core_field_coverage':core,'aux_field_coverage':aux,'request_receipts':receipts}

def exact_metadata(name):
    obj,rc=safe_get('/public/get_instrument',{'instrument_name':name})
    rec=(obj or {}).get('result') or {}
    # Metadata only; no market outcomes.
    return {k:rec.get(k) for k in META},rc

def main():
    result={'lab_id':AUTH['lab_id'],'source_gate_id':AUTH['source_gate_id'],'runner':'source_gate_v02_protectedfix.py','void_predecessor_run_id':REM['invalid_run']['github_run_id'],'access_2025':False,'access_2026':False,'outcomes_opened':False,'strategy_pnl_opened':False,'live_trading':False,'exchange_mutation':False,'merge_to_main':False}
    try:
        assert_protected_safe()
        wins=[window_summary(a,b) for a,b in AUTH['fixed_probe_windows_utc']]
        names=sorted(set(n for w in wins for n in w['unique_btcdvol_instruments']))
        metadata={}; metadata_receipts={}
        for n in names:
            metadata[n],metadata_receipts[n]=exact_metadata(n)
        agg=sum(w['btcdvol_trade_count'] for w in wins)
        r=ADD['source_density_pass_rule']
        core_num=sum(w['btcdvol_trade_count']*len(CORE)*w['core_field_coverage'] for w in wins); core_den=max(1,agg*len(CORE))
        aux_num=sum(w['btcdvol_trade_count']*len(AUX)*w['aux_field_coverage'] for w in wins); aux_den=max(1,agg*len(AUX))
        meta_ok=bool(names) and all(all(metadata[n].get(k) is not None for k in META) for n in names)
        checks={
          'all_four_probe_windows_nonempty': len(wins)==4 and all(w['btcdvol_trade_count']>0 for w in wins),
          'aggregate_trades_ge_min': agg>=r['minimum_aggregate_btcdvol_trades_across_four_windows'],
          'min_unique_instrument_each_window': all(len(w['unique_btcdvol_instruments'])>=r['minimum_unique_btcdvol_instruments_per_probe_window'] for w in wins),
          'core_field_coverage_ge_min': (core_num/core_den)>=r['minimum_core_field_coverage'],
          'aux_field_coverage_ge_min': (aux_num/aux_den)>=r['minimum_aux_field_coverage'],
          'metadata_100pct': meta_ok
        }
        result.update({'classification':'SOURCE_DATA_PASS' if all(checks.values()) else 'SOURCE_DATA_INSUFFICIENT_OR_BLOCKED','probe_windows':wins,'aggregate_btcdvol_trade_count':agg,'unique_btcdvol_instruments':names,'metadata':metadata,'metadata_receipts':metadata_receipts,'gate_checks':checks})
    except Exception as e:
        result.update({'classification':'SOURCE_ACQUISITION_TECHNICAL_FAILURE','error':repr(e)})
    p=OUT/'source_gate_result.json'; p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    manifest={'authority_sha256':sha_bytes(AUTH_PATH.read_bytes()),'addendum_sha256':sha_bytes(ADD_PATH.read_bytes()),'remediation_sha256':sha_bytes(REM_PATH.read_bytes()),'result_sha256':sha_bytes(p.read_bytes())}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    return 2 if result['classification']=='SOURCE_ACQUISITION_TECHNICAL_FAILURE' else 0

if __name__=='__main__': sys.exit(main())
