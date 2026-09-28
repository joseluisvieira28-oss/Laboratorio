#!/usr/bin/env python3
import hashlib, json, os, time
from collections import defaultdict
from urllib.request import Request, urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)
COMET="0xc3d688B66703497DAA19211EEdff47f25384cdc3"
B0=16_308_190
B1=21_525_890
ABSORB_TOPIC="0x9850ab1af75177e4a9201c65a2cf7976d5d28e40ef63494b44366f86b2f9412e"
BUY_TOPIC="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"

def fetch_json(url,timeout=120):
    req=Request(url,headers={"User-Agent":"CryptoLab-CompoundLedger-V0.1","Accept":"application/json"})
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return json.loads(b.decode()),hashlib.sha256(b).hexdigest()

def iv(v):
    if isinstance(v,int): return v
    s=str(v); return int(s,16) if s.startswith("0x") else int(s)

def words(data):
    s=str(data or "")
    if s.startswith("0x"): s=s[2:]
    if len(s)%64: raise ValueError("malformed event data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]

def get_logs(topic0):
    out=[]; seen=set(); cur=B0; chunk=2_000_000; pages=[]
    while cur<=B1:
        stop=min(B1,cur+chunk-1)
        url=("https://eth.blockscout.com/api/?module=logs&action=getLogs"
             f"&fromBlock={cur}&toBlock={stop}&address={COMET}&topic0={topic0}")
        time.sleep(1.1)
        obj,sha=fetch_json(url)
        rows=obj.get("result") if isinstance(obj,dict) else None
        if not isinstance(rows,list): raise RuntimeError(f"invalid logs response: {obj!r}")
        if len(rows)>=1000: raise RuntimeError(f"possible truncation {cur}-{stop}: {len(rows)}")
        pages.append({"from":cur,"to":stop,"count":len(rows),"sha256":sha})
        for x in rows:
            k=(str(x.get("blockNumber","")).lower(),str(x.get("transactionHash","")).lower(),str(x.get("logIndex","")).lower())
            if k not in seen: seen.add(k); out.append(x)
        cur=stop+1
    return out,pages

def asset_absorb(x):
    t=x.get("topics") or []
    return ("0x"+str(t[3])[-40:]).lower() if len(t)>3 else None

def asset_buy(x):
    t=x.get("topics") or []
    return ("0x"+str(t[2])[-40:]).lower() if len(t)>2 else None

def p(x):
    return (iv(x.get("blockNumber",0)),iv(x.get("transactionIndex",0)),iv(x.get("logIndex",0)))

absorbs,apages=get_logs(ABSORB_TOPIC)
buys,bpages=get_logs(BUY_TOPIC)
events=[]
for x in absorbs:
    w=words(x.get("data"))
    if len(w)<2: raise RuntimeError("AbsorbCollateral data words missing")
    events.append({
      "kind":"ABSORB","asset":asset_absorb(x),"block":p(x)[0],
      "txi":p(x)[1],"logi":p(x)[2],"tx":str(x.get("transactionHash","")).lower(),
      "collateral_raw":w[0],"usd_value_raw":w[1]
    })
for x in buys:
    w=words(x.get("data"))
    if len(w)<2: raise RuntimeError("BuyCollateral data words missing")
    events.append({
      "kind":"BUY","asset":asset_buy(x),"block":p(x)[0],
      "txi":p(x)[1],"logi":p(x)[2],"tx":str(x.get("transactionHash","")).lower(),
      "base_amount_raw":w[0],"collateral_raw":w[1]
    })
events.sort(key=lambda e:(e["block"],e["txi"],e["logi"]))

inv=defaultdict(int)
start=None
episodes=[]
underflows=defaultdict(lambda:{"events":0,"collateral_raw":0})
per_asset=defaultdict(lambda:{"absorbs":0,"buys":0,"episodes":0,"same_tx_clear":0,"same_block_clear":0,"persist_gt_1":0,"persist_gt_5":0,"persist_gt_20":0,"persist_gt_100":0,"open_at_end":0})

for e in events:
    a=e["asset"]
    if not a: continue
    s=per_asset[a]
    if e["kind"]=="ABSORB":
        s["absorbs"]+=1
        if inv[a]==0:
            start={"asset":a,"start_block":e["block"],"start_tx":e["tx"],"start_txi":e["txi"],"start_logi":e["logi"]}
        inv[a]+=e["collateral_raw"]
    else:
        s["buys"]+=1
        before=inv[a]
        consume=min(before,e["collateral_raw"])
        inv[a]-=consume
        if e["collateral_raw"]>before:
            underflows[a]["events"]+=1
            underflows[a]["collateral_raw"]+=e["collateral_raw"]-before
        if before>0 and inv[a]==0 and start and start["asset"]==a:
            ep=dict(start)
            ep.update({
              "end_block":e["block"],"end_tx":e["tx"],"end_txi":e["txi"],"end_logi":e["logi"],
              "duration_blocks":e["block"]-start["start_block"],
              "same_block":e["block"]==start["start_block"],
              "same_tx":e["tx"]==start["start_tx"],
            })
            episodes.append(ep)
            s["episodes"]+=1
            if ep["same_tx"]: s["same_tx_clear"]+=1
            if ep["same_block"]: s["same_block_clear"]+=1
            if ep["duration_blocks"]>1: s["persist_gt_1"]+=1
            if ep["duration_blocks"]>5: s["persist_gt_5"]+=1
            if ep["duration_blocks"]>20: s["persist_gt_20"]+=1
            if ep["duration_blocks"]>100: s["persist_gt_100"]+=1
            start=None

# Note: one global start variable is incorrect if assets overlap. Recompute episodes independently by asset.
episodes=[]
for a in sorted({e["asset"] for e in events if e["asset"]}):
    ai=0; ast=None
    # reset episode counters that depend on exact ledger
    for k in ("episodes","same_tx_clear","same_block_clear","persist_gt_1","persist_gt_5","persist_gt_20","persist_gt_100","open_at_end"):
        per_asset[a][k]=0
    for e in [z for z in events if z["asset"]==a]:
        if e["kind"]=="ABSORB":
            if ai==0:
                ast={"asset":a,"start_block":e["block"],"start_tx":e["tx"],"start_txi":e["txi"],"start_logi":e["logi"]}
            ai+=e["collateral_raw"]
        else:
            before=ai
            ai=max(0,ai-e["collateral_raw"])
            if before>0 and ai==0 and ast is not None:
                ep=dict(ast)
                ep.update({
                  "end_block":e["block"],"end_tx":e["tx"],"end_txi":e["txi"],"end_logi":e["logi"],
                  "duration_blocks":e["block"]-ast["start_block"],
                  "same_block":e["block"]==ast["start_block"],
                  "same_tx":e["tx"]==ast["start_tx"],
                })
                episodes.append(ep)
                s=per_asset[a]; s["episodes"]+=1
                if ep["same_tx"]: s["same_tx_clear"]+=1
                if ep["same_block"]: s["same_block_clear"]+=1
                if ep["duration_blocks"]>1: s["persist_gt_1"]+=1
                if ep["duration_blocks"]>5: s["persist_gt_5"]+=1
                if ep["duration_blocks"]>20: s["persist_gt_20"]+=1
                if ep["duration_blocks"]>100: s["persist_gt_100"]+=1
                ast=None
    if ai>0 and ast is not None:
        per_asset[a]["open_at_end"]=1
        ep=dict(ast)
        ep.update({"end_block":None,"end_tx":None,"duration_blocks":None,"same_block":False,"same_tx":False,"open_at_end":True})
        episodes.append(ep)

closed=[e for e in episodes if e.get("duration_blocks") is not None]
dur=sorted(e["duration_blocks"] for e in closed)
def q(frac):
    if not dur: return None
    idx=min(len(dur)-1,max(0,int(round(frac*(len(dur)-1)))))
    return dur[idx]
def pct(n,d): return round(100*n/d,4) if d else None

same_tx=sum(e["same_tx"] for e in closed)
same_block=sum(e["same_block"] for e in closed)
gt1=sum(e["duration_blocks"]>1 for e in closed)
gt5=sum(e["duration_blocks"]>5 for e in closed)
gt20=sum(e["duration_blocks"]>20 for e in closed)
gt100=sum(e["duration_blocks"]>100 for e in closed)
open_end=sum(1 for e in episodes if e.get("open_at_end"))

receipt={
 "program":"COMPOUND_INVENTORY_LEDGER_SOURCE_DIAGNOSTIC_V0.1",
 "lab_id":"COMPOUND-INVENTORY-LIQUIDATION-001",
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "window_blocks":[B0,B1],
 "source":"BLOCKSCOUT_INDEXED_LOGS",
 "source_pages":{"absorb":apages,"buy":bpages},
 "counts":{
   "absorb_logs":len(absorbs),"buy_logs":len(buys),
   "closed_known_inventory_episodes":len(closed),
   "open_known_inventory_episodes_at_window_end":open_end,
   "assets":len(per_asset),
   "buy_underflow_events_due_to_left_boundary_or_prior_unknown_inventory":sum(x["events"] for x in underflows.values()),
 },
 "episode_timing":{
   "same_tx_clear_count":same_tx,"same_tx_clear_pct":pct(same_tx,len(closed)),
   "same_block_clear_count":same_block,"same_block_clear_pct":pct(same_block,len(closed)),
   "persist_gt_1_block_count":gt1,"persist_gt_1_block_pct":pct(gt1,len(closed)),
   "persist_gt_5_blocks_count":gt5,"persist_gt_5_blocks_pct":pct(gt5,len(closed)),
   "persist_gt_20_blocks_count":gt20,"persist_gt_20_blocks_pct":pct(gt20,len(closed)),
   "persist_gt_100_blocks_count":gt100,"persist_gt_100_blocks_pct":pct(gt100,len(closed)),
   "duration_blocks_median":q(0.5),"duration_blocks_p90":q(0.9),"duration_blocks_p99":q(0.99),
   "duration_blocks_max":max(dur) if dur else None,
 },
 "by_asset":{a:v for a,v in sorted(per_asset.items())},
 "underflow_by_asset":{a:v for a,v in sorted(underflows.items()) if v["events"]},
 "episode_sample":closed[:30],
 "interpretation":{
   "ledger_is_lower_bound":True,
   "reason":"The window starts 2023-01-01; BuyCollateral can consume inventory created before the left boundary. Underflow events are not fabricated into inventory.",
   "purpose":"Measure whether directly observed absorbed collateral remains in known protocol inventory across later blocks before BuyCollateral clears it.",
   "market_outcome_claim":False,
   "no_edge_verdict_allowed":True,
 },
 "firewall":{
   "market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
   "protected_2025_opened":False,"live_trading":False,"orders":False,
   "exchange_mutation":False,"capital":False,"paid_data":False
 }
}
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=hashlib.sha256(pre).hexdigest()
out=os.path.join(OUTDIR,"COMPOUND_INVENTORY_LEDGER_SOURCE_DIAGNOSTIC_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2))
print(f"receipt={out}")
