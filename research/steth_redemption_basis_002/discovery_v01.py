#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,json,math,os,random,statistics,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from decimal import Decimal,getcontext
from pathlib import Path
from typing import Any
import requests
from eth_hash.auto import keccak

getcontext().prec=80
LAB_ID="STETH-REDEMPTION-BASIS-002"
START_TS=int(datetime(2023,5,16,12,tzinfo=timezone.utc).timestamp())
END_TS=int(datetime(2024,12,31,12,tzinfo=timezone.utc).timestamp())
N_SNAP=596; START_BLOCK=17_272_128; END_BLOCK=21_522_315
NOTIONAL=10**19; E27=10**27; MAX_HOLD=14*86400
BASE_RESERVE=10**16; STRESS_RESERVE=25*10**15
STETH="0xae7ab96520de3a18e5e111b5eaab095312d7fe84"
QUEUE="0x889edc2edab5f40e902b864ad4d7ade8e412f9b1"
CURVE="0xdc24316b9ae028f1497c275eb9192a3ea0f67022"
PROVIDERS=["https://eth-mainnet.public.blastapi.io","https://rpc.mevblocker.io","https://ethereum.blinklabs.xyz/"]
SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"; TRANSIENT={429,500,502,503,504,529}
OUT=Path("out/steth_redemption_basis_002_discovery"); OUT.mkdir(parents=True,exist_ok=True)
STATS=Counter()

def sel(s): return "0x"+keccak(s.encode())[:4].hex()
def top(s): return "0x"+keccak(s.encode()).hex()
def u(x): return int(x).to_bytes(32,"big").hex()
def si(x): return int(x).to_bytes(32,"big",signed=True).hex()
C_DY=sel("get_dy(int128,int128,uint256)")+si(0)+si(1)+u(NOTIONAL)
C_LAST=sel("getLastRequestId()"); C_UNF=sel("unfinalizedStETH()"); C_CP=sel("getLastCheckpointIndex()")
S_SHARES=sel("getSharesByPooledEth(uint256)")
T_REBASE=top("TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)").lower()
T_FIN=top("WithdrawalsFinalized(uint256,uint256,uint256,uint256,uint256)").lower()
CP_POS=int.from_bytes(keccak(b"lido.WithdrawalQueue.checkpoints"),"big")

class DError(RuntimeError): pass

def load_source():
    hits=[]
    for p in Path("downloaded_source").rglob("*.json"):
        try:o=json.loads(p.read_text())
        except:continue
        if o.get("lab_id")==LAB_ID and o.get("classification")=="SOURCE_DATA_PASS": hits.append((p,o))
    if len(hits)!=1: raise DError(f"source receipt count={len(hits)}")
    p,o=hits[0]
    if o.get("agreed_start_block")!=START_BLOCK or o.get("agreed_end_block")!=END_BLOCK or o.get("expected_daily_snapshot_population")!=N_SNAP: raise DError("source boundary mismatch")
    s=o.get("safety",{})
    if any(s.get(k) is not False for k in ("accessed_2025_or_2026","market_prices_opened","returns_opened","pnl_opened")): raise DError("source safety mismatch")
    return hashlib.sha256(p.read_bytes()).hexdigest()

def post(ep,payload,retries=5):
    last=None
    for k in range(retries):
        try:
            r=requests.post(ep,json=payload,timeout=(15,90),headers={"Content-Type":"application/json","User-Agent":LAB_ID+"/discovery-v0.1"})
            STATS["rpc_http"]+=1
            if r.status_code in TRANSIENT: STATS["rpc_transient"]+=1; r.close(); time.sleep(min(8,1.2*(k+1))); continue
            r.raise_for_status(); z=r.json(); r.close(); return z
        except Exception as e:
            last=e; STATS["rpc_errors"]+=1
            if k<retries-1: time.sleep(min(8,1.2*(k+1)))
    raise DError(f"rpc transport {ep}: {last}")

def one(ep,m,p):
    z=post(ep,{"jsonrpc":"2.0","id":1,"method":m,"params":p})
    return {"ok":isinstance(z,dict) and z.get("error") is None,"result":z.get("result") if isinstance(z,dict) else None}

def batch(ep,calls,chunk=40):
    out=[None]*len(calls)
    for a in range(0,len(calls),chunk):
        cc=calls[a:a+chunk]; payload=[{"jsonrpc":"2.0","id":a+i,"method":m,"params":p} for i,(m,p) in enumerate(cc)]
        try:z=post(ep,payload)
        except:z=None
        if isinstance(z,list):
            d={x.get("id"):x for x in z if isinstance(x,dict)}
            for i in range(len(cc)):
                x=d.get(a+i); out[a+i]={"ok":bool(x and x.get("error") is None),"result":x.get("result") if x else None}
        else:
            STATS["batch_fallback"]+=1
            for i,(m,p) in enumerate(cc): out[a+i]=one(ep,m,p)
    return out

def hv(o):
    if not o or not o.get("ok") or not isinstance(o.get("result"),str) or not o["result"].startswith("0x"): return None
    try:return int(o["result"],16)
    except:return None

def quorum(per,label):
    n=len(per[0]); ans=[]
    for i in range(n):
        v=defaultdict(int)
        for rows in per:
            x=hv(rows[i])
            if x is not None:v[x]+=1
        good=[x for x,c in v.items() if c>=2]
        if len(good)!=1: raise DError(f"quorum {label} index={i}")
        ans.append(good[0])
    return ans

def parse_header(o):
    if not o.get("ok") or not isinstance(o.get("result"),dict): return None
    h=o["result"]
    try:return {"n":int(h["number"],16),"ts":int(h["timestamp"],16),"hash":h["hash"].lower(),"bf":int(h.get("baseFeePerGas","0x0"),16)}
    except:return None

def headers(ep,blocks):
    bb=list(dict.fromkeys(blocks)); rr=batch(ep,[("eth_getBlockByNumber",[hex(b),False]) for b in bb]); out={}
    for b,r in zip(bb,rr):
        h=parse_header(r)
        if h:out[b]=h
    return out

def map_blocks(targets):
    spanT=END_TS-START_TS; spanB=END_BLOCK-START_BLOCK; lo=[]; hi=[]
    for t in targets:
        if t==START_TS: lo.append(START_BLOCK-1); hi.append(START_BLOCK); continue
        if t==END_TS: lo.append(END_BLOCK-1); hi.append(END_BLOCK); continue
        e=START_BLOCK+spanB*(t-START_TS)//spanT; lo.append(max(START_BLOCK,e-2000)); hi.append(min(END_BLOCK,e+2000))
    hh=headers(PROVIDERS[0],lo+hi)
    for i,t in enumerate(targets):
        if lo[i] not in hh or hi[i] not in hh or not(hh[lo[i]]["ts"]<t<=hh[hi[i]]["ts"]): lo[i],hi[i]=START_BLOCK-1,END_BLOCK
    for _ in range(30):
        ix=[i for i in range(len(targets)) if hi[i]-lo[i]>1]
        if not ix:break
        mids={i:(lo[i]+hi[i])//2 for i in ix}; mh=headers(PROVIDERS[0],list(mids.values()))
        if len(mh)<len(set(mids.values())): raise DError("mapping header missing")
        for i,m in mids.items():
            if mh[m]["ts"]>=targets[i]:hi[i]=m
            else:lo[i]=m
    if hi[0]!=START_BLOCK or hi[-1]!=END_BLOCK: raise DError("edge map drift")
    return hi

def verify_headers(blocks,targets):
    req=[]
    for b in blocks:req.extend([b-1,b])
    pp=[headers(ep,req) for ep in PROVIDERS]; out=[]
    for b,t in zip(blocks,targets):
        v=defaultdict(int); pv=defaultdict(int)
        for d in pp:
            if b in d:v[(d[b]["hash"],d[b]["ts"],d[b]["bf"])]+=1
            if b-1 in d:pv[(d[b-1]["hash"],d[b-1]["ts"])]+=1
        g=[x for x,c in v.items() if c>=2]; gp=[x for x,c in pv.items() if c>=2]
        if len(g)!=1 or len(gp)!=1:raise DError(f"header quorum {b}")
        hh,ts,bf=g[0]; _,pts=gp[0]
        if ts<t or pts>=t:raise DError(f"first block invariant {b}")
        out.append({"block":b,"target":t,"ts":ts,"hash":hh,"bf":bf})
    return out

def snapshot_state(hh):
    calls=[]
    for h in hh:
        b=hex(h["block"]); calls += [("eth_call",[{"to":CURVE,"data":C_DY},b]),("eth_call",[{"to":QUEUE,"data":C_LAST},b]),("eth_call",[{"to":QUEUE,"data":C_UNF},b])]
    vals=quorum([batch(ep,calls) for ep in PROVIDERS],"snapshot-state"); out=[]
    for i,h in enumerate(hh): out.append({**h,"quote":vals[3*i],"last":vals[3*i+1],"unf":vals[3*i+2]})
    return out

def sqd(body):
    last=None
    for k in range(8):
        try:
            r=requests.post(SQD,json=body,stream=True,timeout=(20,180),headers={"Content-Type":"application/json","Accept-Encoding":"gzip","User-Agent":LAB_ID+"/sqd-v0.1"})
            STATS["sqd_http"]+=1
            if r.status_code in TRANSIENT:STATS["sqd_transient"]+=1;r.close();time.sleep(min(15,1.5*(2**k)));continue
            r.raise_for_status();return r
        except Exception as e:last=e;STATS["sqd_errors"]+=1
    raise DError(f"sqd {last}")

def words(data):
    h=data[2:] if isinstance(data,str) and data.startswith("0x") else ""
    if len(h)%64:raise DError("bad ABI data")
    return [int(h[i:i+64],16) for i in range(0,len(h),64)]

def events():
    cur=START_BLOCK; reb=[]; fin=[]; seen=set()
    filt=[{"address":[STETH],"topic0":[T_REBASE]},{"address":[QUEUE],"topic0":[T_FIN]}]
    while cur<=END_BLOCK:
        rt=min(END_BLOCK,cur+29999)
        body={"type":"evm","fromBlock":cur,"toBlock":rt,"fields":{"block":{"number":True,"timestamp":True},"log":{"topics":True,"data":True,"transactionHash":True,"logIndex":True}},"logs":filt}
        r=sqd(body); last=None
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw:continue
                o=json.loads(raw)
                if isinstance(o,dict) and o.get("error"):raise DError(str(o["error"]))
                h=o.get("header") or o.get("block") or {}; bn=int(h["number"]); ts=int(h["timestamp"])
                if not(cur<=bn<=rt<=END_BLOCK):raise DError("SQD boundary")
                if last is not None and bn<last:raise DError("SQD nonmonotonic")
                last=bn
                for l in o.get("logs") or []:
                    tx=str(l.get("transactionHash","")).lower(); li=l.get("logIndex"); li=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                    if (tx,li) in seen:raise DError("duplicate log")
                    seen.add((tx,li)); tt=[str(x).lower() for x in l.get("topics",[])]
                    if not tt:continue
                    if tt[0]==T_REBASE:
                        w=words(l.get("data",""))
                        if len(tt)<2 or len(w)!=6:raise DError("rebase ABI")
                        reb.append({"block":bn,"ts":ts,"li":li,"preS":w[1],"preE":w[2],"postS":w[3],"postE":w[4]})
                    elif tt[0]==T_FIN:
                        w=words(l.get("data",""))
                        if len(tt)<3 or len(w)!=3:raise DError("final ABI")
                        if w[2]!=ts:raise DError("final timestamp mismatch")
                        fin.append({"block":bn,"ts":ts,"li":li,"from":int(tt[1],16),"to":int(tt[2],16),"eth":w[0]})
        finally:r.close()
        cur=rt+1 if last is None else last+1
    reb.sort(key=lambda x:(x["block"],x["li"])); fin.sort(key=lambda x:(x["block"],x["li"]))
    if not reb or not fin:raise DError("missing canonical events")
    return reb,fin

def qcall(addr,data,b,label):
    calls=[("eth_call",[{"to":addr,"data":data},hex(b)])]
    return quorum([[batch(ep,calls)[0]] for ep in PROVIDERS],label)[0]

def cp_slot(i):return int.from_bytes(keccak(bytes.fromhex(u(i)+u(CP_POS))),"big")

def bind_checkpoints(fin):
    initial=qcall(QUEUE,C_CP,START_BLOCK-1,"cp-start"); ending=qcall(QUEUE,C_CP,END_BLOCK,"cp-end")
    if ending!=initial+len(fin):raise DError(f"checkpoint count {initial}+{len(fin)}!={ending}")
    calls=[]
    for j,f in enumerate(fin,1):
        z=cp_slot(initial+j); calls += [("eth_getStorageAt",[QUEUE,hex(z),hex(f["block"])]),("eth_getStorageAt",[QUEUE,hex(z+1),hex(f["block"])])]
    vals=quorum([batch(ep,calls) for ep in PROVIDERS],"cp-storage")
    for j,f in enumerate(fin,1):
        if vals[2*j-2]!=f["from"]:raise DError(f"checkpoint from mismatch {j}")
        if vals[2*j-1]<=0:raise DError("zero maxShareRate")
        f["cp"]=initial+j; f["msr"]=vals[2*j-1]

def apr7(ts,reb):
    x=[r for r in reb if ts-7*86400<r["ts"]<=ts]
    if not x:return None
    g=Decimal(1)
    for r in x:
        if min(r["preS"],r["preE"],r["postS"])<=0:raise DError("bad rebase denominator")
        g*= (Decimal(r["postE"])/Decimal(r["postS"]))/(Decimal(r["preE"])/Decimal(r["preS"]))
    return (g-1)*Decimal(365)/Decimal(7)

def throughput(ts,fin):return sum(f["eth"] for f in fin if ts-14*86400<f["ts"]<=ts)

def qheader(b):
    pp=[headers(ep,[b]) for ep in PROVIDERS]; v=defaultdict(int)
    for d in pp:
        if b in d:v[(d[b]["hash"],d[b]["ts"],d[b]["bf"])]+=1
    g=[x for x,c in v.items() if c>=2]
    if len(g)!=1 or b>END_BLOCK:raise DError("submission header quorum/boundary")
    h,ts,bf=g[0];return {"block":b,"ts":ts,"hash":h,"bf":bf}

def shares(b,amt,label):return qcall(STETH,S_SHARES+u(amt),b,label)

def final_for(pid,subts,fin):
    for f in fin:
        if f["ts"]>=subts and f["to"]>=pid:return f
    return None

def claim(amt,sh,msr):
    if sh<=0:raise DError("zero shares")
    return sh*msr//E27 if amt*E27//sh>msr else amt

def bootstrap(vals):
    n=len(vals); L=max(2,round(math.sqrt(n))); p=1/L; rng=random.Random(20260918); means=[]
    for _ in range(10000):
        idx=rng.randrange(n); a=[]
        for j in range(n):
            if j and rng.random()<p:idx=rng.randrange(n)
            a.append(vals[idx]);idx=(idx+1)%n
        means.append(statistics.fmean(a))
    means.sort(); return means[max(0,math.ceil(.05*len(means))-1)],L

def csvout(p,rows,fields):
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:r.get(k) for k in fields})

def main():
    source_sha=load_source()
    targets=[START_TS+86400*i for i in range(N_SNAP)]
    if targets[-1]!=END_TS:raise DError("snapshot clock")
    blocks=map_blocks(targets); snap=snapshot_state(verify_headers(blocks,targets)); reb,fin=events(); bind_checkpoints(fin)
    boundary=snap[-1]["ts"]; nextfree=START_TS-1; terminal=False; positions=[]; completed=[]; rows=[]; opfail=0
    for s in snap:
        ts=s["ts"]; rr={"target_utc":datetime.fromtimestamp(s["target"],timezone.utc).isoformat(),"block":s["block"],"block_ts":ts}
        if terminal:rr["status"]="OVERLAP_SKIPPED_PROTECTED_CENSOR";rows.append(rr);continue
        if ts<nextfree:rr["status"]="OVERLAP_SKIPPED";rows.append(rr);continue
        ap=apr7(ts,reb); th=throughput(ts,fin)
        if ap is None:rr["status"]="NO_SIGNAL_APR_UNAVAILABLE";rows.append(rr);continue
        if th<=0:rr["status"]="NO_SIGNAL_ZERO_THROUGHPUT";rows.append(rr);continue
        qd=max(Decimal(".25"),Decimal(s["unf"])/(Decimal(th)/14)); rr.update(apr_7d=str(ap),queue_days_est=str(qd))
        if qd>14:rr["status"]="NO_SIGNAL_QUEUE_GT_14D";rows.append(rr);continue
        acq=s["quote"]*9998//10000; gas=800000*s["bf"]*5//4
        reward=Decimal(acq)*ap*qd/Decimal(365); edge=Decimal(acq-NOTIONAL-gas-BASE_RESERVE)-reward; rr["estimated_edge_eth"]=str(edge/Decimal(10**18))
        if edge<=0:rr["status"]="NO_SIGNAL_EDGE_LE_0";rows.append(rr);continue
        rr["status"]="SIGNAL";rows.append(rr); pid=s["last"]+1; sb=s["block"]+1
        base={"entry_block":s["block"],"entry_ts":ts,"position_id":pid,"apr_7d":str(ap),"queue_days_est":str(qd),"estimated_edge_wei":str(edge)}
        if sb>END_BLOCK:
            positions.append({**base,"status":"PROTECTED_PERIOD_CENSORED","reason":"submission beyond boundary"});terminal=True;continue
        sh=qheader(sb); stress=s["quote"]*9995//10000; shb=shares(sb,acq,"shares-base"); shs=shares(sb,stress,"shares-stress")
        base.update(submission_block=sb,submission_ts=sh["ts"],curve_quote_wei=s["quote"],acquired_base_wei=acq,acquired_stress_wei=stress,shares_base=shb,shares_stress=shs,gas_base_wei=gas)
        ff=final_for(pid,sh["ts"],fin); horizon=sh["ts"]+MAX_HOLD
        if ff is None or ff["ts"]>horizon:
            if boundary>=horizon:positions.append({**base,"status":"OPERATIONAL_HORIZON_FAILURE","horizon_end_ts":horizon});opfail+=1;nextfree=horizon
            else:positions.append({**base,"status":"PROTECTED_PERIOD_CENSORED","horizon_end_ts":horizon});terminal=True
            continue
        hold=Decimal(ff["ts"]-sh["ts"])/86400; cb=claim(acq,shb,ff["msr"]); cs=claim(stress,shs,ff["msr"])
        rc=Decimal(acq)*ap*hold/365; rcs=Decimal(stress)*ap*hold/365
        nb=Decimal(cb-NOTIONAL-gas-BASE_RESERVE)-rc; ns=Decimal(cs-NOTIONAL-STRESS_RESERVE)-Decimal(gas)*Decimal("1.5")-rcs
        p={**base,"status":"COMPLETED","final_block":ff["block"],"final_ts":ff["ts"],"checkpoint_index":ff["cp"],"max_share_rate":ff["msr"],"holding_days":str(hold),"claim_base_wei":cb,"claim_stress_wei":cs,"net_base_eth":str(nb/Decimal(10**18)),"net_stress_eth":str(ns/Decimal(10**18)),"year":datetime.fromtimestamp(ts,timezone.utc).year}
        positions.append(p);completed.append(p);nextfree=ff["ts"]
    cens=sum(p["status"]=="PROTECTED_PERIOD_CENSORED" for p in positions); gates={}
    if cens:classification="DISCOVERY_PROTECTED_PERIOD_BLOCKED"
    elif len(completed)<30:classification="DISCOVERY_INSUFFICIENT_SAMPLE"
    else:
        b=[float(Decimal(p["net_base_eth"])) for p in completed]; st=[float(Decimal(p["net_stress_eth"])) for p in completed]
        mean=statistics.fmean(b); med=statistics.median(b); pr=sum(x>0 for x in b)/len(b); lcb,L=bootstrap(b)
        yy=defaultdict(list)
        for p,x in zip(completed,b):yy[p["year"]].append(x)
        cal=all(len(yy[y])>=10 and statistics.fmean(yy[y])>=0 for y in (2023,2024))
        pos=[x for x in b if x>0]; share=max(pos)/sum(pos) if pos else 1.; sm=statistics.fmean(st)
        gates={"n_completed":len(b),"n_ge_30":len(b)>=30,"mean_base_eth":mean,"mean_gt_0":mean>0,"median_base_eth":med,"median_gt_0":med>0,"positive_rate":pr,"positive_rate_ge_0_70":pr>=.70,"bootstrap_lcb_95_eth":lcb,"bootstrap_lcb_gt_0":lcb>0,"bootstrap_block_length":L,"year_2023_n":len(yy[2023]),"year_2023_mean":statistics.fmean(yy[2023]) if yy[2023] else None,"year_2024_n":len(yy[2024]),"year_2024_mean":statistics.fmean(yy[2024]) if yy[2024] else None,"calendar_gate":cal,"largest_positive_contribution_share":share,"largest_positive_le_0_30":share<=.30,"stress_mean_eth":sm,"stress_mean_gt_0":sm>0,"operational_horizon_failures":opfail,"zero_operational_failures":opfail==0,"provenance_clean":True}
        ok=all([gates["n_ge_30"],gates["mean_gt_0"],gates["median_gt_0"],gates["positive_rate_ge_0_70"],gates["bootstrap_lcb_gt_0"],gates["calendar_gate"],gates["largest_positive_le_0_30"],gates["stress_mean_gt_0"],gates["zero_operational_failures"],gates["provenance_clean"]])
        classification="DISCOVERY_REDEMPTION_EDGE_PASS_REQUIRES_SEPARATE_REPLICATION" if ok else "DISCOVERY_NO_REDEMPTION_EDGE"
    auth={}
    for f in ["STETH_REDEMPTION_BASIS_002_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md","STETH_REDEMPTION_BASIS_002_DISCOVERY_IMPLEMENTATION_SEMANTICS_FREEZE_V0_1.md","STETH_REDEMPTION_BASIS_002_DISCOVERY_IMPLEMENTATION_BOUNDARY_AMENDMENT_V0_1A.md","STETH_REDEMPTION_BASIS_002_CHECKPOINT_PROVENANCE_AMENDMENT_V0_1B.md"]:
        p=Path("research/steth_redemption_basis_002")/f;auth[f]=hashlib.sha256(p.read_bytes()).hexdigest()
    receipt={"lab_id":LAB_ID,"phase":"DISCOVERY_V0_1","classification":classification,"source_binding":{"run":35386033845,"artifact":10563803871,"artifact_zip_digest":"sha256:d1c371d5dda3718bb044f9a6b2cd628d8c35cd55af8ba85040375ee903110f53","receipt_json_sha256":source_sha},"authority_sha256":auth,"snapshot_population":len(snap),"all_signaled_positions":len(positions),"completed_positions":len(completed),"operational_horizon_failures":opfail,"protected_period_censored":cens,"token_rebased_events":len(reb),"withdrawals_finalized_events":len(fin),"gates":gates,"transport_stats":dict(STATS),"safety":{"accessed_after_frozen_end_block":False,"accessed_2025_or_2026":False,"live_trading":False,"wallet_access":False,"exchange_mutation":False,"main_merge":False},"git_sha":os.environ.get("GITHUB_SHA")}
    (OUT/"STETH_REDEMPTION_BASIS_002_DISCOVERY_V0_1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    (OUT/"STETH_REDEMPTION_BASIS_002_DISCOVERY_POSITIONS_V0_1.json").write_text(json.dumps(positions,indent=2,sort_keys=True)+"\n")
    csvout(OUT/"STETH_REDEMPTION_BASIS_002_DISCOVERY_POSITIONS_V0_1.csv",positions,["status","entry_block","entry_ts","submission_block","submission_ts","position_id","final_block","final_ts","holding_days","apr_7d","queue_days_est","estimated_edge_wei","net_base_eth","net_stress_eth"])
    csvout(OUT/"STETH_REDEMPTION_BASIS_002_DISCOVERY_SNAPSHOTS_V0_1.csv",rows,["target_utc","block","block_ts","status","apr_7d","queue_days_est","estimated_edge_eth"])
    print(json.dumps({"classification":classification,"snapshots":len(snap),"signals":len(positions),"completed":len(completed),"op_failures":opfail,"censored":cens,"gates":gates,"live_trading":False,"accessed_2025_or_2026":False},sort_keys=True))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        fail={"lab_id":LAB_ID,"phase":"DISCOVERY_V0_1","classification":"DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE","error":f"{type(e).__name__}: {str(e)[:2000]}","transport_stats":dict(STATS),"safety":{"accessed_2025_or_2026":False,"live_trading":False,"wallet_access":False,"exchange_mutation":False,"main_merge":False},"git_sha":os.environ.get("GITHUB_SHA")}
        (OUT/"STETH_REDEMPTION_BASIS_002_DISCOVERY_V0_1.json").write_text(json.dumps(fail,indent=2,sort_keys=True)+"\n");print(json.dumps(fail,sort_keys=True));raise SystemExit(2)
