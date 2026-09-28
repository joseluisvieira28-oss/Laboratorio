#!/usr/bin/env python3
import hashlib, json, os, time
from collections import Counter, defaultdict
from urllib.request import Request, urlopen
from urllib.error import HTTPError

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)
LAB_ID="COMPOUND-REALIZED-DISPOSAL-FLOW-001"
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
B0=16_308_190
B1=21_525_890
EXPECTED_BUY_LOGS=999
PROBE_N=64
BUY_TOPIC="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
TRANSFER_TOPIC="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
RPC_ENDPOINTS=[
  "https://ethereum-rpc.publicnode.com",
  "https://rpc.flashbots.net",
  "https://eth.llamarpc.com",
  "https://eth.drpc.org",
  "https://public.1rpc.io/eth",
  "https://eth.blockscout.com/api/eth-rpc",
]

def sha(b): return hashlib.sha256(b).hexdigest()
def iv(v):
    if isinstance(v,int): return v
    s=str(v or "0"); return int(s,16) if s.startswith("0x") else int(s)
def addr(v):
    s=str(v or "").lower()
    return "0x"+s[-40:] if len(s)>=40 else None
def words(data):
    s=str(data or "")
    if s.startswith("0x"): s=s[2:]
    if len(s)%64: raise ValueError("malformed event data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def pct(n,d): return round(100*n/d,4) if d else None

def fetch_json(url,method="GET",data=None,timeout=90):
    body=None if data is None else json.dumps(data).encode()
    headers={"User-Agent":"CryptoLab-CompoundRealizedFlow-V0.1.1","Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    req=Request(url,data=body,headers=headers,method=method)
    with urlopen(req,timeout=timeout) as r:
        raw=r.read()
    return json.loads(raw.decode()),sha(raw)

def rpc_one(endpoint,method,params):
    obj,h=fetch_json(endpoint,"POST",{"jsonrpc":"2.0","id":1,"method":method,"params":params})
    if not isinstance(obj,dict) or "error" in obj:
        raise RuntimeError(f"{method} rpc error: {obj!r}")
    result=obj.get("result")
    if result is None: raise RuntimeError(f"{method} returned null")
    return result,h

def rpc_pair(tx_hash):
    errors=[]
    for ep in RPC_ENDPOINTS:
        for attempt in range(2):
            try:
                if attempt: time.sleep(0.8*(attempt+1))
                tx,txh=rpc_one(ep,"eth_getTransactionByHash",[tx_hash])
                time.sleep(0.12)
                rcpt,rh=rpc_one(ep,"eth_getTransactionReceipt",[tx_hash])
                return tx,txh,rcpt,rh,ep,errors
            except Exception as e:
                errors.append({"endpoint":ep,"attempt":attempt+1,"error":repr(e)})
                time.sleep(0.25)
    raise RuntimeError(json.dumps(errors,sort_keys=True))

def get_buy_logs():
    out=[]; seen=set(); pages=[]; cur=B0
    while cur<=B1:
        stop=min(B1,cur+1_999_999)
        url=("https://eth.blockscout.com/api/?module=logs&action=getLogs"
             f"&fromBlock={cur}&toBlock={stop}&address={COMET}&topic0={BUY_TOPIC}")
        time.sleep(1.1)
        obj,h=fetch_json(url)
        rows=obj.get("result") if isinstance(obj,dict) else None
        if not isinstance(rows,list): raise RuntimeError(f"invalid logs response: {obj!r}")
        if len(rows)>=1000: raise RuntimeError(f"possible truncation {cur}-{stop}: {len(rows)}")
        pages.append({"from":cur,"to":stop,"count":len(rows),"sha256":h})
        for x in rows:
            k=(str(x.get("blockNumber","")).lower(),str(x.get("transactionHash","")).lower(),str(x.get("logIndex","")).lower())
            if k not in seen: seen.add(k); out.append(x)
        cur=stop+1
    return out,pages

def buyrow(x):
    t=x.get("topics") or []; w=words(x.get("data"))
    if len(t)<3 or len(w)<2: raise ValueError("BuyCollateral malformed")
    return {"block":iv(x.get("blockNumber")),"txi":iv(x.get("transactionIndex")),"logi":iv(x.get("logIndex")),
            "tx":str(x.get("transactionHash","")).lower(),"buyer":addr(t[1]),"asset":addr(t[2]),
            "base":w[0],"collateral":w[1]}

def transfer(x):
    t=x.get("topics") or []
    if len(t)<3 or str(t[0]).lower()!=TRANSFER_TOPIC: return None
    w=words(x.get("data"))
    if not w: return None
    return {"token":str(x.get("address","")).lower(),"from":addr(t[1]),"to":addr(t[2]),
            "amount":w[0],"logi":iv(x.get("logIndex"))}

receipt={
 "program":"COMPOUND_REALIZED_DISPOSAL_FLOW_SOURCE_V0.1.1",
 "lab_id":LAB_ID,
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "transport_retry_of":{"run_id":36346693857,"prior_status":"SOURCE_REALIZED_FLOW_PARTIAL","reason":"HTTP_429_RECEIPT_TRANSPORT"},
 "firewall":{"source_only":True,"market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
             "protected_2025_market_outcomes_opened":False,"live_trading":False,"orders":False,
             "exchange_mutation":False,"capital":False,"paid_data":False,"main_merge":False,
             "post_outcome_tuning":False},
}
try:
    raw,pages=get_buy_logs()
    buys=[buyrow(x) for x in raw]
    buys.sort(key=lambda x:(x["block"],x["txi"],x["logi"]))
    buyers=Counter(x["buyer"] for x in buys if x["buyer"])
    assets=Counter(x["asset"] for x in buys if x["asset"])
    txmap=defaultdict(list)
    for x in buys: txmap[x["tx"]].append(x)
    unique=sorted(txmap)
    selected=sorted(unique,key=lambda h:hashlib.sha256(h.encode()).hexdigest())[:min(PROBE_N,len(unique))]
    expected_events=sum(len(txmap[h]) for h in selected)

    usable=0; inferred=0; onward=0; buyer_sender=0; errors=[]; records=[]; endpoints=Counter()
    for h in selected:
        try:
            tx,txh,rc,rch,ep,attempt_errors=rpc_pair(h)
            usable+=1; endpoints[ep]+=1
            sender=str(tx.get("from","")).lower()
            ts=[z for z in (transfer(l) for l in (rc.get("logs") or [])) if z]
            evs=[]
            for b in txmap[h]:
                if b["buyer"]==sender: buyer_sender+=1
                candidates=[t for t in ts if t["token"]==b["asset"] and t["from"]==COMET and
                            t["amount"]==b["collateral"] and t["logi"]<b["logi"]]
                candidates.sort(key=lambda t:t["logi"],reverse=True)
                hit=candidates[0] if candidates else None
                recipient=hit["to"] if hit else None
                later=[]
                if recipient:
                    inferred+=1
                    later=[t for t in ts if t["token"]==b["asset"] and t["from"]==recipient and t["logi"]>b["logi"] and t["amount"]>0]
                    if later: onward+=1
                evs.append({"buy_log_index":b["logi"],"buyer":b["buyer"],"asset":b["asset"],
                            "base_amount_raw":str(b["base"]),"collateral_amount_raw":str(b["collateral"]),
                            "recipient_inferred":recipient,"recipient_transfer_log_index":hit["logi"] if hit else None,
                            "same_tx_onward_transfer":bool(later),"same_tx_onward_transfer_count":len(later),
                            "buyer_equals_tx_sender":b["buyer"]==sender})
            records.append({"tx":h,"block":iv(rc.get("blockNumber")),"tx_sender":sender,
                            "tx_to":str(tx.get("to","")).lower() if tx.get("to") else None,
                            "receipt_status":iv(rc.get("status","0x0")),"rpc_endpoint":ep,
                            "tx_rpc_sha256":txh,"receipt_rpc_sha256":rch,"buy_events":evs,
                            "fallback_errors_before_success":attempt_errors})
        except Exception as e:
            errors.append({"tx":h,"error":repr(e)})

    n=len(buys); sel=len(selected)
    use_rate=usable/sel if sel else 0
    inf_rate=inferred/expected_events if expected_events else 0
    if n!=EXPECTED_BUY_LOGS: status="SOURCE_CORPUS_DRIFT"
    elif len(buyers)<1 or len(assets)<1 or sel<1: status="SOURCE_REALIZED_FLOW_PARTIAL"
    elif use_rate<0.95 or inf_rate<0.90: status="SOURCE_REALIZED_FLOW_PARTIAL"
    else: status="SOURCE_REALIZED_FLOW_PASS"

    receipt.update({
      "status":status,
      "source":{"comet":COMET,"window_blocks":[B0,B1],"window_utc":["2023-01-01T00:00:00Z","2024-12-31T23:59:59Z"],
                "buy_topic":BUY_TOPIC,"transfer_topic":TRANSFER_TOPIC,"expected_parent_canary_buy_logs":EXPECTED_BUY_LOGS,
                "rpc_fallbacks":RPC_ENDPOINTS},
      "source_pages":pages,
      "corpus":{"buy_logs":n,"unique_transactions":len(unique),"unique_buyers":len(buyers),"unique_assets":len(assets),
                "buyer_concentration_top15":[{"buyer":a,"buy_logs":c,"share_pct":pct(c,n)} for a,c in buyers.most_common(15)],
                "by_asset":dict(sorted(assets.items()))},
      "deterministic_receipt_probe":{"selection_rule":"ascending SHA256(lowercase tx hash), first 64 unique BuyCollateral transactions",
                "selected_transactions":sel,"usable_transactions":usable,"usable_transactions_pct":pct(usable,sel),
                "probed_buy_events":expected_events,"recipient_inferred_events":inferred,"recipient_inferred_pct":pct(inferred,expected_events),
                "buyer_equals_tx_sender_events":buyer_sender,"buyer_equals_tx_sender_pct":pct(buyer_sender,expected_events),
                "same_tx_onward_transfer_events":onward,"same_tx_onward_transfer_pct":pct(onward,inferred),
                "endpoint_success_counts":dict(endpoints),"records":records,"errors":errors,
                "note":"Onward transfer is routing/flow diagnostic only; not automatically a DEX sale and has no source PASS threshold."},
      "gate":{"exact_999_parent_canary":n==EXPECTED_BUY_LOGS,"buyer_and_asset_population_present":len(buyers)>=1 and len(assets)>=1,
              "receipt_probe_sample_complete":sel==min(PROBE_N,len(unique)),"receipt_usable_ge_95pct":use_rate>=0.95,
              "recipient_inference_ge_90pct":inf_rate>=0.90,"onward_transfer_is_non_gate_diagnostic":True},
      "interpretation":{"edge_claim":False,"direction_claim":False,"holding_period_selected":False,
                        "economic_test_authorized":False,"protected_2025_market_test_authorized":False}
    })
except Exception as e:
    receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e),
                    "interpretation":{"edge_claim":False,"direction_claim":False,"holding_period_selected":False,
                                      "economic_test_authorized":False,"protected_2025_market_test_authorized":False}})

pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=sha(pre)
out=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_SOURCE_RECEIPT_V0.1.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2))
print(f"receipt={out}")
