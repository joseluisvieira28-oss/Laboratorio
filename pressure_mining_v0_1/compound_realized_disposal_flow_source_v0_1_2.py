#!/usr/bin/env python3
import hashlib, json, os, time
from collections import Counter, defaultdict
from urllib.request import Request, urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts"); os.makedirs(OUTDIR,exist_ok=True)
LAB_ID="COMPOUND-REALIZED-DISPOSAL-FLOW-001"
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
B0=16_308_190; B1=21_525_890; EXPECTED=999; N=64
BUY="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ENDPOINTS=["https://rpc.flashbots.net","https://ethereum-rpc.publicnode.com","https://eth.llamarpc.com","https://eth.drpc.org"]

def h(b): return hashlib.sha256(b).hexdigest()
def iv(v):
    if isinstance(v,int): return v
    s=str(v or "0"); return int(s,16) if s.startswith("0x") else int(s)
def ad(v):
    s=str(v or "").lower(); return "0x"+s[-40:] if len(s)>=40 else None
def wd(d):
    s=str(d or ""); s=s[2:] if s.startswith("0x") else s
    if len(s)%64: raise ValueError("bad data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def pct(a,b): return round(100*a/b,4) if b else None
def req(url,payload=None,timeout=90):
    body=None if payload is None else json.dumps(payload).encode()
    hd={"User-Agent":"CryptoLab-CompoundRealizedFlow-V0.1.2","Accept":"application/json"}
    if body is not None: hd["Content-Type"]="application/json"
    q=Request(url,data=body,headers=hd,method="POST" if body is not None else "GET")
    with urlopen(q,timeout=timeout) as r: raw=r.read()
    return json.loads(raw.decode()),h(raw)

def logs():
    out=[]; seen=set(); pages=[]; a=B0
    while a<=B1:
        b=min(B1,a+1_999_999)
        u=("https://eth.blockscout.com/api/?module=logs&action=getLogs"
           f"&fromBlock={a}&toBlock={b}&address={COMET}&topic0={BUY}")
        time.sleep(1.1); o,sh=req(u)
        xs=o.get("result") if isinstance(o,dict) else None
        if not isinstance(xs,list) or len(xs)>=1000: raise RuntimeError(f"bad logs {a}-{b}")
        pages.append({"from":a,"to":b,"count":len(xs),"sha256":sh})
        for x in xs:
            k=(str(x.get("blockNumber","")),str(x.get("transactionHash","")).lower(),str(x.get("logIndex","")))
            if k not in seen: seen.add(k); out.append(x)
        a=b+1
    return out,pages

def buyrow(x):
    t=x.get("topics") or []; w=wd(x.get("data"))
    return {"block":iv(x["blockNumber"]),"txi":iv(x["transactionIndex"]),"logi":iv(x["logIndex"]),
            "tx":str(x["transactionHash"]).lower(),"buyer":ad(t[1]),"asset":ad(t[2]),"base":w[0],"coll":w[1]}
def tr(x):
    t=x.get("topics") or []
    if len(t)<3 or str(t[0]).lower()!=TRANSFER: return None
    w=wd(x.get("data"))
    if not w:return None
    return {"token":str(x.get("address","")).lower(),"from":ad(t[1]),"to":ad(t[2]),"amount":w[0],"logi":iv(x["logIndex"])}

def batch(selected):
    payload=[]; idmap={}
    i=1
    for txh in selected:
        payload.append({"jsonrpc":"2.0","id":i,"method":"eth_getTransactionByHash","params":[txh]}); idmap[i]=(txh,"tx"); i+=1
        payload.append({"jsonrpc":"2.0","id":i,"method":"eth_getTransactionReceipt","params":[txh]}); idmap[i]=(txh,"receipt"); i+=1
    attempts=[]
    best=None
    for ep in ENDPOINTS:
        try:
            o,rawh=req(ep,payload,90)
            if not isinstance(o,list): raise RuntimeError("non-list batch response")
            pairs={txh:{} for txh in selected}
            errors=[]
            for item in o:
                rid=item.get("id"); tag=idmap.get(rid)
                if not tag: continue
                txh,kind=tag
                if "error" in item or item.get("result") is None:
                    errors.append({"id":rid,"tx":txh,"kind":kind,"error":item.get("error")})
                else: pairs[txh][kind]=item["result"]
            usable=sum(1 for x in pairs.values() if isinstance(x.get("tx"),dict) and isinstance(x.get("receipt"),dict))
            attempts.append({"endpoint":ep,"raw_sha256":rawh,"responses":len(o),"usable_pairs":usable,"errors":errors})
            if best is None or usable>best[0]: best=(usable,ep,pairs,rawh,attempts.copy())
            if usable>=int(0.95*len(selected)+0.999999): return ep,pairs,rawh,attempts
        except Exception as e:
            attempts.append({"endpoint":ep,"error":repr(e)})
    if best: return best[1],best[2],best[3],attempts
    raise RuntimeError(json.dumps(attempts,sort_keys=True))

receipt={"program":"COMPOUND_REALIZED_DISPOSAL_FLOW_SOURCE_V0.1.2","lab_id":LAB_ID,
"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
"transport_retry_of":{"v0_1_run":36346693857,"v0_1_1_run":36346885795},
"firewall":{"source_only":True,"market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
"protected_2025_market_outcomes_opened":False,"live_trading":False,"orders":False,"exchange_mutation":False,
"capital":False,"paid_data":False,"main_merge":False,"post_outcome_tuning":False}}

try:
    raw,pages=logs(); bs=[buyrow(x) for x in raw]; bs.sort(key=lambda x:(x["block"],x["txi"],x["logi"]))
    buyers=Counter(x["buyer"] for x in bs); assets=Counter(x["asset"] for x in bs)
    m=defaultdict(list)
    for x in bs:m[x["tx"]].append(x)
    uniq=sorted(m); selected=sorted(uniq,key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:min(N,len(uniq))]
    expected_events=sum(len(m[x]) for x in selected)
    ep,pairs,batch_sha,attempts=batch(selected)

    usable=inferred=onward=buyer_sender=0; records=[]; errors=[]
    for txh in selected:
        p=pairs.get(txh,{})
        tx=p.get("tx"); rc=p.get("receipt")
        if not isinstance(tx,dict) or not isinstance(rc,dict):
            errors.append({"tx":txh,"error":"missing tx or receipt in batch"}); continue
        usable+=1; sender=str(tx.get("from","")).lower()
        ts=[z for z in (tr(l) for l in (rc.get("logs") or [])) if z]
        evs=[]
        for b in m[txh]:
            if b["buyer"]==sender: buyer_sender+=1
            cs=[t for t in ts if t["token"]==b["asset"] and t["from"]==COMET and t["amount"]==b["coll"] and t["logi"]<b["logi"]]
            cs.sort(key=lambda t:t["logi"],reverse=True); hit=cs[0] if cs else None; rec=hit["to"] if hit else None
            later=[]
            if rec:
                inferred+=1; later=[t for t in ts if t["token"]==b["asset"] and t["from"]==rec and t["logi"]>b["logi"] and t["amount"]>0]
                if later:onward+=1
            evs.append({"buy_log_index":b["logi"],"buyer":b["buyer"],"asset":b["asset"],"base_amount_raw":str(b["base"]),
                        "collateral_amount_raw":str(b["coll"]),"recipient_inferred":rec,
                        "recipient_transfer_log_index":hit["logi"] if hit else None,"same_tx_onward_transfer":bool(later),
                        "same_tx_onward_transfer_count":len(later),"buyer_equals_tx_sender":b["buyer"]==sender})
        records.append({"tx":txh,"block":iv(rc.get("blockNumber")),"tx_sender":sender,
                        "tx_to":str(tx.get("to","")).lower() if tx.get("to") else None,"receipt_status":iv(rc.get("status","0x0")),
                        "buy_events":evs})
    sel=len(selected); ur=usable/sel if sel else 0; ir=inferred/expected_events if expected_events else 0
    status="SOURCE_CORPUS_DRIFT" if len(bs)!=EXPECTED else ("SOURCE_REALIZED_FLOW_PASS" if len(buyers)>=1 and len(assets)>=1 and ur>=.95 and ir>=.90 else "SOURCE_REALIZED_FLOW_PARTIAL")
    receipt.update({"status":status,"source":{"comet":COMET,"window_blocks":[B0,B1],"expected_parent_canary_buy_logs":EXPECTED,
                    "buy_topic":BUY,"transfer_topic":TRANSFER,"batch_endpoint_used":ep,"batch_response_sha256":batch_sha},
      "source_pages":pages,"batch_attempts":attempts,
      "corpus":{"buy_logs":len(bs),"unique_transactions":len(uniq),"unique_buyers":len(buyers),"unique_assets":len(assets),
                "buyer_concentration_top15":[{"buyer":a,"buy_logs":c,"share_pct":pct(c,len(bs))} for a,c in buyers.most_common(15)],
                "by_asset":dict(sorted(assets.items()))},
      "deterministic_receipt_probe":{"selection_rule":"ascending SHA256(lowercase tx hash), first 64 unique BuyCollateral transactions",
        "selected_transactions":sel,"usable_transactions":usable,"usable_transactions_pct":pct(usable,sel),
        "probed_buy_events":expected_events,"recipient_inferred_events":inferred,"recipient_inferred_pct":pct(inferred,expected_events),
        "buyer_equals_tx_sender_events":buyer_sender,"buyer_equals_tx_sender_pct":pct(buyer_sender,expected_events),
        "same_tx_onward_transfer_events":onward,"same_tx_onward_transfer_pct":pct(onward,inferred),"records":records,"errors":errors,
        "note":"Onward transfer is a source routing diagnostic only; not automatically a DEX sale."},
      "gate":{"exact_999_parent_canary":len(bs)==EXPECTED,"buyer_and_asset_population_present":len(buyers)>=1 and len(assets)>=1,
              "receipt_probe_sample_complete":sel==min(N,len(uniq)),"receipt_usable_ge_95pct":ur>=.95,"recipient_inference_ge_90pct":ir>=.90,
              "onward_transfer_is_non_gate_diagnostic":True},
      "interpretation":{"edge_claim":False,"direction_claim":False,"holding_period_selected":False,
                        "economic_test_authorized":False,"protected_2025_market_test_authorized":False}})
except Exception as e:
    receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e),
      "interpretation":{"edge_claim":False,"direction_claim":False,"holding_period_selected":False,
                        "economic_test_authorized":False,"protected_2025_market_test_authorized":False}})

pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode(); receipt["receipt_sha256_pre_self_field"]=h(pre)
out=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_SOURCE_RECEIPT_V0.1.2.json")
with open(out,"w",encoding="utf-8") as f: json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2)); print("receipt="+out)
