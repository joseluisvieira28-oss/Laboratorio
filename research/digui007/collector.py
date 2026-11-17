#!/usr/bin/env python3
"""DIGUI-007: read-only, timestamped prospective observation. Never trades.
Only records what public services returned at the time. No secret keys.
This is NOT an all-launch universe or validated fraud classifier.
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

GECKO = "https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page={}"
DEX = "https://api.dexscreener.com/token-pairs/v1/solana/{}"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
MAX_ENRICH = int(os.environ.get("DIGUI007_MAX_ENRICH", "8"))
USER_AGENT = "CryptoLab-DIGUI007-Research/0.1 (read-only)"

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")

def request(url, method="GET", payload=None, timeout=18):
    start = utc()
    monotonic = time.monotonic()
    body = None
    if payload is not None:
        body=json.dumps(payload,sort_keys=True,separators=(",",":")).encode("utf-8")
    headers={"User-Agent":USER_AGENT,"Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    req=urllib.request.Request(url,data=body,headers=headers,method=method)
    receipt={"url":url,"method":method,"requested_at":start,"received_at":None,
             "http_status":None,"elapsed_ms":None,"body_sha256":None,
             "error":None,"response":None}
    try:
        with urllib.request.urlopen(req,timeout=timeout) as res:
            raw=res.read(1_800_000)
            receipt["http_status"]=res.status
            receipt["body_sha256"]=hashlib.sha256(raw).hexdigest()
        receipt["response"]=json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        receipt["http_status"]=exc.code
        receipt["error"]="HTTP "+str(exc.code)
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,json.JSONDecodeError) as exc:
        receipt["error"]=type(exc).__name__+": "+str(exc)[:160]
    finally:
        receipt["received_at"]=utc()
        receipt["elapsed_ms"]=round((time.monotonic()-monotonic)*1000)
    return receipt

def rpc(method, params, rid):
    return request(SOLANA_RPC,"POST",{
        "jsonrpc":"2.0","id":rid,"method":method,"params":params
    })

def token_from_relationship(pair):
    rel=pair.get("relationships") or {}
    base=((rel.get("base_token") or {}).get("data") or {}).get("id") or ""
    quote=((rel.get("quote_token") or {}).get("data") or {}).get("id") or ""
    # Don't imply base is always the newly minted token.
    if not base.startswith("solana_"):return None,quote
    return base.split("solana_",1)[1],quote

def parse_pool(rec):
    attrs=rec.get("attributes") or {}
    mint,quote=token_from_relationship(rec)
    if not mint:return None
    return {"mint":mint,"quote_id":quote,"pool_id":rec.get("id"),
       "pool_address":attrs.get("address"),"created_at_claimed":attrs.get("pool_created_at"),
       "gecko_prices":{"base_usd":attrs.get("base_token_price_usd"),
                       "quote_usd":attrs.get("quote_token_price_usd")},
       "gecko_liquidity_usd":attrs.get("reserve_in_usd"),
       "gecko_volume_usd":attrs.get("volume_usd"),
       "gecko_transactions":attrs.get("transactions"),
       "dex":None,"onchain":None,"flags":[],"flag_status":"unknown"}

def choose_dex(pairs,mint,pool_addr):
    if not isinstance(pairs,list):return None
    filt=[p for p in pairs if p.get("chainId")=="solana"]
    if not filt:return None
    chosen=next((p for p in filt if p.get("pairAddress")==pool_addr),None)
    if chosen is None:
        chosen=max(filt,key=lambda p:float((p.get("liquidity") or {}).get("usd") or 0))
    return {"pairAddress":chosen.get("pairAddress"),"dexId":chosen.get("dexId"),
       "pairCreatedAt":chosen.get("pairCreatedAt"),
       "priceUsd":chosen.get("priceUsd"),"liquidityUsd":(chosen.get("liquidity") or {}).get("usd"),
       "marketCap":chosen.get("marketCap"),"fdv":chosen.get("fdv"),
       "volume":chosen.get("volume"),"txns":chosen.get("txns"),
       "boosts":chosen.get("boosts"),"reportedAt":utc(),
       "selected_pool_matches_gecko":chosen.get("pairAddress")==pool_addr}

def decode_chain(account,largest):
    if not isinstance(account,dict) or not isinstance(largest,dict):return None
    info=(((account.get("result") or {}).get("value") or {}).get("data") or {}).get("parsed") or {}
    i=info.get("info") or {}
    supply=float(i.get("supply") or 0)
    a=(largest.get("result") or {}).get("value") or []
    amounts=[float(row.get("amount") or 0) for row in a]
    return {"mint_authority_active":i.get("mintAuthority") is not None,
        "freeze_authority_active":i.get("freezeAuthority") is not None,
        "mint_data_seen":bool(i),"supply_base_units":str(i.get("supply")),
        "top20_token_accounts_pct":round(100*sum(amounts)/supply,4) if supply>0 and a else None,
        "top_accounts_count":len(a),"note":"token accounts are NOT unique beneficial owners; pool/bonding accounts can dominate"}

def assess(pool):
    flags=[]
    d=pool.get("dex")
    c=pool.get("onchain")
    liq=d.get("liquidityUsd") if d else pool.get("gecko_liquidity_usd")
    try:
        if liq is not None and float(liq)<1000:flags.append("LOW_LIQUIDITY_LT_1000_USD")
    except (TypeError,ValueError):pass
    if c and c.get("mint_data_seen"):
        if c["mint_authority_active"]:flags.append("MINT_AUTHORITY_ACTIVE")
        if c["freeze_authority_active"]:flags.append("FREEZE_AUTHORITY_ACTIVE")
        if c.get("top20_token_accounts_pct") is not None and c["top20_token_accounts_pct"]>85:
            flags.append("CONCENTRATED_TOKEN_ACCOUNTS_NOT_WALLETS")
    pool["flags"]=flags
    # Flags are cautionary observations, NEVER proof of fraud or safety.
    pool["flag_status"]="caution" if flags else "no_flags_in_available_fields"
    if not d or not c or not c.get("mint_data_seen"):
        pool["flag_status"]="PARTIAL_DATA_UNVERIFIED" if not flags else "CAUTION_PARTIAL_DATA"
    return pool

def collect():
    started=utc()
    gecko_receipts=[request(GECKO.format(page)) for page in [1,2]]
    pools={}
    gecko_seen=0
    for receipt in gecko_receipts:
        data=receipt.get("response")
        if not isinstance(data,dict):continue
        for rec in data.get("data") or []:
            gecko_seen+=1
            entry=parse_pool(rec)
            if entry:
                # preserve earliest new pool by mint within the same observation
                pools.setdefault(entry["mint"],entry)
    rpc_receipt=rpc("getSignaturesForAddress",[PUMP_PROGRAM,{"limit":1000,"commitment":"finalized"}],1)
    tx=(rpc_receipt.get("response") or {}).get("result")
    launch_coverage={"pump_program":PUMP_PROGRAM,
        "recent_signatures_count":len(tx) if isinstance(tx,list) else None,
        "signature_limit_hit":len(tx)==1000 if isinstance(tx,list) else None,
        "new_launch_count":None,
        "coverage":"UNVERIFIED; signatures != token launches; 1000-result truncation possible"}
    receipts={"gecko":gecko_receipts,
       "rpc_pump_recent":{"url":SOLANA_RPC,"requested_at":rpc_receipt["requested_at"],
           "received_at":rpc_receipt["received_at"],"http_status":rpc_receipt["http_status"],
           "body_sha256":rpc_receipt["body_sha256"],"error":rpc_receipt["error"]},
       "dex":[],"mint_rpc":[],"pump_rpc_response":rpc_receipt.get("response")}
    for mint, pool in list(pools.items())[:MAX_ENRICH]:
        dex_receipt=request(DEX.format(mint))
        payload=dex_receipt.get("response")
        pool["dex"]=choose_dex(payload,mint,pool["pool_address"])
        receipts["dex"].append(dex_receipt)
        acc=rpc("getAccountInfo",[mint,{"encoding":"jsonParsed","commitment":"finalized"}],2)
        largest=rpc("getTokenLargestAccounts",[mint,{"commitment":"finalized"}],3)
        pool["onchain"]=decode_chain(acc.get("response"),largest.get("response"))
        receipts["mint_rpc"].append({"mint":mint,"account":acc,"largest":largest})
        assess(pool)
    for pool in list(pools.values())[MAX_ENRICH:]: assess(pool)
    output={"version":"digui-007.1","collected_after":started,"completed_at":utc(),
       "universe":"GeckoTerminal latest two pages only; NOT full Pump.fun launch universe",
       "gecko_raw_pools_seen":gecko_seen,"distinct_base_mints":len(pools),
       "enriched":min(len(pools),MAX_ENRICH),"launch_coverage":launch_coverage,
       "observations":list(pools.values()),"receipts":receipts,
       "no_orders":True,"no_private_keys":True,"no_future_labels":True,
       "quality_gates":{"full_universe":False,"asof_onchain":False,"risk_validated":False,
         "economic_edge":False,"proven_execution":False}}
    return output

def main():
    output=collect()
    outdir=pathlib.Path(os.environ.get("DIGUI007_OUTPUT_DIR","digui007-evidence"))
    outdir.mkdir(parents=True,exist_ok=True)
    path=outdir/"snapshot.json"
    raw=json.dumps(output,sort_keys=True,indent=2,ensure_ascii=False).encode("utf-8")
    path.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest()
    (outdir/"snapshot.sha256").write_text(digest+"  snapshot.json\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"sha256":digest,
      "raw_pools":output["gecko_raw_pools_seen"],
      "distinct_mints":output["distinct_base_mints"],
      "enriched":output["enriched"],
      "rpc_count":output["launch_coverage"]["recent_signatures_count"],
      "errors":{"gecko":[r["error"] for r in output["receipts"]["gecko"]],
                "pump_rpc":output["receipts"]["rpc_pump_recent"]["error"]},
      "economic_status":"NO-GO","orders_sent":0},ensure_ascii=False))
    if output["gecko_raw_pools_seen"]==0:
        print("SOURCE_BLOCKED: no current pool payloads",file=sys.stderr)
        return 2
    return 0
if __name__=="__main__":
    sys.exit(main())
