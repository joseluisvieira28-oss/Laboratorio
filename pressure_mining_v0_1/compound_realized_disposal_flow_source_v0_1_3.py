#!/usr/bin/env python3
import hashlib, json, os, time
from collections import Counter, defaultdict
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

LAB_ID="COMPOUND-REALIZED-DISPOSAL-FLOW-001"
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
B0=16_308_190
B1=21_525_890
EXPECTED=999
N=64
BUY="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BASE="https://eth.blockscout.com"

def sha(b): return hashlib.sha256(b).hexdigest()
def iv(v):
    if isinstance(v,int): return v
    s=str(v or "0")
    return int(s,16) if s.startswith("0x") else int(s)
def ad(v):
    if isinstance(v,dict): v=v.get("hash") or v.get("address") or v.get("value")
    s=str(v or "").lower()
    return "0x"+s[-40:] if len(s)>=40 else None
def topic_value(v):
    if isinstance(v,dict):
        return str(v.get("value") or v.get("hex") or v.get("data") or "").lower()
    return str(v or "").lower()
def wd(d):
    if isinstance(d,dict): d=d.get("data") or d.get("value") or d.get("raw") or ""
    s=str(d or "")
    if s.startswith("0x"): s=s[2:]
    if len(s)%64: raise ValueError("bad event data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def pct(a,b): return round(100*a/b,4) if b else None

def fetch(url, attempts=7, timeout=90):
    errs=[]
    for i in range(attempts):
        try:
            req=Request(url,headers={"User-Agent":"CryptoLab-CompoundRealizedFlow-V0.1.3","Accept":"application/json"})
            with urlopen(req,timeout=timeout) as r:
                raw=r.read()
            return json.loads(raw.decode()),sha(raw),errs
        except HTTPError as e:
            errs.append({"attempt":i+1,"kind":"HTTPError","code":e.code,"error":repr(e)})
            if e.code not in (429,500,502,503,504): raise
            time.sleep(min(8.0,0.8*(2**i)))
        except (URLError,TimeoutError) as e:
            errs.append({"attempt":i+1,"kind":type(e).__name__,"error":repr(e)})
            time.sleep(min(8.0,0.8*(2**i)))
    raise RuntimeError(json.dumps(errs,sort_keys=True))

def corpus():
    out=[]; seen=set(); pages=[]; cur=B0
    while cur<=B1:
        stop=min(B1,cur+1_999_999)
        url=(f"{BASE}/api/?module=logs&action=getLogs"
             f"&fromBlock={cur}&toBlock={stop}&address={COMET}&topic0={BUY}")
        time.sleep(1.1)
        o,h,errs=fetch(url)
        rows=o.get("result") if isinstance(o,dict) else None
        if not isinstance(rows,list) or len(rows)>=1000:
            raise RuntimeError(f"invalid/truncated corpus page {cur}-{stop}: {type(rows)} {len(rows) if isinstance(rows,list) else None}")
        pages.append({"from":cur,"to":stop,"count":len(rows),"sha256":h,"retry_errors":errs})
        for x in rows:
            key=(str(x.get("blockNumber","")).lower(),str(x.get("transactionHash","")).lower(),str(x.get("logIndex","")).lower())
            if key not in seen: seen.add(key); out.append(x)
        cur=stop+1
    return out,pages

def buyrow(x):
    t=x.get("topics") or []; w=wd(x.get("data"))
    if len(t)<3 or len(w)<2: raise ValueError("BuyCollateral malformed")
    return {"block":iv(x.get("blockNumber")),"txi":iv(x.get("transactionIndex")),"logi":iv(x.get("logIndex")),
            "tx":str(x.get("transactionHash","")).lower(),"buyer":ad(t[1]),"asset":ad(t[2]),
            "base":w[0],"coll":w[1]}

def extract_log_index(x):
    for k in ("index","log_index","logIndex"):
        if k in x and x.get(k) is not None:
            try: return iv(x.get(k))
            except Exception: pass
    return None

def extract_address(x):
    return ad(x.get("address") or x.get("address_hash") or x.get("contract_address"))

def transfer(x):
    topics=x.get("topics") or []
    if len(topics)<3: return None
    if topic_value(topics[0])!=TRANSFER: return None
    w=wd(x.get("data"))
    if not w: return None
    li=extract_log_index(x)
    if li is None: return None
    return {"token":extract_address(x),"from":ad(topic_value(topics[1])),"to":ad(topic_value(topics[2])),
            "amount":w[0],"logi":li}

def get_tx(txh):
    o,h,errs=fetch(f"{BASE}/api/v2/transactions/{txh}")
    if not isinstance(o,dict): raise RuntimeError("transaction detail is not object")
    return o,h,errs

def get_logs(txh):
    all_items=[]; page_hashes=[]; retry_errors=[]; params={}
    for _ in range(25):
        q=("?"+urlencode(params)) if params else ""
        o,h,errs=fetch(f"{BASE}/api/v2/transactions/{txh}/logs{q}")
        retry_errors.extend(errs); page_hashes.append(h)
        if isinstance(o,list):
            items=o; nxt=None
        elif isinstance(o,dict):
            items=o.get("items")
            if items is None and isinstance(o.get("result"),list): items=o.get("result")
            nxt=o.get("next_page_params")
        else:
            raise RuntimeError("logs response invalid")
        if not isinstance(items,list): raise RuntimeError(f"logs items invalid keys={list(o) if isinstance(o,dict) else type(o)}")
        all_items.extend(items)
        if not nxt: break
        if not isinstance(nxt,dict): raise RuntimeError("next_page_params not dict")
        params=nxt
    else:
        raise RuntimeError("log pagination exceeded 25 pages")
    return all_items,page_hashes,retry_errors

receipt={
 "program":"COMPOUND_REALIZED_DISPOSAL_FLOW_SOURCE_V0.1.3",
 "lab_id":LAB_ID,
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "transport_retry_of":{"v0_1_run":36346693857,"v0_1_2_run":36347122477},
 "firewall":{"source_only":True,"market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
             "protected_2025_market_outcomes_opened":False,"live_trading":False,"orders":False,
             "exchange_mutation":False,"capital":False,"paid_data":False,"main_merge":False,
             "post_outcome_tuning":False},
}

try:
    raw,pages=corpus()
    bs=[buyrow(x) for x in raw]
    bs.sort(key=lambda x:(x["block"],x["txi"],x["logi"]))
    buyers=Counter(x["buyer"] for x in bs if x["buyer"])
    assets=Counter(x["asset"] for x in bs if x["asset"])
    m=defaultdict(list)
    for x in bs: m[x["tx"]].append(x)
    uniq=sorted(m)
    selected=sorted(uniq,key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:min(N,len(uniq))]
    expected_events=sum(len(m[x]) for x in selected)

    usable=inferred=onward=buyer_sender=0
    records=[]; errors=[]
    for n,txh in enumerate(selected,1):
        try:
            time.sleep(0.34)
            tx,tx_sha,tx_retries=get_tx(txh)
            time.sleep(0.34)
            ls,log_hashes,log_retries=get_logs(txh)
            sender=ad(tx.get("from"))
            status=tx.get("status")
            success=(status=="ok" or status is True or status=="1" or status==1)
            if sender is None: raise RuntimeError("transaction sender unavailable")
            ts=[z for z in (transfer(l) for l in ls) if z]
            usable+=1
            evs=[]
            for b in m[txh]:
                if b["buyer"]==sender: buyer_sender+=1
                cs=[t for t in ts if t["token"]==b["asset"] and t["from"]==COMET and t["amount"]==b["coll"] and t["logi"]<b["logi"]]
                cs.sort(key=lambda t:t["logi"],reverse=True)
                hit=cs[0] if cs else None
                rec=hit["to"] if hit else None
                later=[]
                if rec:
                    inferred+=1
                    later=[t for t in ts if t["token"]==b["asset"] and t["from"]==rec and t["logi"]>b["logi"] and t["amount"]>0]
                    if later: onward+=1
                evs.append({"buy_log_index":b["logi"],"buyer":b["buyer"],"asset":b["asset"],
                            "base_amount_raw":str(b["base"]),"collateral_amount_raw":str(b["coll"]),
                            "recipient_inferred":rec,"recipient_transfer_log_index":hit["logi"] if hit else None,
                            "same_tx_onward_transfer":bool(later),"same_tx_onward_transfer_count":len(later),
                            "buyer_equals_tx_sender":b["buyer"]==sender})
            records.append({"tx":txh,"ordinal":n,"block":tx.get("block_number") or tx.get("block"),
                            "tx_sender":sender,"tx_to":ad(tx.get("to")),"tx_status":status,"tx_success_interpreted":success,
                            "tx_response_sha256":tx_sha,"log_page_sha256":log_hashes,
                            "retry_errors":tx_retries+log_retries,"raw_log_count":len(ls),"erc20_transfer_count":len(ts),
                            "buy_events":evs})
        except Exception as e:
            errors.append({"tx":txh,"ordinal":n,"error":repr(e)})

    sel=len(selected); ur=usable/sel if sel else 0.0; ir=inferred/expected_events if expected_events else 0.0
    if len(bs)!=EXPECTED: status="SOURCE_CORPUS_DRIFT"
    elif len(buyers)<1 or len(assets)<1 or sel<1: status="SOURCE_REALIZED_FLOW_PARTIAL"
    elif ur<0.95 or ir<0.90: status="SOURCE_REALIZED_FLOW_PARTIAL"
    else: status="SOURCE_REALIZED_FLOW_PASS"

    receipt.update({
      "status":status,
      "source":{"comet":COMET,"window_blocks":[B0,B1],"window_utc":["2023-01-01T00:00:00Z","2024-12-31T23:59:59Z"],
                "expected_parent_canary_buy_logs":EXPECTED,"buy_topic":BUY,"transfer_topic":TRANSFER,
                "explorer_transaction_endpoint":BASE+"/api/v2/transactions/{hash}",
                "explorer_logs_endpoint":BASE+"/api/v2/transactions/{hash}/logs"},
      "source_pages":pages,
      "corpus":{"buy_logs":len(bs),"unique_transactions":len(uniq),"unique_buyers":len(buyers),"unique_assets":len(assets),
                "buyer_concentration_top15":[{"buyer":a,"buy_logs":c,"share_pct":pct(c,len(bs))} for a,c in buyers.most_common(15)],
                "by_asset":dict(sorted(assets.items()))},
      "deterministic_receipt_probe":{"selection_rule":"ascending SHA256(lowercase tx hash), first 64 unique BuyCollateral transactions",
                "selected_transactions":sel,"usable_transactions":usable,"usable_transactions_pct":pct(usable,sel),
                "probed_buy_events":expected_events,"recipient_inferred_events":inferred,"recipient_inferred_pct":pct(inferred,expected_events),
                "buyer_equals_tx_sender_events":buyer_sender,"buyer_equals_tx_sender_pct":pct(buyer_sender,expected_events),
                "same_tx_onward_transfer_events":onward,"same_tx_onward_transfer_pct":pct(onward,inferred),
                "records":records,"errors":errors,
                "note":"Same-transaction onward transfer is a routing/flow diagnostic only; it is not automatically a DEX sale and has no PASS threshold."},
      "gate":{"exact_999_parent_canary":len(bs)==EXPECTED,"buyer_and_asset_population_present":len(buyers)>=1 and len(assets)>=1,
              "receipt_probe_sample_complete":sel==min(N,len(uniq)),"receipt_usable_ge_95pct":ur>=0.95,
              "recipient_inference_ge_90pct":ir>=0.90,"onward_transfer_is_non_gate_diagnostic":True},
      "interpretation":{"edge_claim":False,"direction_claim":False,"holding_period_selected":False,
                        "economic_test_authorized":False,"protected_2025_market_test_authorized":False}})
except Exception as e:
    receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e),
                    "interpretation":{"edge_claim":False,"direction_claim":False,"holding_period_selected":False,
                                      "economic_test_authorized":False,"protected_2025_market_test_authorized":False}})

pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=sha(pre)
out=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_SOURCE_RECEIPT_V0.1.3.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2))
print("receipt="+out)
