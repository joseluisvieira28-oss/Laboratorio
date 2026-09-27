#!/usr/bin/env python3
import json, hashlib, os, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from eth_hash.auto import keccak

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def fetch_json(url, method="GET", data=None, timeout=90):
    headers={"User-Agent":"CryptoLab-PressureMining-Census-V0.2","Accept":"application/json"}
    body=None if data is None else json.dumps(data).encode()
    if body is not None:
        headers["Content-Type"]="application/json"
    req=Request(url,data=body,headers=headers,method=method)
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return json.loads(b.decode()), sha256_bytes(b)

RPC_ENDPOINTS=[
    # Blockscout's Ethereum mainnet ETH-RPC is an indexed public fallback and
    # supports eth_getTransactionReceipt + eth_getLogs. It is especially useful
    # for the historical anchor sanity check when ordinary free RPC nodes prune
    # or refuse old receipts.
    "https://eth.blockscout.com/api/eth-rpc",
    "https://ethereum-rpc.publicnode.com",
    "https://rpc.flashbots.net",
    "https://eth.llamarpc.com",
    "https://cloudflare-eth.com",
    "https://eth.drpc.org",
    "https://ethereum.public.blockpi.network/v1/rpc/public",
    "https://public.1rpc.io/eth",
]

def rpc(endpoint, method, params):
    j,_=fetch_json(
        endpoint,
        method="POST",
        data={"jsonrpc":"2.0","id":1,"method":method,"params":params},
        timeout=90,
    )
    if "error" in j:
        raise RuntimeError(str(j["error"]))
    return j["result"]

def block_timestamp(ep,n):
    b=rpc(ep,"eth_getBlockByNumber",[hex(n),False])
    if not isinstance(b,dict) or "timestamp" not in b:
        raise RuntimeError(f"missing block/timestamp for {n}")
    return int(b["timestamp"],16)

def first_block_at_or_after(ep,target_ts):
    hi=int(rpc(ep,"eth_blockNumber",[]),16)
    # Frozen census begins 2023-01-01; 15.5m is safely before that boundary.
    lo=15_500_000
    while lo<hi:
        mid=(lo+hi)//2
        ts=block_timestamp(ep,mid)
        if ts<target_ts:
            lo=mid+1
        else:
            hi=mid
    return lo

def topic(sig):
    return "0x"+keccak(sig.encode()).hex()

def get_logs_adaptive(ep,address,topic0,start,end):
    """Query one event signature at a time; fail closed on provider errors."""
    all_logs=[]
    cur=start
    chunk=100_000
    failures=0
    while cur<=end:
        stop=min(end,cur+chunk-1)
        try:
            logs=rpc(ep,"eth_getLogs",[{
                "address":address,
                "fromBlock":hex(cur),
                "toBlock":hex(stop),
                "topics":[topic0],
            }])
            if not isinstance(logs,list):
                raise RuntimeError("eth_getLogs non-list response")
            all_logs.extend(logs)
            cur=stop+1
            if chunk<100_000:
                chunk=min(100_000,chunk*2)
        except Exception:
            failures+=1
            if chunk<=2_000:
                raise
            chunk=max(2_000,chunk//2)
    return all_logs,failures

def receipt_contains_event(ep,tx_hash,address,topic0):
    rec=rpc(ep,"eth_getTransactionReceipt",[tx_hash])
    if not isinstance(rec,dict):
        raise RuntimeError("anchor transaction receipt unavailable")
    addr=address.lower()
    target=topic0.lower()
    matching=[]
    for lg in rec.get("logs") or []:
        topics=lg.get("topics") or []
        if str(lg.get("address","")).lower()==addr and topics and str(topics[0]).lower()==target:
            matching.append(lg)
    if not matching:
        raise RuntimeError("anchor receipt missing expected event")
    return {
        "tx_hash":tx_hash,
        "block_number":int(rec["blockNumber"],16),
        "matching_logs":len(matching),
    }

receipt={
 "program":"PRESSURE_MINING_SOURCE_CENSUS_V0.2",
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "firewall":{
   "source_only":True,
   "price_returns_opened":False,
   "pnl_computed":False,
   "protected_holdout_opened":False,
   "live_trading":False,
   "orders":False,
   "exchange_mutation":False,
   "paid_data":False,
 },
 "compound":{},
 "pendle":{},
}

# Compound event census: 2023-01-01 through 2024-12-31 only.
#
# V0.1 correction:
# A provider was previously accepted after returning zero logs. That is not
# sufficient archive proof. V0.2 requires a known public on-chain
# AbsorbCollateral anchor receipt AND requires that the same anchor is recovered
# by eth_getLogs inside the frozen historical window.
try:
    roots,_=fetch_json(
        "https://raw.githubusercontent.com/compound-finance/comet/main/deployments/mainnet/usdc/roots.json"
    )
    comet=roots["comet"]
    t0=int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp())
    t1=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())-1
    absorb=topic("AbsorbCollateral(address,address,address,uint256,uint256)")
    buy=topic("BuyCollateral(address,address,uint256,uint256)")

    # Public historical transaction independently observed to contain the
    # canonical USDCv3 AbsorbCollateral topic. Runtime trust comes from direct
    # eth_getTransactionReceipt verification, not from the explorer.
    absorb_anchor_tx="0x437110f3f87836279e9262d6b76f71ed946b3d5e39ad8dd04dbe6aebc43dfd2e"

    attempts=[]
    selected=None
    result=None
    for ep in RPC_ENDPOINTS:
        try:
            if rpc(ep,"eth_chainId",[])!="0x1":
                raise RuntimeError("wrong chain")

            anchor=receipt_contains_event(ep,absorb_anchor_tx,comet,absorb)
            b0=first_block_at_or_after(ep,t0)
            b1=first_block_at_or_after(ep,t1)
            if not (b0 <= anchor["block_number"] <= b1):
                raise RuntimeError(
                    f"anchor block {anchor['block_number']} outside frozen window {b0}-{b1}"
                )

            absorb_logs,fail_a=get_logs_adaptive(ep,comet,absorb,b0,b1)
            buy_logs,fail_b=get_logs_adaptive(ep,comet,buy,b0,b1)

            txs={str(x.get("transactionHash","")).lower() for x in absorb_logs}
            if absorb_anchor_tx.lower() not in txs:
                raise RuntimeError(
                    "archive sanity failure: anchor receipt exists but eth_getLogs did not recover it"
                )
            if len(absorb_logs)==0:
                raise RuntimeError("archive sanity failure: zero AbsorbCollateral logs")

            selected=ep
            result=(b0,b1,absorb_logs,buy_logs,fail_a+fail_b,anchor)
            attempts.append({
                "endpoint":ep,
                "pass":True,
                "absorb_logs":len(absorb_logs),
                "buy_logs":len(buy_logs),
                "block_range":[b0,b1],
                "anchor_recovered":True,
            })
            break
        except Exception as inner:
            attempts.append({"endpoint":ep,"pass":False,"error":repr(inner)})

    if selected is None:
        raise RuntimeError(f"all archive census routes failed sanity checks: {attempts}")

    b0,b1,absorb_logs,buy_logs,failures,anchor=result
    logs=absorb_logs+buy_logs
    counts={
        "AbsorbCollateral":len(absorb_logs),
        "BuyCollateral":len(buy_logs),
        "other":0,
    }
    unique_assets=set()
    unique_borrowers=set()
    for lg in absorb_logs:
        topics=lg.get("topics") or []
        if len(topics)>2:
            unique_borrowers.add("0x"+topics[2][-40:])
        if len(topics)>3:
            unique_assets.add("0x"+topics[3][-40:])
    for lg in buy_logs:
        topics=lg.get("topics") or []
        if len(topics)>2:
            unique_assets.add("0x"+topics[2][-40:])

    # The proposed primitive is explicitly two-stage. If no disposal events are
    # observed, keep the source gate partial rather than claiming a usable
    # inventory-disposal corpus.
    compound_status=(
        "SOURCE_CENSUS_PASS"
        if counts["AbsorbCollateral"]>0 and counts["BuyCollateral"]>0
        else "SOURCE_CENSUS_PARTIAL"
    )
    receipt["compound"]={
      "lab_id":"COMPOUND-INVENTORY-LIQUIDATION-001",
      "status":compound_status,
      "rpc":selected,
      "rpc_attempts":attempts,
      "comet_address":comet,
      "window_utc":["2023-01-01T00:00:00Z","2024-12-31T23:59:59Z"],
      "block_range":[b0,b1],
      "event_topics":{"AbsorbCollateral":absorb,"BuyCollateral":buy},
      "archive_sanity_anchor":anchor,
      "event_counts":counts,
      "unique_assets":len(unique_assets),
      "unique_absorbed_borrowers_lower_bound":len(unique_borrowers),
      "adaptive_query_failures":failures,
      "sample_viability_note":"Source/event census only. No market response, price return, direction or PnL computed.",
    }
except Exception as e:
    receipt["compound"]={
        "lab_id":"COMPOUND-INVENTORY-LIQUIDATION-001",
        "status":"SOURCE_CENSUS_PARTIAL",
        "error":repr(e),
        "rpc_attempts":locals().get("attempts",[]),
        "v01_zero_log_pass_retracted":True,
    }

# Pendle metadata/coverage census only. No convergence values are emitted.
try:
    allm=[]
    skip=0
    for _ in range(20):
        url=f"https://api-v2.pendle.finance/core/v2/markets/all?limit=100&skip={skip}"
        j,_=fetch_json(url,timeout=120)
        rows=j.get("results") if isinstance(j,dict) else None
        if not isinstance(rows,list):
            break
        allm.extend(rows)
        if len(rows)<100:
            break
        skip+=100

    cutoff=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())

    def norm_exp(v):
        if isinstance(v,(int,float)):
            return int(v/1000) if v>10_000_000_000 else int(v)
        if isinstance(v,str):
            try:
                if v.isdigit():
                    return norm_exp(int(v))
                return int(datetime.fromisoformat(v.replace("Z","+00:00")).timestamp())
            except Exception:
                return None
        return None

    eth=[]
    expired=[]
    for m in allm:
        if not isinstance(m,dict):
            continue
        chain=m.get("chain")
        cid=m.get("chainId") or m.get("chain_id") or (chain.get("id") if isinstance(chain,dict) else None)
        if str(cid)!="1":
            continue
        eth.append(m)
        exp=norm_exp(m.get("expiry") or m.get("expiryTimestamp") or m.get("expiration"))
        if exp is not None and exp<cutoff:
            expired.append((m,exp))

    samples=[]
    coverage_pass=0
    historical_row_key_union=set()
    market_key_union=set()
    protocol_counts={}
    accounting_asset_counts={}
    expired_with_points=0
    expired_with_reward_tokens=0
    for m,_ in expired:
        market_key_union.update(m.keys())
        proto=m.get("protocol")
        if isinstance(proto,dict):
            proto=proto.get("name") or proto.get("id")
        if isinstance(proto,str) and proto:
            protocol_counts[proto]=protocol_counts.get(proto,0)+1
        aa=m.get("accountingAsset")
        if isinstance(aa,dict):
            aa=aa.get("symbol") or aa.get("name") or aa.get("address")
        if isinstance(aa,str) and aa:
            accounting_asset_counts[aa]=accounting_asset_counts.get(aa,0)+1
        pts=m.get("points")
        if pts not in (None,False,[],{},""):
            expired_with_points+=1
        rewards=m.get("rewardTokens")
        if rewards not in (None,False,[],{},""):
            expired_with_reward_tokens+=1

    for m,exp in expired[:10]:
        addr=m.get("address")
        if not isinstance(addr,str):
            continue
        try:
            h,_=fetch_json(
                f"https://api-v2.pendle.finance/core/v3/1/markets/{addr}/historical-data",
                timeout=120,
            )
            rows=h.get("results") if isinstance(h,dict) else None
            row_keys=[]
            if isinstance(rows,list) and rows and isinstance(rows[0],dict):
                row_keys=sorted(rows[0].keys())
                historical_row_key_union.update(row_keys)
            total=h.get("total") if isinstance(h,dict) else None
            if isinstance(total,int) and total>0:
                coverage_pass+=1
            samples.append({
              "address":addr,
              "expiry_ts":exp,
              "historical_total":total,
              "timestamp_start":h.get("timestamp_start") if isinstance(h,dict) else None,
              "timestamp_end":h.get("timestamp_end") if isinstance(h,dict) else None,
              "historical_row_keys":row_keys,
            })
        except Exception as inner:
            samples.append({"address":addr,"expiry_ts":exp,"error":repr(inner)})

    pendle_status=(
        "SOURCE_CENSUS_PASS"
        if len(expired)>0 and coverage_pass>0
        else "SOURCE_CENSUS_PARTIAL"
    )
    receipt["pendle"]={
      "lab_id":"PENDLE-PT-MATURITY-CONVERGENCE-001",
      "status":pendle_status,
      "markets_enumerated":len(allm),
      "ethereum_markets":len(eth),
      "ethereum_markets_expired_before_2025":len(expired),
      "expired_with_points_metadata":expired_with_points,
      "expired_with_reward_tokens":expired_with_reward_tokens,
      "protocol_counts":dict(sorted(protocol_counts.items(), key=lambda kv:(-kv[1],kv[0]))),
      "accounting_asset_counts":dict(sorted(accounting_asset_counts.items(), key=lambda kv:(-kv[1],kv[0]))),
      "market_metadata_keys":sorted(market_key_union),
      "historical_row_key_union":sorted(historical_row_key_union),
      "historical_coverage_probe_pass_count":coverage_pass,
      "historical_coverage_probes":samples,
      "sample_viability_note":"Metadata/schema/coverage only. No PT convergence statistic, market return or PnL computed.",
    }
except Exception as e:
    receipt["pendle"]={
        "lab_id":"PENDLE-PT-MATURITY-CONVERGENCE-001",
        "status":"SOURCE_CENSUS_PARTIAL",
        "error":repr(e),
    }

raw=json.dumps(receipt,sort_keys=True,indent=2).encode()
receipt["receipt_sha256_pre_self_field"]=sha256_bytes(raw)
out=os.path.join(OUTDIR,"PRESSURE_MINING_SOURCE_CENSUS_RECEIPT_V0.2.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2)
    f.write("\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
print(f"receipt={out}")
