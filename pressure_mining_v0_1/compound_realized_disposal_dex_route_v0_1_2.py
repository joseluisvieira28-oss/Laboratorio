#!/usr/bin/env python3
import hashlib, json, os, time
from collections import Counter, defaultdict
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from eth_hash.auto import keccak

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts"); os.makedirs(OUTDIR,exist_ok=True)
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
B0=16_308_190; B1=21_525_890; EXPECTED=999; N=64
BUY="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BASE="https://eth.blockscout.com"
SIGS=[
"Swap(address,uint256,uint256,uint256,uint256,address)",
"Swap(address,address,int256,int256,uint160,uint128,int24)",
"Swap(bytes32,address,address,uint256,uint256)",
"TokenExchange(address,int128,uint256,int128,uint256)",
"TokenExchangeUnderlying(address,int128,uint256,int128,uint256)",
"TokenExchange(address,uint256,uint256,uint256,uint256)",
"TokenExchangeUnderlying(address,uint256,uint256,uint256,uint256)",
]
TOPICS={"0x"+keccak(x.encode()).hex():x for x in SIGS}

def sh(b): return hashlib.sha256(b).hexdigest()
def iv(v):
    if isinstance(v,int): return v
    s=str(v or "0"); return int(s,16) if s.startswith("0x") else int(s)
def ad(v):
    if isinstance(v,dict): v=v.get("hash") or v.get("address") or v.get("value")
    s=str(v or "").lower(); return "0x"+s[-40:] if len(s)>=40 else None
def tv(v):
    if isinstance(v,dict): return str(v.get("value") or v.get("hex") or v.get("data") or "").lower()
    return str(v or "").lower()
def wd(d):
    if isinstance(d,dict): d=d.get("data") or d.get("value") or d.get("raw") or ""
    s=str(d or ""); s=s[2:] if s.startswith("0x") else s
    if len(s)%64: raise ValueError("bad data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def fetch(url,timeout=90):
    req=Request(url,headers={"User-Agent":"CryptoLab-CompoundDexRoute-V0.1.2","Accept":"application/json"})
    with urlopen(req,timeout=timeout) as r: raw=r.read()
    return json.loads(raw.decode()),sh(raw)
def corpus():
    out=[]; seen=set(); cur=B0; pages=[]
    while cur<=B1:
        stop=min(B1,cur+1_999_999)
        u=(f"{BASE}/api/?module=logs&action=getLogs&fromBlock={cur}&toBlock={stop}&address={COMET}&topic0={BUY}")
        time.sleep(1.1); o,h=fetch(u); rows=o.get("result") if isinstance(o,dict) else None
        if not isinstance(rows,list) or len(rows)>=1000: raise RuntimeError("bad/truncated corpus page")
        pages.append({"from":cur,"to":stop,"count":len(rows),"sha256":h})
        for x in rows:
            k=(str(x.get("blockNumber","")),str(x.get("transactionHash","")).lower(),str(x.get("logIndex","")))
            if k not in seen: seen.add(k); out.append(x)
        cur=stop+1
    return out,pages
def buyrow(x):
    t=x.get("topics") or []; w=wd(x.get("data"))
    return {"block":iv(x["blockNumber"]),"txi":iv(x["transactionIndex"]),"logi":iv(x["logIndex"]),
            "tx":str(x["transactionHash"]).lower(),"buyer":ad(t[1]),"asset":ad(t[2]),"coll":w[1]}
def logi(x):
    for k in ("index","log_index","logIndex"):
        if x.get(k) is not None:
            try:return iv(x[k])
            except: pass
    return None
def tr(x):
    t=x.get("topics") or []
    if len(t)<3 or tv(t[0])!=TRANSFER:return None
    w=wd(x.get("data")); li=logi(x)
    if not w or li is None:return None
    return {"token":ad(x.get("address") or x.get("address_hash") or x.get("contract_address")),
            "from":ad(tv(t[1])),"to":ad(tv(t[2])),"amount":w[0],"logi":li}
def getlogs(txh):
    items=[]; params={}; hashes=[]
    for _ in range(25):
        q="?"+urlencode(params) if params else ""
        o,h=fetch(f"{BASE}/api/v2/transactions/{txh}/logs{q}"); hashes.append(h)
        if isinstance(o,list): xs=o; nxt=None
        else: xs=o.get("items") if isinstance(o,dict) else None; nxt=o.get("next_page_params") if isinstance(o,dict) else None
        if not isinstance(xs,list): raise RuntimeError("invalid tx logs")
        items+=xs
        if not nxt:break
        params=nxt
    return items,hashes

receipt={"program":"COMPOUND_REALIZED_DISPOSAL_FLOW_DEX_ROUTE_CLASSIFICATION_V0.1.2",
"lab_id":"COMPOUND-REALIZED-DISPOSAL-FLOW-001",
"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
"recognized_topics":TOPICS,
"firewall":{"source_only":True,"market_prices_opened":False,"swap_prices_computed":False,
"swap_amounts_used_for_economics":False,"returns_computed":False,"pnl_computed":False,
"protected_2025_market_outcomes_opened":False,"direction_selected":False,"holding_period_selected":False,
"live_trading":False,"orders":False,"capital":False,"main_merge":False}}

try:
    raw,pages=corpus(); bs=[buyrow(x) for x in raw]; bs.sort(key=lambda x:(x["block"],x["txi"],x["logi"]))
    m=defaultdict(list)
    for x in bs:m[x["tx"]].append(x)
    uniq=sorted(m); selected=sorted(uniq,key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:min(N,len(uniq))]
    inferred=onward=recognized=recognized_onward=0; signature_counts=Counter(); records=[]; errors=[]
    for txh in selected:
        try:
            time.sleep(0.35); ls,hashes=getlogs(txh)
            transfers=[z for z in (tr(x) for x in ls) if z]
            txrec=[]
            for b in m[txh]:
                cs=[t for t in transfers if t["token"]==b["asset"] and t["from"]==COMET and t["amount"]==b["coll"] and t["logi"]<b["logi"]]
                cs.sort(key=lambda x:x["logi"],reverse=True); hit=cs[0] if cs else None; rec=hit["to"] if hit else None
                later_transfers=[]
                if rec:
                    inferred+=1
                    later_transfers=[t for t in transfers if t["token"]==b["asset"] and t["from"]==rec and t["logi"]>b["logi"] and t["amount"]>0]
                    if later_transfers:onward+=1
                swaps=[]
                for lg in ls:
                    li=logi(lg); topics=lg.get("topics") or []
                    if li is None or li<=b["logi"] or not topics: continue
                    t0=tv(topics[0])
                    if t0 in TOPICS:
                        swaps.append({"log_index":li,"address":ad(lg.get("address") or lg.get("address_hash") or lg.get("contract_address")),
                                      "signature":TOPICS[t0],"topic0":t0})
                if swaps:
                    recognized+=1
                    if later_transfers:
                        recognized_onward+=1
                    for z in {x["signature"] for x in swaps}: signature_counts[z]+=1
                txrec.append({"buy_log_index":b["logi"],"asset":b["asset"],"recipient":rec,
                              "same_tx_onward_transfer":bool(later_transfers),"recognized_dex_swap_after_buy":bool(swaps),
                              "recognized_swap_logs":swaps})
            records.append({"tx":txh,"buy_events":txrec,"log_page_sha256":hashes})
        except Exception as e: errors.append({"tx":txh,"error":repr(e)})
    events=sum(len(m[x]) for x in selected)
    onward_share=(recognized_onward/onward) if onward else 0.0
    if onward and onward_share>=0.60: route_status="DEX_ROUTE_EVIDENCE_STRONG"
    elif recognized_onward>0: route_status="DEX_ROUTE_EVIDENCE_PRESENT"
    else: route_status="DEX_ROUTE_EVIDENCE_NOT_DEMONSTRATED"
    receipt.update({"status":route_status,"corpus_canary":{"buy_logs":len(bs),"expected":EXPECTED,"unique_transactions":len(uniq)},
      "sample":{"selected_transactions":len(selected),"buy_events":events,"recipient_inferred_events":inferred,
                "same_tx_onward_transfer_events":onward,"recognized_dex_swap_events":recognized,
                "recognized_dex_swap_on_onward_events":recognized_onward,
                "recognized_dex_swap_share_of_inferred_pct":round(100*recognized/inferred,4) if inferred else None,
                "recognized_dex_swap_share_of_onward_pct":round(100*recognized_onward/onward,4) if onward else None,
                "recognized_signature_event_counts":dict(signature_counts),"records":records,"errors":errors},
      "interpretation":{"edge_claim":False,"direction_claim":False,"tradability_claim":False,
                        "recognized_swap_means_exchange_interaction_not_guaranteed_net_sell":True}})
except Exception as e:
    receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e),
                    "interpretation":{"edge_claim":False,"direction_claim":False,"tradability_claim":False}})
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode(); receipt["receipt_sha256_pre_self_field"]=sh(pre)
out=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_DEX_ROUTE_RECEIPT_V0.1.2.json")
with open(out,"w") as f: json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2)); print("receipt="+out)
