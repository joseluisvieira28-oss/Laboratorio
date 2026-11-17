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
    if not isinstance(account,dict):return None
    info=(((account.get("result") or {}).get("value") or {}).get("data") or {}).get("parsed") or {}
    i=info.get("info") or {}
    if not i:return None
    supply=float(i.get("supply") or 0)
    a=((largest.get("result") or {}).get("value") or []) if isinstance(largest,dict) else []
    amounts=[float(row.get("amount") or 0) for row in a]
    return {"mint_authority_active":i.get("mintAuthority") is not None,
        "freeze_authority_active":i.get("freezeAuthority") is not None,
        "mint_data_seen":True,"supply_base_units":str(i.get("supply")),
        "top20_token_accounts_pct":round(100*sum(amounts)/supply,4) if supply>0 and a else None,
        "top_accounts_count":len(a),
        "concentration_source":"UNAVAILABLE" if not a else "PUBLIC_TOKEN_ACCOUNTS_ONLY",
        "note":"token accounts are NOT unique beneficial owners; pool/bonding accounts can dominate"}

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

def carryforward_from_prior(pools):
    """Longitudinal sampling, fixed by SHA-256, never selected using future prices.
    Only observe pool attr; a drop is a warning, never a fraud label.
    """
    entries={}
    prior_path=pathlib.Path(os.environ.get("DIGUI007_PRIOR_PATH","digui007-prior/snapshot.json"))
    prior_loaded=False
    if prior_path.is_file():
        try:
            prior=json.loads(prior_path.read_text(encoding="utf-8"))
            for item in prior.get("tracking",[]):
                key=item.get("mint")
                if key and item.get("pool_address"):entries[key]=item
            prior_loaded=True
        except (ValueError,OSError):
            pass
    now=dt.datetime.now(dt.timezone.utc)
    # Take exactly two addresses per observation, chosen by public-key SHA-256,
    # not by their popularity, prior returns, liquidity or other observed results.
    new_cohort=sorted(pools.values(),key=lambda p:hashlib.sha256(p["mint"].encode()).hexdigest())[:2]
    for p in new_cohort:
        mint=p["mint"]
        entries.setdefault(mint,{"mint":mint,"pool_address":p["pool_address"],
            "first_seen":p.get("created_at_claimed") or utc(),
            "source":"GeckoTerminal-new-pools","samples":[]})
    selected=[]
    for e in entries.values():
        try:
            first=dt.datetime.fromisoformat(e["first_seen"].replace("Z","+00:00"))
            age=(now-first).total_seconds()
            if age<0 or age>36*3600:continue
        except (ValueError,TypeError,AttributeError):continue
        selected.append(e)
    # Cap allocation oldest-first so continued samples survive to >=24h.
    selected.sort(key=lambda e:(e["first_seen"],e["mint"]))
    selected=selected[:40]
    receipts=[]
    for ent in selected:
        pool_addr=ent["pool_address"]
        rec=request("https://api.geckoterminal.com/api/v2/networks/solana/pools/"+pool_addr)
        attrs=(((rec.get("response") or {}).get("data") or {}).get("attributes") or {})
        sample={"observed_at":rec["received_at"],"http_status":rec["http_status"],
          "price_usd":attrs.get("base_token_price_usd"),
          "reserve_usd":attrs.get("reserve_in_usd"),
          "volume_usd":attrs.get("volume_usd"),"error":rec["error"],
          "source_hash":rec["body_sha256"]}
        ent.setdefault("samples",[]).append(sample)
        try:
            first_liq=next(float(s["reserve_usd"]) for s in ent["samples"]
                           if s.get("reserve_usd") is not None and float(s["reserve_usd"])>0)
            last_liq=float(sample["reserve_usd"])
            sample["liquidity_drop_from_first_pct"]=round(100*(1-last_liq/first_liq),2)
            sample["liq_drop_gt_80pct"]=last_liq < .2*first_liq
        except (StopIteration,TypeError,ValueError,ZeroDivisionError):pass
        receipts.append({"mint":ent["mint"],"pool_address":pool_addr,"receipt":rec})
    return selected,receipts,prior_loaded

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
    largest_throttled=False
    for mint, pool in list(pools.items())[:MAX_ENRICH]:
        dex_receipt=request(DEX.format(mint))
        payload=dex_receipt.get("response")
        pool["dex"]=choose_dex(payload,mint,pool["pool_address"])
        receipts["dex"].append(dex_receipt)
        acc=rpc("getAccountInfo",[mint,{"encoding":"jsonParsed","commitment":"finalized"}],2)
        largest=(rpc("getTokenLargestAccounts",[mint,{"commitment":"finalized"}],3)
                 if not largest_throttled else {"response":None,"error":"SKIPPED_AFTER_RATE_LIMIT",
                   "http_status":None,"requested_at":utc(),"received_at":utc(),
                   "body_sha256":None})
        if largest["http_status"]==429:largest_throttled=True
        pool["onchain"]=decode_chain(acc.get("response"),largest.get("response"))
        receipts["mint_rpc"].append({"mint":mint,"account":acc,"largest":largest})
        assess(pool)
    for pool in list(pools.values())[MAX_ENRICH:]: assess(pool)
    tracked,tracking_receipts,prior_loaded=carryforward_from_prior(pools)
    output={"version":"digui-007.1","collected_after":started,"completed_at":utc(),
       "universe":"GeckoTerminal latest two pages only; NOT full Pump.fun launch universe",
       "gecko_raw_pools_seen":gecko_seen,"distinct_base_mints":len(pools),
       "enriched":min(len(pools),MAX_ENRICH),"launch_coverage":launch_coverage,
       "observations":list(pools.values()),"tracking":tracked,
       "tracking_previous_loaded":prior_loaded,
       "tracking_receipts":tracking_receipts,"receipts":receipts,
       "no_orders":True,"no_private_keys":True,"no_future_labels":True,
       "quality_gates":{"full_universe":False,"asof_onchain":False,"risk_validated":False,
         "economic_edge":False,"proven_execution":False}}
    return output

def main():
    # Stop calling public APIs after the predeclared ~30-day 2026 observation window.
    if dt.datetime.now(dt.timezone.utc).date()>dt.date(2026,12,17):
        print("DIGUI007_WINDOW_CLOSED: no API calls or trading")
        return 0
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
      "risk_flag_counts":{flag:sum(flag in v["flags"] for v in output["observations"]) for flag in sorted({f for v in output["observations"] for f in v["flags"]})},
      "partial_or_unknown":sum("PARTIAL" in v["flag_status"] or v["flag_status"]=="unknown" for v in output["observations"]),
      "no_liquidity_data":sum(v["gecko_liquidity_usd"] is None for v in output["observations"]),
      "tracking_count":len(output["tracking"]),"prior_loaded":output["tracking_previous_loaded"],
      "errors":{"gecko":[r["error"] for r in output["receipts"]["gecko"]],
                "pump_rpc":output["receipts"]["rpc_pump_recent"]["error"]},
      "economic_status":"NO-GO","orders_sent":0},ensure_ascii=False))
    if output["gecko_raw_pools_seen"]==0:
        print("SOURCE_BLOCKED: no current pool payloads",file=sys.stderr)
        return 2
    return 0
if __name__=="__main__":
    sys.exit(main())
