#!/usr/bin/env python3
import argparse, json, math, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

SYMBOLS=['BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','XRPUSDT','DOGEUSDT']

def load_csvs(root,symbol):
    files=sorted(Path(root).glob(f'{symbol}*.zip'))
    if not files: raise FileNotFoundError(symbol)
    parts=[]
    for zf in files:
        with zipfile.ZipFile(zf) as z:
            for n in z.namelist():
                if n.endswith('.csv'):
                    x=pd.read_csv(z.open(n),header=None,usecols=range(6),names=['open_time','open','high','low','close','volume'])
                    x['ts']=pd.to_datetime(x.open_time,unit='ms',utc=True,errors='coerce')
                    parts.append(x[['ts','open','high','low','close','volume']])
    x=pd.concat(parts).dropna().sort_values('ts').drop_duplicates('ts')
    return x[(x.ts>='2022-01-01')&(x.ts<'2024-01-01')]

def hourly(x):
    x=x.set_index('ts')
    h=x.resample('1h').agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),n=('close','size'))
    h['valid']=h.n.eq(60)
    # segment restarts after any incomplete/missing hour
    h['seg']=(~h.valid).cumsum()
    return h

def trades_for(symbol,h):
    out=[]
    for _,g in h.groupby('seg'):
        g=g[g.valid].copy()
        if len(g)<25: continue
        g['mid']=g.close.rolling(20).mean()
        g['sd']=g.close.rolling(20).std(ddof=0)
        g['lo']=g.mid-2*g.sd; g['hi']=g.mid+2*g.sd
        g['dir']=np.where(g.close<g.lo,1,np.where(g.close>g.hi,-1,0))
        idx=list(g.index); i=19
        while i < len(g)-5:
            d=int(g.iloc[i].dir)
            if d==0: i+=1; continue
            entry_i=i+1; exit_i=entry_i+4
            ep=float(g.iloc[entry_i].open); xp=float(g.iloc[exit_i].open)
            gross=d*math.log(xp/ep)*10000
            out.append({'symbol':symbol,'signal_ts':str(idx[i]),'entry_ts':str(idx[entry_i]),'exit_ts':str(idx[exit_i]),'direction':d,'gross_bps':gross,'net10_bps':gross-10,'net14_bps':gross-14})
            i=exit_i
    return out

def pf(v):
    v=np.asarray(v,float); pos=v[v>0].sum(); neg=-v[v<0].sum()
    return float(pos/neg) if neg>0 else float('inf')

def metrics(t):
    v=t.net10_bps.to_numpy(float)
    return {'n':int(len(t)),'gross_mean_bps':float(t.gross_bps.mean()),'net10_mean_bps':float(t.net10_bps.mean()),'net14_mean_bps':float(t.net14_bps.mean()),'profit_factor_net10':pf(v),'win_rate_net10':float((v>0).mean())}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-root',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    alltr=[]
    for s in SYMBOLS: alltr += trades_for(s,hourly(load_csvs(a.data_root,s)))
    t=pd.DataFrame(alltr)
    if t.empty: raise RuntimeError('NO_TRADES')
    m=metrics(t); gate=m['n']>=300 and m['net10_mean_bps']>0 and m['profit_factor_net10']>1
    per={s:metrics(g) for s,g in t.groupby('symbol')}
    t['quarter']=pd.to_datetime(t.entry_ts,utc=True).dt.to_period('Q').astype(str)
    quarters={q:metrics(g) for q,g in t.groupby('quarter')}
    result={'lab':'CIGL-BB-01','phase':'DISCOVERY_2022_2023','rule':'BB20_2SD_POP_MEAN_REVERSION_1H_HOLD4','metrics':m,'per_asset':per,'quarters':quarters,'discovery_gate_pass':gate,'status':'DISCOVERY_PASS_2024_ELIGIBLE' if gate else 'DISCOVERY_FAIL_NO_VALIDATION_ACCESS','protected_periods':{'2024':'UNOPENED_BY_THIS_RUN','2025':'PROTECTED_UNOPENED','2026':'LOCKED_UNOPENED'}}
    t.to_csv(out/'CIGL_BB_01_DISCOVERY_TRADES.csv',index=False)
    (out/'CIGL_BB_01_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
