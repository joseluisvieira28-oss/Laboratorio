#!/usr/bin/env python3
import bisect, hashlib, json, os, time
from collections import defaultdict, Counter
from urllib.request import Request, urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

COMET="0xc3d688B66703497DAA19211EEdff47f25384cdc3"
B0=16_308_190
B1=21_525_890
ABSORB_TOPIC="0x9850ab1af75177e4a9201c65a2cf7976d5d28e40ef63494b44366f86b2f9412e"
BUY_TOPIC="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
ANCHOR_TX="0x437110f3f87836279e9262d6b76f71ed946b3d5e39ad8dd04dbe6aebc43dfd2e"

def fetch_json(url, timeout=120):
    req=Request(url,headers={"User-Agent":"CryptoLab-CompoundTiming-V0.1","Accept":"application/json"})
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return json.loads(b.decode()), hashlib.sha256(b).hexdigest()

def iv(v):
    if isinstance(v,int): return v
    s=str(v)
    return int(s,16) if s.startswith("0x") else int(s)

def get_logs(topic0):
    out=[]
    seen=set()
    cur=B0
    chunk=2_000_000
    page_hashes=[]
    while cur<=B1:
        stop=min(B1,cur+chunk-1)
        url=("https://eth.blockscout.com/api/?module=logs&action=getLogs"
             f"&fromBlock={cur}&toBlock={stop}&address={COMET}&topic0={topic0}")
        time.sleep(1.1)
        obj,sha=fetch_json(url)
        page_hashes.append({"from":cur,"to":stop,"sha256":sha})
        rows=obj.get("result") if isinstance(obj,dict) else None
        if not isinstance(rows,list):
            raise RuntimeError(f"invalid Blockscout logs response {cur}-{stop}: {obj!r}")
        if len(rows)>=1000:
            raise RuntimeError(f"possible Blockscout truncation {cur}-{stop}: {len(rows)}")
        for x in rows:
            key=(str(x.get("blockNumber","")).lower(),
                 str(x.get("transactionHash","")).lower(),
                 str(x.get("logIndex","")).lower())
            if key not in seen:
                seen.add(key); out.append(x)
        cur=stop+1
    return out,page_hashes

def asset_from_absorb(lg):
    t=lg.get("topics") or []
    return ("0x"+str(t[3])[-40:]).lower() if len(t)>3 else None

def asset_from_buy(lg):
    t=lg.get("topics") or []
    return ("0x"+str(t[2])[-40:]).lower() if len(t)>2 else None

def pos(lg):
    return (iv(lg.get("blockNumber",0)),
            iv(lg.get("transactionIndex",0)),
            iv(lg.get("logIndex",0)))

absorb,absorb_pages=get_logs(ABSORB_TOPIC)
buy,buy_pages=get_logs(BUY_TOPIC)
absorb.sort(key=pos); buy.sort(key=pos)

if ANCHOR_TX.lower() not in {str(x.get("transactionHash","")).lower() for x in absorb}:
    raise RuntimeError("known historical AbsorbCollateral anchor not recovered")

buys_by_asset=defaultdict(list)
for x in buy:
    a=asset_from_buy(x)
    if a: buys_by_asset[a].append(x)

buy_positions={}
for a,rows in buys_by_asset.items():
    buy_positions[a]=[pos(x) for x in rows]

records=[]
by_asset=defaultdict(lambda: Counter())
delay_values=[]
for x in absorb:
    a=asset_from_absorb(x)
    if not a: continue
    p=pos(x)
    rows=buys_by_asset.get(a,[])
    poss=buy_positions.get(a,[])
    i=bisect.bisect_right(poss,p)
    # If a BuyCollateral occurs later in the same tx, bisect_right on full log position will find it.
    # Search from the first buy with position strictly after the absorb log.
    if i < len(rows):
        y=rows[i]
        q=pos(y)
        delay=q[0]-p[0]
        same_tx=(str(y.get("transactionHash","")).lower()==str(x.get("transactionHash","")).lower())
        same_block=(q[0]==p[0])
        delay_values.append(delay)
        r={
          "asset":a,
          "absorb_block":p[0],
          "absorb_tx":str(x.get("transactionHash","")).lower(),
          "first_subsequent_buy_block":q[0],
          "first_subsequent_buy_tx":str(y.get("transactionHash","")).lower(),
          "delay_blocks":delay,
          "same_block":same_block,
          "same_tx":same_tx,
        }
        records.append(r)
        c=by_asset[a]
        c["absorbs_with_future_buy"]+=1
        if same_tx: c["same_tx"]+=1
        if same_block: c["same_block"]+=1
        if delay<=1: c["within_1_block"]+=1
        if delay<=5: c["within_5_blocks"]+=1
        if delay<=20: c["within_20_blocks"]+=1
        if delay<=100: c["within_100_blocks"]+=1
    else:
        records.append({
          "asset":a,"absorb_block":p[0],
          "absorb_tx":str(x.get("transactionHash","")).lower(),
          "first_subsequent_buy_block":None,"first_subsequent_buy_tx":None,
          "delay_blocks":None,"same_block":False,"same_tx":False,
        })
        by_asset[a]["no_future_buy"]+=1

def pct(n,d):
    return round(100*n/d,4) if d else None

matched=[r for r in records if r["delay_blocks"] is not None]
same_tx_n=sum(r["same_tx"] for r in matched)
same_block_n=sum(r["same_block"] for r in matched)
within1=sum(r["delay_blocks"]<=1 for r in matched)
within5=sum(r["delay_blocks"]<=5 for r in matched)
within20=sum(r["delay_blocks"]<=20 for r in matched)
within100=sum(r["delay_blocks"]<=100 for r in matched)
no_future=len(records)-len(matched)
sd=sorted(delay_values)
def q(frac):
    if not sd: return None
    idx=min(len(sd)-1,max(0,int(round(frac*(len(sd)-1)))))
    return sd[idx]

# Independent transaction-level overlap diagnostic.
absorb_tx_asset={(str(x.get("transactionHash","")).lower(),asset_from_absorb(x)) for x in absorb}
buy_tx_asset={(str(x.get("transactionHash","")).lower(),asset_from_buy(x)) for x in buy}
same_tx_pairs=absorb_tx_asset & buy_tx_asset

receipt={
 "program":"COMPOUND_INVENTORY_TIMING_SOURCE_DIAGNOSTIC_V0.1",
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "lab_id":"COMPOUND-INVENTORY-LIQUIDATION-001",
 "window_blocks":[B0,B1],
 "comet_address":COMET,
 "source":"BLOCKSCOUT_INDEXED_LOGS",
 "source_page_hashes":{"absorb":absorb_pages,"buy":buy_pages},
 "anchor_tx":ANCHOR_TX,
 "counts":{
   "absorb_logs":len(absorb),
   "buy_logs":len(buy),
   "assets_absorb":len({asset_from_absorb(x) for x in absorb if asset_from_absorb(x)}),
   "assets_buy":len({asset_from_buy(x) for x in buy if asset_from_buy(x)}),
   "absorbs_with_subsequent_same_asset_buy":len(matched),
   "absorbs_without_later_same_asset_buy_in_window":no_future,
   "absorb_tx_asset_pairs":len(absorb_tx_asset),
   "same_tx_absorb_buy_asset_pairs":len(same_tx_pairs),
 },
 "timing":{
   "same_tx_count":same_tx_n,
   "same_tx_pct_of_matched":pct(same_tx_n,len(matched)),
   "same_block_count":same_block_n,
   "same_block_pct_of_matched":pct(same_block_n,len(matched)),
   "within_1_block_pct":pct(within1,len(matched)),
   "within_5_blocks_pct":pct(within5,len(matched)),
   "within_20_blocks_pct":pct(within20,len(matched)),
   "within_100_blocks_pct":pct(within100,len(matched)),
   "delay_blocks_median":q(0.5),
   "delay_blocks_p90":q(0.9),
   "delay_blocks_p99":q(0.99),
   "delay_blocks_max":max(sd) if sd else None,
 },
 "by_asset":{a:dict(c) for a,c in sorted(by_asset.items())},
 "sample_records":records[:25],
 "interpretation_rule":{
   "source_only":True,
   "no_price_or_return_opened":True,
   "purpose":"Determine whether seized-collateral inventory generally exists before disposal long enough to define a causal predictor state.",
   "no_edge_verdict_allowed":True
 },
 "firewall":{
   "market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
   "protected_2025_opened":False,"live_trading":False,"orders":False,
   "exchange_mutation":False,"capital":False,"paid_data":False
 }
}
raw=json.dumps(receipt,sort_keys=True,indent=2).encode()
receipt["receipt_sha256_pre_self_field"]=hashlib.sha256(raw).hexdigest()
out=os.path.join(OUTDIR,"COMPOUND_INVENTORY_TIMING_SOURCE_DIAGNOSTIC_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
print(f"receipt={out}")
