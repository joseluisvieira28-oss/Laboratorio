#!/usr/bin/env python3
"""ARQ-001-MTF-001 frozen local Discovery runner.

Inputs:
- operator-supplied official TradingView CRYPTOCAP 4H CSVs;
- checksum-audited normalized Binance 1H corpus produced by the frozen source workflow.

Discovery only: calendar year 2024. 2025/2026 scientific values are not parsed.
"""

from __future__ import annotations

import argparse, csv, gzip, hashlib, io, json, math, statistics, zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
from pathlib import Path

import numpy as np

TV_HASHES={
    "BTC.D":"d833ddd89913f076f9797ca89014371ed806468ae94bd3084ccbb58f7ba46208",
    "USDT.D":"66eae148679447a788ee5ccd40e50a5c58766ed185f94f89c83a722d29e71bcf",
    "TOTAL3":"b151d0bc36090b3433a171dd0d28e777c794f7ab7f428ea5e5ddbd12f24749d7",
}
BINANCE_ARTIFACT_SHA256="81665e40e15c7f0836f2cbd7681627ccb373896c9f1354d9d04b6e60116d92c8"
BINANCE_INNER_GZIP_SHA256="87b05645bacd11e18870c2d174c32c770bf354c5585b90a3c57345a64508b1e2"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
ALTS=SYMBOLS[1:]
UTC=timezone.utc
DISCOVERY_START=datetime(2024,1,1,tzinfo=UTC)
DISCOVERY_END=datetime(2025,1,1,tzinfo=UTC)
COSTS={"LOW10":0.0010,"BASE12":0.0012,"STRESS14":0.0014}
BOOT_REPS=10000
BOOT_SEED=140001
OUT=Path("ARQ001_MTF_DISCOVERY_RECEIPT_V0.1.json")

class FrozenError(RuntimeError): pass

@dataclass(frozen=True)
class Candle:
    ts:int
    op:float
    hi:float
    lo:float
    cl:float

@dataclass(frozen=True)
class Feature:
    event_ts:int
    symbol:str
    beta:float
    btc_signal:float
    gap:float
    btc_z:float
    gap_z:float

@dataclass(frozen=True)
class Obs:
    event_ts:int
    day:str
    symbol:str
    direction:int
    btc_z:float
    gap_z:float
    regime_b:bool
    regime_c:bool
    regime_d:bool
    gross:float
    low10:float
    base12:float
    stress14:float

def sha256_path(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def load_tv(path:Path, expected_hash:str, label:str)->dict[int,Candle]:
    actual=sha256_path(path)
    if actual!=expected_hash:
        raise FrozenError(f"TV_HASH_MISMATCH:{label}:{actual}")
    out={}
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required={"time","open","high","low","close"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise FrozenError(f"TV_SCHEMA:{label}:{reader.fieldnames}")
        for row in reader:
            ts=int(float(row["time"]))
            # Firewall: only convert economic fields for 2024 rows.
            if ts < int(DISCOVERY_START.timestamp()) or ts >= int(DISCOVERY_END.timestamp()):
                continue
            if ts%14400!=0: raise FrozenError(f"TV_NOT_4H:{label}:{ts}")
            vals=[float(row[k]) for k in ("open","high","low","close")]
            if not all(math.isfinite(x) and x>0 for x in vals):
                raise FrozenError(f"TV_BAD_OHLC:{label}:{ts}")
            if ts in out: raise FrozenError(f"TV_DUP_TS:{label}:{ts}")
            out[ts]=Candle(ts,*vals)
    expected=list(range(int(DISCOVERY_START.timestamp()),int(DISCOVERY_END.timestamp()),14400))
    if sorted(out)!=expected:
        raise FrozenError(f"TV_2024_GRID:{label}:{len(out)}/{len(expected)}")
    return out

def load_binance_artifact(path:Path)->dict[str,dict[int,Candle]]:
    actual=sha256_path(path)
    if actual!=BINANCE_ARTIFACT_SHA256:
        raise FrozenError(f"BINANCE_ARTIFACT_HASH:{actual}")
    with zipfile.ZipFile(path,"r") as z:
        names=z.namelist()
        if names!=["arq001_mtf_binance_1h_2023_12_2024.csv.gz"]:
            raise FrozenError(f"BINANCE_ARTIFACT_CONTENTS:{names}")
        gz=z.read(names[0])
    if hashlib.sha256(gz).hexdigest()!=BINANCE_INNER_GZIP_SHA256:
        raise FrozenError("BINANCE_GZIP_HASH")
    raw=gzip.decompress(gz).decode("utf-8")
    out={s:{} for s in SYMBOLS}
    reader=csv.DictReader(io.StringIO(raw))
    if reader.fieldnames!=["symbol","open_time_ms","open","high","low","close"]:
        raise FrozenError(f"BINANCE_SCHEMA:{reader.fieldnames}")
    min_ts=int(datetime(2023,12,1,tzinfo=UTC).timestamp())
    max_ts=int(DISCOVERY_END.timestamp())
    for row in reader:
        s=row["symbol"]
        if s not in out: raise FrozenError(f"BINANCE_SYMBOL:{s}")
        ts=int(row["open_time_ms"])//1000
        if ts<min_ts or ts>=max_ts:
            raise FrozenError(f"BINANCE_TS_SCOPE:{s}:{ts}")
        vals=[float(row[k]) for k in ("open","high","low","close")]
        if not all(math.isfinite(x) and x>0 for x in vals):
            raise FrozenError(f"BINANCE_BAD_OHLC:{s}:{ts}")
        if ts in out[s]: raise FrozenError(f"BINANCE_DUP_TS:{s}:{ts}")
        out[s][ts]=Candle(ts,*vals)
    expected=list(range(min_ts,max_ts,3600))
    for s in SYMBOLS:
        if sorted(out[s])!=expected:
            raise FrozenError(f"BINANCE_GRID:{s}:{len(out[s])}/{len(expected)}")
    return out

def candle_return(c:Candle)->float:
    return math.log(c.cl/c.op)

def beta_for_event(data, alt:str, event_ts:int)->float|None:
    # Amendment B: exactly H=T-721h through T-2h inclusive = 720 possible rows.
    hours=[event_ts-721*3600+i*3600 for i in range(720)]
    pairs=[]
    for h in hours:
        b=data["BTCUSDT"].get(h); a=data[alt].get(h)
        if b is None or a is None: continue
        pairs.append((candle_return(b),candle_return(a)))
    if len(pairs)<684: return None
    x=np.array([p[0] for p in pairs],dtype=float)
    y=np.array([p[1] for p in pairs],dtype=float)
    xm=x.mean(); ym=y.mean()
    denom=float(np.sum((x-xm)**2))
    if not math.isfinite(denom) or denom<=0: return None
    beta=float(np.sum((x-xm)*(y-ym))/denom)
    return beta if math.isfinite(beta) else None

def zscore(x:float, hist:list[float])->float|None:
    if len(hist)<150: return None
    mu=statistics.fmean(hist)
    sd=statistics.stdev(hist)
    if not math.isfinite(sd) or sd<=0: return None
    z=(x-mu)/sd
    if not math.isfinite(z): return None
    return max(-5.0,min(5.0,z))

def build_features(data)->dict[tuple[int,str],Feature]:
    # Need Binance-only candidate boundaries from Dec 2023 onward to create causal z warm-up.
    start=int(datetime(2023,12,1,4,tzinfo=UTC).timestamp())
    end=int(DISCOVERY_END.timestamp())
    event_ts=list(range(start,end,14400))
    raw_btc={}
    raw_gap={a:{} for a in ALTS}
    raw_beta={a:{} for a in ALTS}

    for t in event_ts:
        sig=t-3600
        btc=data["BTCUSDT"].get(sig)
        if btc is None: continue
        br=candle_return(btc)
        raw_btc[t]=br
        for a in ALTS:
            ac=data[a].get(sig)
            if ac is None: continue
            beta=beta_for_event(data,a,t)
            if beta is None: continue
            gap=candle_return(ac)-beta*br
            if math.isfinite(gap):
                raw_gap[a][t]=gap
                raw_beta[a][t]=beta

    features={}
    for t in event_ts:
        if t not in raw_btc: continue
        lo=t-30*86400
        btc_hist=[v for tt,v in raw_btc.items() if lo<=tt<t]
        bz=zscore(raw_btc[t],btc_hist)
        if bz is None: continue
        for a in ALTS:
            if t not in raw_gap[a]: continue
            gh=[v for tt,v in raw_gap[a].items() if lo<=tt<t]
            gz=zscore(raw_gap[a][t],gh)
            if gz is None: continue
            features[(t,a)]=Feature(t,a,raw_beta[a][t],raw_btc[t],raw_gap[a][t],bz,gz)
    return features

def regime_at(tv:dict[str,dict[int,Candle]], event_ts:int)->tuple[float,float,float]:
    candle_ts=event_ts-14400
    vals=[]
    for label in ("BTC.D","USDT.D","TOTAL3"):
        c=tv[label].get(candle_ts)
        if c is None: raise FrozenError(f"REGIME_CANDLE_MISSING:{label}:{candle_ts}")
        vals.append(math.log(c.cl/c.op))
    return tuple(vals)

def classify_regime(direction:int, r:tuple[float,float,float])->tuple[bool,bool,bool]:
    bd,ud,t3=r
    if direction>0:
        b=bd<0
        c=b and ud<0
        d=c and t3>0
    else:
        b=bd>0
        c=b and ud>0
        d=c and t3<0
    return b,c,d

def discovery(data,tv,features)->tuple[list[Obs],dict]:
    obs=[]
    A_count=0; B_count=0; C_count=0; D_count=0
    for t in range(int(datetime(2024,1,1,4,tzinfo=UTC).timestamp()),
                   int(DISCOVERY_END.timestamp()),14400):
        # Target candle must finish inside 2024.
        if t+3600>int(DISCOVERY_END.timestamp()): continue
        r=regime_at(tv,t)
        for a in ALTS:
            f=features.get((t,a))
            if f is None: continue
            direction=0
            if f.btc_z>=0.75 and f.gap_z<=-1.0: direction=1
            elif f.btc_z<=-0.75 and f.gap_z>=1.0: direction=-1
            if direction==0: continue
            A_count+=1
            b,c,d=classify_regime(direction,r)
            B_count+=int(b); C_count+=int(c); D_count+=int(d)
            target=data[a].get(t)
            if target is None: raise FrozenError(f"TARGET_MISSING:{a}:{t}")
            gross=direction*candle_return(target)
            day=datetime.fromtimestamp(t,tz=UTC).date().isoformat()
            obs.append(Obs(t,day,a,direction,f.btc_z,f.gap_z,b,c,d,gross,
                           gross-COSTS["LOW10"],gross-COSTS["BASE12"],gross-COSTS["STRESS14"]))
    return obs,{"A":A_count,"B":B_count,"C":C_count,"D":D_count}

def mean(xs):
    return float(statistics.fmean(xs)) if xs else None

def bootstrap_days(confirmed:list[Obs])->dict:
    byday=defaultdict(list)
    for o in confirmed: byday[o.day].append(o.base12)
    days=sorted(byday)
    if not days: return {"valid":False,"reason":"NO_CONFIRMED"}
    rng=np.random.default_rng(BOOT_SEED)
    means=np.empty(BOOT_REPS,dtype=float)
    nday=len(days)
    for i in range(BOOT_REPS):
        pick=rng.integers(0,nday,size=nday)
        vals=[]
        for ix in pick: vals.extend(byday[days[int(ix)]])
        means[i]=np.mean(vals)
    return {
        "valid":True,"repetitions":BOOT_REPS,"seed":BOOT_SEED,
        "unique_utc_days":nday,
        "ci95_low":float(np.percentile(means,2.5)),
        "ci95_high":float(np.percentile(means,97.5)),
        "bootstrap_mean":float(np.mean(means))
    }

def evaluate(obs,ablation):
    confirmed=[o for o in obs if o.regime_d]
    rejected=[o for o in obs if not o.regime_d]
    per_alt={}
    for a in ALTS:
        xs=[o for o in confirmed if o.symbol==a]
        per_alt[a]={
            "n":len(xs),
            "base12_mean":mean([o.base12 for o in xs]),
            "stress14_mean":mean([o.stress14 for o in xs]),
        }

    base_mean=mean([o.base12 for o in confirmed])
    stress_mean=mean([o.stress14 for o in confirmed])
    rejected_mean=mean([o.base12 for o in rejected])
    delta=None if base_mean is None or rejected_mean is None else base_mean-rejected_mean
    boot=bootstrap_days(confirmed)

    # Amendment D exact best-1% removal.
    k=max(1,math.ceil(0.01*len(confirmed))) if confirmed else 0
    ranked=sorted(confirmed,key=lambda o:(-o.base12,o.event_ts,o.symbol))
    trimmed=ranked[k:] if k else []
    trimmed_mean=mean([o.base12 for o in trimmed])

    alt_means=[(a,per_alt[a]["base12_mean"]) for a in ALTS if per_alt[a]["base12_mean"] is not None]
    if alt_means:
        best_alt=sorted(alt_means,key=lambda x:(-x[1],x[0]))[0][0]
        without_best=[o for o in confirmed if o.symbol!=best_alt]
        without_best_mean=mean([o.base12 for o in without_best])
    else:
        best_alt=None; without_best_mean=None

    positive_alts=sum(1 for a in ALTS if per_alt[a]["base12_mean"] is not None and per_alt[a]["base12_mean"]>0)
    alts_n20=sum(1 for a in ALTS if per_alt[a]["n"]>=20)
    gates={
        "source_provenance_pass":True,
        "d_confirmed_n_gte_200":len(confirmed)>=200,
        "at_least_4_alts_n_gte_20":alts_n20>=4,
        "base12_mean_gt_0":base_mean is not None and base_mean>0,
        "stress14_mean_gt_0":stress_mean is not None and stress_mean>0,
        "confirmed_minus_rejected_base12_gt_0":delta is not None and delta>0,
        "bootstrap_95_lower_gt_0":boot.get("valid") is True and boot["ci95_low"]>0,
        "at_least_3_of_5_alts_positive_base12":positive_alts>=3,
        "remove_best_1pct_still_positive":trimmed_mean is not None and trimmed_mean>0,
        "remove_best_alt_still_positive":without_best_mean is not None and without_best_mean>0,
    }
    survived=all(gates.values())
    return {
        "classification":"DISCOVERY_SURVIVES_NOT_EDGE" if survived else "DISCOVERY_FAIL_NO_PROMOTION",
        "ablation_counts":ablation,
        "baseline_A_n":len(obs),
        "d_confirmed_n":len(confirmed),
        "d_rejected_n":len(rejected),
        "d_confirmed_low10_mean":mean([o.low10 for o in confirmed]),
        "d_confirmed_base12_mean":base_mean,
        "d_confirmed_stress14_mean":stress_mean,
        "d_rejected_base12_mean":rejected_mean,
        "confirmed_minus_rejected_base12_delta":delta,
        "per_alt":per_alt,
        "positive_alt_count_base12":positive_alts,
        "alts_with_n_gte_20":alts_n20,
        "bootstrap_utc_day":boot,
        "best_1pct_removed_count":k,
        "best_1pct_removed_base12_mean":trimmed_mean,
        "best_alt_removed":best_alt,
        "remove_best_alt_base12_mean":without_best_mean,
        "gates":gates,
        "all_gates_pass":survived,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--btc-d",required=True)
    ap.add_argument("--usdt-d",required=True)
    ap.add_argument("--total3",required=True)
    ap.add_argument("--binance-artifact",required=True)
    ap.add_argument("--out",default=str(OUT))
    args=ap.parse_args()

    paths={
        "BTC.D":Path(args.btc_d),
        "USDT.D":Path(args.usdt_d),
        "TOTAL3":Path(args.total3),
    }
    receipt={
        "lab_id":"ARQ-001-MTF-001",
        "date_utc":"2026-09-23",
        "authority":[
            "ARQ001_MTF_PREOUTCOME_AUTHORITY_V0.1.md",
            "ARQ001_MTF_PREOUTCOME_AMENDMENT_A_V0.1.md",
            "ARQ001_MTF_PREOUTCOME_AMENDMENT_B_V0.1.md",
            "ARQ001_MTF_PREOUTCOME_AMENDMENT_C_V0.1.md",
            "ARQ001_MTF_PREOUTCOME_AMENDMENT_D_V0.1.md",
        ],
        "classification":"RUNNING",
        "source":{
            "tradingview_sha256":{k:sha256_path(v) for k,v in paths.items()},
            "binance_artifact_sha256":sha256_path(Path(args.binance_artifact)),
            "binance_source_workflow_run":35893432555,
            "binance_source_census_sha256":"b9e6350d3b2559b9d795a4cded381668d69be4717e1a8532a4f73fc03dccc7e4",
        },
        "firewall":{
            "discovery_year":2024,
            "confirmation_2025_accessed":False,
            "final_holdout_2026_accessed":False,
            "live_trading":False,"orders":False,"exchange_mutation":False,"wallet_access":False,
            "main_merge":False
        },
        "errors":[]
    }
    try:
        tv={k:load_tv(paths[k],TV_HASHES[k],k) for k in paths}
        data=load_binance_artifact(Path(args.binance_artifact))
        features=build_features(data)
        obs,ablation=discovery(data,tv,features)
        result=evaluate(obs,ablation)
        receipt["eligible_feature_rows"]=len(features)
        receipt["discovery"]=result
        receipt["classification"]=result["classification"]
    except Exception as e:
        receipt["classification"]="TECHNICAL_FAIL_CLOSED"
        receipt["errors"].append(f"{type(e).__name__}:{e}")
    payload=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["receipt_sha256"]=hashlib.sha256(payload).hexdigest()
    Path(args.out).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "lab_id":receipt["lab_id"],
        "classification":receipt["classification"],
        "discovery":receipt.get("discovery"),
        "firewall":receipt["firewall"],
        "errors":receipt["errors"],
        "receipt_sha256":receipt["receipt_sha256"]
    },sort_keys=True))
    return 0 if receipt["classification"] in {"DISCOVERY_SURVIVES_NOT_EDGE","DISCOVERY_FAIL_NO_PROMOTION"} else 1

if __name__=="__main__":
    raise SystemExit(main())
