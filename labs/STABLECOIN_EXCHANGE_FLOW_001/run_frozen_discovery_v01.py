#!/usr/bin/env python3
"""Frozen one-shot Discovery for STABLECOIN-EXCHANGE-FLOW-001.

DO NOT EXECUTE unless the immutable source artifact says SOURCE_DATASET_PASS.
Consumes only 2022-2024 source signals and official Binance USD-M BTCUSDT 1m
monthly archives. No 2025/2026 access. No exchange mutation/live trading.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, random, re, sys, time, urllib.request, urllib.error, zipfile
from datetime import date, datetime, time as dtime, timezone, timedelta
from pathlib import Path

LAB='STABLECOIN-EXCHANGE-FLOW-001'
MVE='SEF-BINANCE-PUBLIC-USDT-ETH-1D-001'
SOURCE_ROOT=Path('source_artifact')
OUT=Path('artifacts/stablecoin_exchange_flow_discovery_v01')
BINANCE='https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1m'
BOOT_REPS=20000
BOOT_BLOCK=7
SEED=20260914
COST_BASE_BPS=10.0
COST_STRESS_BPS=14.0


def file_sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def get(url:str,timeout=90):
    last=None
    for attempt in range(5):
        req=urllib.request.Request(url,headers={'User-Agent':'CryptoLab-SEF-Discovery/0.1','Accept':'*/*'})
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r: return r.status,r.read()
        except urllib.error.HTTPError as e:
            last=f'HTTP{e.code}:{e.read()[:200]!r}'
        except Exception as e: last=f'{type(e).__name__}:{e}'
        time.sleep(min(5,0.5*(2**attempt)))
    raise RuntimeError(f'DOWNLOAD_FAILED {url}: {last}')

def month_iter(a:date,b:date):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        if m==12: y,m=y+1,1
        else: m+=1

def expected_checksum(text:str,filename:str):
    # Binance checksum files are sha256sum-compatible: <hex>  <filename>.
    for line in text.splitlines():
        parts=line.strip().split()
        if parts and re.fullmatch(r'[0-9a-fA-F]{64}',parts[0]): return parts[0].lower()
    raise RuntimeError(f'no sha256 in checksum for {filename}')

def load_source():
    receipts=list(SOURCE_ROOT.rglob('SOURCE_DATASET_RECEIPT.json'))
    csvs=list(SOURCE_ROOT.rglob('USDT_BINANCE_PUBLIC_BASKET_DAILY_20221111_20241229.csv'))
    if len(receipts)!=1 or len(csvs)!=1: raise RuntimeError(f'source artifact incomplete receipts={len(receipts)} csvs={len(csvs)}')
    receipt=json.loads(receipts[0].read_text())
    if receipt.get('classification')!='SOURCE_DATASET_PASS': raise RuntimeError(f"SOURCE_GATE_NOT_PASS:{receipt.get('classification')}")
    if receipt.get('access_2025') or receipt.get('access_2026') or receipt.get('btc_market_data_accessed'):
        raise RuntimeError('source governance receipt invalid')
    if file_sha(csvs[0])!=receipt.get('csv_sha256'): raise RuntimeError('source CSV hash mismatch')
    rows=[]
    with csvs[0].open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['date']=='2022-11-11': continue
            d=date.fromisoformat(r['date'])
            if not(date(2022,11,12)<=d<=date(2024,12,29)): raise RuntimeError(f'forbidden source date {d}')
            rows.append({'signal_date':d,'net_flow_raw':int(r['net_flow_raw']),'net_flow_usdt':float(r['net_flow_usdt'])})
    if len(rows)!=779: raise RuntimeError(f'expected 779 signal rows, got {len(rows)}')
    return receipt,receipts[0],csvs[0],rows

def target_ms(d:date,h:int,m:int):
    return int(datetime.combine(d,dtime(h,m),tzinfo=timezone.utc).timestamp()*1000)

def acquire_prices(signal_rows):
    needed={}
    for r in signal_rows:
        od=r['signal_date']+timedelta(days=1)
        if od.year>=2025: raise RuntimeError(f'forbidden outcome day {od}')
        needed[target_ms(od,0,15)]=('entry',r['signal_date'].isoformat())
        needed[target_ms(od,1,15)]=('exit',r['signal_date'].isoformat())
    prices={}; manifests=[]
    start=date(2022,11,1); end=date(2024,12,31)
    for y,m in month_iter(start,end):
        if y>=2025: raise RuntimeError('forbidden Binance month')
        fn=f'BTCUSDT-1m-{y:04d}-{m:02d}.zip'
        url=f'{BINANCE}/{fn}'; cu=url+'.CHECKSUM'
        cs,cb=get(cu); zs,zb=get(url)
        if cs!=200 or zs!=200: raise RuntimeError(f'bad Binance status {fn}: {cs}/{zs}')
        exp=expected_checksum(cb.decode(errors='replace'),fn); actual=hashlib.sha256(zb).hexdigest()
        if actual!=exp: raise RuntimeError(f'Binance checksum mismatch {fn}')
        found=0
        with zipfile.ZipFile(io.BytesIO(zb)) as zf:
            names=[n for n in zf.namelist() if n.lower().endswith('.csv')]
            if len(names)!=1: raise RuntimeError(f'unexpected ZIP members {fn}: {names}')
            with zf.open(names[0]) as raw:
                txt=io.TextIOWrapper(raw,encoding='utf-8',newline='')
                rd=csv.reader(txt)
                for row in rd:
                    if not row: continue
                    try: ts=int(row[0])
                    except ValueError: continue
                    if ts in needed:
                        if len(row)<2: raise RuntimeError(f'bad kline row {fn}')
                        prices[ts]=float(row[1]); found+=1
        manifests.append({'file':fn,'url':url,'checksum_url':cu,'sha256':actual,'bytes':len(zb),'target_rows_found':found})
    missing=sorted(set(needed)-set(prices))
    if missing: raise RuntimeError(f'missing frozen Binance candles count={len(missing)} first={missing[:5]}')
    return needed,prices,manifests

def ols_beta(x,y):
    n=len(x); xb=sum(x)/n; yb=sum(y)/n
    den=sum((v-xb)**2 for v in x)
    if den<=0: raise RuntimeError('zero x variance')
    beta=sum((x[i]-xb)*(y[i]-yb) for i in range(n))/den
    alpha=yb-beta*xb
    return alpha,beta,xb,yb,den

def moving_block_null_p(x,y,beta_obs,block=7,reps=20000,seed=20260914):
    n=len(x); _,_,xb,yb,den=ols_beta(x,y)
    xc=[v-xb for v in x]
    # Restricted H0 beta=0 residuals; preserve serial dependence by circular moving blocks.
    resid=[v-yb for v in y]
    rng=random.Random(seed); ge=0
    blocks=math.ceil(n/block)
    for _ in range(reps):
        num=0.0; pos=0
        for __ in range(blocks):
            s=rng.randrange(n)
            for j in range(block):
                if pos>=n: break
                num += xc[pos]*resid[(s+j)%n]
                pos+=1
        b=num/den
        if b>=beta_obs: ge+=1
    return (ge+1)/(reps+1),ge

def profit_factor(xs):
    gp=sum(v for v in xs if v>0); gl=-sum(v for v in xs if v<0)
    if gl==0: return math.inf if gp>0 else 0.0
    return gp/gl

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source_receipt,source_receipt_path,source_csv_path,signals=load_source()
    needed,prices,manifests=acquire_prices(signals)
    obs=[]
    for r in signals:
        od=r['signal_date']+timedelta(days=1)
        ets=target_ms(od,0,15); xts=target_ms(od,1,15)
        ep=prices[ets]; xp=prices[xts]
        ret=xp/ep-1.0
        flow=r['net_flow_usdt']; s=1 if flow>0 else (-1 if flow<0 else 0)
        gross_bps=s*ret*10000 if s else 0.0
        net10=gross_bps-COST_BASE_BPS if s else 0.0
        net14=gross_bps-COST_STRESS_BPS if s else 0.0
        obs.append({'signal_date':r['signal_date'].isoformat(),'outcome_date':od.isoformat(),'net_flow_usdt':flow,'net_flow_billion':flow/1e9,'entry_ts_ms':ets,'entry_price':ep,'exit_ts_ms':xts,'exit_price':xp,'btc_return':ret,'direction':s,'strategy_gross_bps':gross_bps,'net10_bps':net10,'net14_bps':net14})
    if len(obs)!=779: raise RuntimeError('observation count mismatch')
    x=[o['net_flow_billion'] for o in obs]; y=[o['btc_return'] for o in obs]
    alpha,beta,xb,yb,den=ols_beta(x,y)
    p,boot_ge=moving_block_null_p(x,y,beta,BOOT_BLOCK,BOOT_REPS,SEED)
    active=[o for o in obs if o['direction']!=0]
    gross=[o['strategy_gross_bps'] for o in active]; n10=[o['net10_bps'] for o in active]; n14=[o['net14_bps'] for o in active]
    cal={}
    for o in active:
        yr=o['signal_date'][:4]; cal.setdefault(yr,[]).append(o['net14_bps'])
    cal_stats={yr:{'n':len(v),'mean_net14_bps':sum(v)/len(v)} for yr,v in sorted(cal.items())}
    nonneg=sum(1 for v in cal_stats.values() if v['mean_net14_bps']>=0)
    full_year_deep_negative=any(cal_stats.get(yr,{}).get('mean_net14_bps',0)<-10 for yr in ('2023','2024'))
    mean10=sum(n10)/len(n10) if n10 else float('nan'); mean14=sum(n14)/len(n14) if n14 else float('nan')
    pf14=profit_factor(n14)
    primary_pass=(beta>0 and p<0.05)
    economic_pass=(mean10>0 and mean14>0 and pf14>1.0)
    stability_pass=(nonneg>=2 and not full_year_deep_negative)
    promotion=primary_pass and economic_pass and stability_pass
    if promotion: classification='DISCOVERY_SURVIVOR'
    elif not primary_pass: classification='NO_STATISTICAL_EDGE'
    elif not economic_pass: classification='NEGATIVE_EXPECTANCY'
    else: classification='STABILITY_FAILURE'
    economic_classification='POSITIVE_NET_EXPECTANCY' if economic_pass else 'NEGATIVE_EXPECTANCY'

    obs_path=OUT/'DISCOVERY_OBSERVATIONS.csv'
    with obs_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(obs[0].keys())); w.writeheader(); w.writerows(obs)
    manifest_path=OUT/'BINANCE_ARCHIVE_MANIFEST.json'
    manifest_path.write_text(json.dumps(manifests,indent=2,sort_keys=True)+'\n')
    protocol=Path('labs/STABLECOIN_EXCHANGE_FLOW_001/FINAL_PRE_DISCOVERY_PROTOCOL_V0.1.md')
    amendment=Path('labs/STABLECOIN_EXCHANGE_FLOW_001/PRE_DISCOVERY_TECHNICAL_AMENDMENT_001_BOUNDARY_SEARCH.md')
    receipt={
      'lab_id':LAB,'mve_id':MVE,'classification':classification,'economic_classification':economic_classification,'promotion_candidate':promotion,
      'n':len(obs),'active_strategy_n':len(active),'primary':{'alpha_return':alpha,'beta_return_per_1bn_usdt':beta,'beta_bps_per_1bn_usdt':beta*10000,'bootstrap_method':'restricted-null circular moving-block residual bootstrap','bootstrap_block_days':BOOT_BLOCK,'bootstrap_reps':BOOT_REPS,'seed':SEED,'one_sided_p_beta_le_0':p,'bootstrap_beta_ge_observed_count':boot_ge,'pass':primary_pass},
      'economic':{'mean_gross_bps':sum(gross)/len(gross) if gross else None,'mean_net10_bps':mean10,'mean_net14_bps':mean14,'profit_factor_net14':pf14,'pass':economic_pass},
      'stability':{'calendar_net14':cal_stats,'nonnegative_calendar_partitions':nonneg,'full_year_deep_negative':full_year_deep_negative,'pass':stability_pass},
      'promotion_gates':{'beta_positive':beta>0,'bootstrap_p_lt_0_05':p<0.05,'mean_net10_positive':mean10>0,'mean_net14_positive':mean14>0,'pf_net14_gt_1':pf14>1.0,'calendar_stability':stability_pass},
      'source_receipt_sha256':file_sha(source_receipt_path),'source_csv_sha256':file_sha(source_csv_path),'protocol_sha256':file_sha(protocol),'technical_amendment_sha256':file_sha(amendment),'observations_sha256':file_sha(obs_path),'binance_manifest_sha256':file_sha(manifest_path),
      'binance_files':len(manifests),'binance_month_start':'2022-11','binance_month_end':'2024-12','binance_checksums_verified':True,
      'access_2025':False,'access_2026':False,'live_trading':False,'exchange_mutation':False,'post_outcome_tuning':False,
    }
    (OUT/'DISCOVERY_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+'\n')
    closeout=f'''# {LAB} — MVE0 DISCOVERY CLOSEOUT\n\n**MVE:** `{MVE}`  \n**CLASSIFICATION:** `{classification}`  \n**PROMOTION:** `{str(promotion).upper()}`\n\n## Frozen primary test\n\n- N: {len(obs)}\n- beta: {beta*10000:.6f} bps BTC return per +$1bn USDT basket net flow\n- one-sided 7-day block-bootstrap p: {p:.8f}\n- primary pass: {primary_pass}\n\n## Companion economic test\n\n- mean gross: {receipt['economic']['mean_gross_bps']:.6f} bps/trade\n- mean NET10: {mean10:.6f} bps/trade\n- mean NET14: {mean14:.6f} bps/trade\n- PF NET14: {pf14:.6f}\n- economic pass: {economic_pass}\n\n## Stability\n\n```json\n{json.dumps(cal_stats,indent=2,sort_keys=True)}\n```\n\n## Governance\n\n2025 accessed: NO  \n2026 accessed: NO  \nLive trading: NO  \nExchange mutation: NO  \nPost-outcome tuning: NO\n\nExact MVE outcome is final under the frozen protocol.\n'''
    (OUT/'DISCOVERY_CLOSEOUT.md').write_text(closeout,encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
