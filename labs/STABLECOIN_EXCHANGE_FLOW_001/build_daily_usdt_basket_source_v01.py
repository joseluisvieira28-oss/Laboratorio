#!/usr/bin/env python3
"""Build protected daily USDT basket source dataset for SEF MVE0.

SOURCE ONLY. No BTC price, return, PnL, 2025 or 2026 access.
Primary archive source: dRPC. Independent monthly-state QA: MEV Blocker.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, threading, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime, timezone, timedelta
from pathlib import Path

LAB='STABLECOIN-EXCHANGE-FLOW-001'
MVE='SEF-BINANCE-PUBLIC-USDT-ETH-1D-001'
OUT=Path('artifacts/stablecoin_exchange_flow_daily_source_v01')
PRIMARY='https://eth.drpc.org'
QA='https://rpc.mevblocker.io'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
BALANCE_OF='70a08231'
DECIMALS=6
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
START_DATE=date(2022,11,11)
END_DATE=date(2024,12,29)
# Protected anchors already established by prior source gates; both are within 2022-2024.
ANCHOR_START_BLOCK=15943061
ANCHOR_START_TS=1668124811
ANCHOR_END_BLOCK=21519027
ANCHOR_END_TS=1735606763
MAX_WORKERS_BOUNDARY=8
MAX_WORKERS_BALANCE=12
REQ_TIMEOUT=30
MAX_RETRIES=6

_block_cache={}
_cache_lock=threading.Lock()

def sha256_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def post_rpc(url:str,method:str,params:list,rid:int=1):
    payload={'jsonrpc':'2.0','id':rid,'method':method,'params':params}
    body=json.dumps(payload,separators=(',',':')).encode()
    last=None
    for attempt in range(MAX_RETRIES):
        req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'CryptoLab-SEF-source-builder/0.1'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=REQ_TIMEOUT) as r:
                raw=r.read(); p=json.loads(raw.decode())
                if r.status==200 and isinstance(p,dict) and not p.get('error'):
                    return p, sha256_bytes(raw), attempt+1
                last=f"HTTP{r.status}:{p.get('error') if isinstance(p,dict) else 'bad_json'}"
        except urllib.error.HTTPError as e:
            raw=e.read()
            try: p=json.loads(raw.decode())
            except Exception: p=None
            last=f"HTTP{e.code}:{p.get('error') if isinstance(p,dict) else raw.decode(errors='replace')[:200]}"
        except Exception as e:
            last=f"{type(e).__name__}:{e}"
        time.sleep(min(4.0,0.20*(2**attempt)))
    raise RuntimeError(f"RPC_FAILED {url} {method} after {MAX_RETRIES}: {last}")

def block_info(n:int):
    if n < ANCHOR_START_BLOCK or n > ANCHOR_END_BLOCK:
        raise ValueError(f'block outside protected anchor range: {n}')
    with _cache_lock:
        if n in _block_cache: return _block_cache[n]
    p,h,a=post_rpc(PRIMARY,'eth_getBlockByNumber',[hex(n),False],rid=11)
    r=p.get('result')
    if not isinstance(r,dict) or 'timestamp' not in r or 'number' not in r:
        raise RuntimeError(f'bad block response for {n}')
    obj={'block':int(r['number'],16),'timestamp':int(r['timestamp'],16),'hash':r.get('hash'),'response_sha256':h,'attempts':a}
    with _cache_lock: _block_cache[n]=obj
    return obj

def target_ts_for(d:date)->int:
    dt=datetime.combine(d,dtime(23,59,59),tzinfo=timezone.utc)
    return int(dt.timestamp())

def find_boundary(d:date):
    target=target_ts_for(d)
    if not (ANCHOR_START_TS <= target < ANCHOR_END_TS):
        raise ValueError(f'target outside protected timestamp anchors {d} {target}')
    slope=(ANCHOR_END_BLOCK-ANCHOR_START_BLOCK)/(ANCHOR_END_TS-ANCHOR_START_TS)
    est=int(round(ANCHOR_START_BLOCK+(target-ANCHOR_START_TS)*slope))
    span=256
    low=max(ANCHOR_START_BLOCK,est-span); high=min(ANCHOR_END_BLOCK,est+span)
    while True:
        li=block_info(low); hi=block_info(high)
        if li['timestamp'] <= target < hi['timestamp']: break
        span*=2
        if span>16384: raise RuntimeError(f'could not bracket {d}; est={est}')
        low=max(ANCHOR_START_BLOCK,est-span); high=min(ANCHOR_END_BLOCK,est+span)
    while high-low>1:
        mid=(low+high)//2; mi=block_info(mid)
        if mi['timestamp'] <= target: low=mid
        else: high=mid
    last=block_info(low); nxt=block_info(high)
    if not(last['timestamp']<=target<nxt['timestamp'] and high==low+1):
        raise RuntimeError(f'boundary invariant failed {d}')
    return {'date':d.isoformat(),'target_timestamp':target,'boundary_block':low,'boundary_timestamp':last['timestamp'],'next_block':high,'next_timestamp':nxt['timestamp'],'boundary_hash':last.get('hash')}

def balance_data(address:str)->str:
    return '0x'+BALANCE_OF+('0'*24)+address[2:].lower()

def one_balance(provider:str,address:str,block:int,rid:int):
    p,h,a=post_rpc(provider,'eth_call',[{'to':USDT,'data':balance_data(address)},hex(block)],rid=rid)
    r=p.get('result')
    if not isinstance(r,str): raise RuntimeError(f'missing balance result {provider} {address} {block}')
    return int(r,16),h,a

def fetch_primary_balance_task(idx:int,address:str,block:int):
    raw,h,a=one_balance(PRIMARY,address,block,1000+(idx%900000))
    return idx,address,raw,h,a

def fetch_qa_balance_task(key:str,address:str,block:int,idx:int):
    raw,h,a=one_balance(QA,address,block,2000+(idx%900000))
    return key,address,raw,h,a

def file_sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    dates=[]; d=START_DATE
    while d<=END_DATE:
        dates.append(d); d+=timedelta(days=1)
    expected=(END_DATE-START_DATE).days+1
    assert len(dates)==expected==780

    # Phase A: exact end-of-day Ethereum block for all protected dates.
    boundaries={}; boundary_errors=[]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_BOUNDARY) as ex:
        futs={ex.submit(find_boundary,d):d for d in dates}
        for fut in as_completed(futs):
            d=futs[fut]
            try: boundaries[d.isoformat()]=fut.result()
            except Exception as e: boundary_errors.append({'date':d.isoformat(),'error':f'{type(e).__name__}:{e}'})
    if boundary_errors:
        receipt={'lab_id':LAB,'mve_id':MVE,'classification':'DATA_FAILURE','stage':'BOUNDARY_DISCOVERY','errors':boundary_errors[:50],'error_count':len(boundary_errors),'btc_market_data_accessed':False,'access_2025':False,'access_2026':False}
        (OUT/'SOURCE_DATASET_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        print(json.dumps(receipt,indent=2,sort_keys=True)); return 0

    ordered=[boundaries[d.isoformat()] for d in dates]
    # Structural boundary QA.
    boundary_ok=True; boundary_issues=[]
    for i,b in enumerate(ordered):
        if b['boundary_timestamp']>b['target_timestamp'] or b['next_timestamp']<=b['target_timestamp'] or b['next_block']!=b['boundary_block']+1:
            boundary_ok=False; boundary_issues.append({'date':b['date'],'issue':'last_block_invariant'})
        if datetime.fromtimestamp(b['boundary_timestamp'],tz=timezone.utc).year>=2025 or datetime.fromtimestamp(b['next_timestamp'],tz=timezone.utc).year>=2025:
            boundary_ok=False; boundary_issues.append({'date':b['date'],'issue':'forbidden_2025_boundary_metadata'})
        if i and b['boundary_block']<=ordered[i-1]['boundary_block']:
            boundary_ok=False; boundary_issues.append({'date':b['date'],'issue':'non_monotonic_block'})
    if not boundary_ok:
        receipt={'lab_id':LAB,'mve_id':MVE,'classification':'DATA_FAILURE','stage':'BOUNDARY_QA','issues':boundary_issues[:50],'btc_market_data_accessed':False,'access_2025':False,'access_2026':False}
        (OUT/'SOURCE_DATASET_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        print(json.dumps(receipt,indent=2,sort_keys=True)); return 0

    # Phase B: all 9 primary balances for every boundary.
    tasks=[]
    for di,b in enumerate(ordered):
        for ai,address in enumerate(BASKET): tasks.append((di*len(BASKET)+ai,address,b['boundary_block']))
    result_by_idx={}; balance_errors=[]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_BALANCE) as ex:
        futs={ex.submit(fetch_primary_balance_task,*t):t for t in tasks}
        for fut in as_completed(futs):
            t=futs[fut]
            try:
                idx,address,raw,h,a=fut.result(); result_by_idx[idx]={'address':address,'raw':raw,'sha256':h,'attempts':a}
            except Exception as e: balance_errors.append({'idx':t[0],'address':t[1],'block':t[2],'error':f'{type(e).__name__}:{e}'})
    if balance_errors or len(result_by_idx)!=len(tasks):
        receipt={'lab_id':LAB,'mve_id':MVE,'classification':'DATA_FAILURE','stage':'PRIMARY_BALANCES','expected_calls':len(tasks),'completed':len(result_by_idx),'errors':balance_errors[:50],'error_count':len(balance_errors),'btc_market_data_accessed':False,'access_2025':False,'access_2026':False}
        (OUT/'SOURCE_DATASET_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        print(json.dumps(receipt,indent=2,sort_keys=True)); return 0

    rows=[]; raw_detail=[]
    prev=None
    for di,b in enumerate(ordered):
        vals=[result_by_idx[di*len(BASKET)+ai] for ai in range(len(BASKET))]
        total=sum(x['raw'] for x in vals)
        flow=None if prev is None else total-prev
        rows.append({'date':b['date'],'boundary_block':b['boundary_block'],'boundary_timestamp':b['boundary_timestamp'],'total_balance_raw':total,'total_balance_usdt':f'{total/(10**DECIMALS):.6f}','net_flow_raw':'' if flow is None else flow,'net_flow_usdt':'' if flow is None else f'{flow/(10**DECIMALS):.6f}'})
        raw_detail.append({'date':b['date'],'boundary_block':b['boundary_block'],'balances':[{k:v for k,v in x.items() if k in ('address','raw','sha256','attempts')} for x in vals]})
        prev=total

    # Phase C: prospectively fixed QA subset: all first calendar days + baseline + final.
    qa_dates={START_DATE.isoformat(),END_DATE.isoformat()}
    qa_dates.update(d.isoformat() for d in dates if d.day==1)
    qa_dates=sorted(qa_dates)
    qa_tasks=[]; qidx=0
    boundary_map={x['date']:x for x in ordered}
    for ds in qa_dates:
        for address in BASKET:
            qa_tasks.append((ds,address,boundary_map[ds]['boundary_block'],qidx)); qidx+=1
    qa_result={}; qa_errors=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs={ex.submit(fetch_qa_balance_task,*t):t for t in qa_tasks}
        for fut in as_completed(futs):
            t=futs[fut]
            try:
                ds,address,raw,h,a=fut.result(); qa_result[(ds,address)]={'raw':raw,'sha256':h,'attempts':a}
            except Exception as e: qa_errors.append({'date':t[0],'address':t[1],'block':t[2],'error':f'{type(e).__name__}:{e}'})
    primary_lookup={}
    for item in raw_detail:
        for x in item['balances']: primary_lookup[(item['date'],x['address'])]=x['raw']
    mismatches=[]
    for ds in qa_dates:
        for address in BASKET:
            q=qa_result.get((ds,address))
            p=primary_lookup.get((ds,address))
            if q is None or p!=q['raw']:
                mismatches.append({'date':ds,'address':address,'primary_raw':p,'qa_raw':None if q is None else q['raw']})

    csv_path=OUT/'USDT_BINANCE_PUBLIC_BASKET_DAILY_20221111_20241229.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    detail_path=OUT/'USDT_BINANCE_PUBLIC_BASKET_BALANCES_AUDIT.jsonl'
    with detail_path.open('w',encoding='utf-8') as f:
        for x in raw_detail: f.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')
    boundary_path=OUT/'UTC_BOUNDARY_BLOCKS.jsonl'
    with boundary_path.open('w',encoding='utf-8') as f:
        for x in ordered: f.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')

    expected_signals=len(rows)-1
    arithmetic_ok=all(int(rows[i]['net_flow_raw'])==int(rows[i]['total_balance_raw'])-int(rows[i-1]['total_balance_raw']) for i in range(1,len(rows)))
    dates_ok=len({r['date'] for r in rows})==len(rows)==780 and rows[0]['date']=='2022-11-11' and rows[-1]['date']=='2024-12-29'
    qa_ok=(not qa_errors and not mismatches and len(qa_result)==len(qa_tasks))
    cls='SOURCE_DATASET_PASS' if arithmetic_ok and dates_ok and qa_ok and expected_signals==779 else 'DATA_FAILURE'
    protocol=Path('labs/STABLECOIN_EXCHANGE_FLOW_001/FINAL_PRE_DISCOVERY_PROTOCOL_V0.1.md')
    amendment=Path('labs/STABLECOIN_EXCHANGE_FLOW_001/PRE_DISCOVERY_TECHNICAL_AMENDMENT_001_BOUNDARY_SEARCH.md')
    receipt={
      'lab_id':LAB,'mve_id':MVE,'classification':cls,
      'primary_provider':PRIMARY,'qa_provider':QA,'basket_size':len(BASKET),'usdt_contract':USDT,
      'baseline_date':rows[0]['date'],'final_source_date':rows[-1]['date'],'boundary_rows':len(rows),'signal_rows':expected_signals,
      'boundary_rule':'last Ethereum block timestamp <= 23:59:59 UTC','boundary_invariants_pass':boundary_ok,
      'date_integrity_pass':dates_ok,'net_flow_arithmetic_pass':arithmetic_ok,
      'qa_dates':qa_dates,'qa_date_count':len(qa_dates),'qa_calls_expected':len(qa_tasks),'qa_calls_completed':len(qa_result),'qa_error_count':len(qa_errors),'qa_mismatch_count':len(mismatches),'qa_exact_match_pass':qa_ok,
      'qa_errors':qa_errors[:20],'qa_mismatches':mismatches[:20],
      'csv_sha256':file_sha(csv_path),'audit_jsonl_sha256':file_sha(detail_path),'boundary_jsonl_sha256':file_sha(boundary_path),
      'protocol_sha256':file_sha(protocol) if protocol.exists() else None,'technical_amendment_sha256':file_sha(amendment) if amendment.exists() else None,
      'queried_block_cache_count':len(_block_cache),'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,
    }
    (OUT/'SOURCE_DATASET_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
