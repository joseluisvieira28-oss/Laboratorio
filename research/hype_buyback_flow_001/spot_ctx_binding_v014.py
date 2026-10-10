#!/usr/bin/env python3
"""One-source, source-only diagnostic for exact market index / context identity."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import urllib.request

OUT=Path("research/hype_buyback_flow_001/receipts/spot_ctx_binding_v014")
OUT.mkdir(parents=True,exist_ok=True)
raw_body=b'{"type":"spotMetaAndAssetCtxs"}'
req=urllib.request.Request("https://api.hyperliquid.xyz/info",data=raw_body,
    method="POST",headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req,timeout=20) as resp:
    raw=resp.read(2000001)
    http=resp.status
if len(raw)>2000000:
    raise ValueError("oversized_response")
(OUT/"spot_meta_ctxs_raw.json").write_bytes(raw)
meta,ctxs=json.loads(raw)
tokens={x["name"]:x["index"] for x in meta["tokens"] if x.get("name") in ("HYPE","USDC")}
assert set(tokens)=={"HYPE","USDC"}
pairs=[(i,x) for i,x in enumerate(meta["universe"])
       if x.get("tokens")==[tokens["HYPE"],tokens["USDC"]]]
assert len(pairs)==1 and pairs[0][1]["name"]=="@107"
pos,pair=pairs[0]
coin_matches=[(i,ctx) for i,ctx in enumerate(ctxs) if isinstance(ctx,dict) and ctx.get("coin")=="@107"]
target={"universe_array_position":pos,"market_object_index":pair.get("index"),
        "matched_by_coin_count":len(coin_matches),
        "exact_ctx_matches":[{"array_index":i,"coin":x.get("coin"),
                              "dayNtlVlm":x.get("dayNtlVlm"),
                              "midPx":x.get("midPx")} for i,x in coin_matches],
        "ctx_at_universe_position":{"coin":ctxs[pos].get("coin"),"dayNtlVlm":ctxs[pos].get("dayNtlVlm")} if pos<len(ctxs) else None,
        "ctx_at_market_object_index":{"coin":ctxs[pair["index"]].get("coin"),
                         "dayNtlVlm":ctxs[pair["index"]].get("dayNtlVlm")}
                          if isinstance(pair.get("index"),int) and pair["index"]<len(ctxs) else None,
        "ctx_array_length":len(ctxs)}
match_valid=len(coin_matches)==1 and coin_matches[0][0]==pair.get("index")
output={"candidate":"HYPE-BUYBACK-FLOW-001","phase":"SOURCE_ONLY",
        "outcome_lookups":0,"trading_authority":"NONE","http_status":http,
        "raw_sha256":hashlib.sha256(raw).hexdigest(),
        "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_id":os.getenv("GITHUB_RUN_ID","LOCAL"),
        "source_volume_identity":"EXACT_MARKET_CONTEXT_MATCH" if match_valid else "SOURCE_BLOCKED_MAPPING",
        "mapped_context_diagnostic":target}
(OUT/"SPOT_CTX_IDENTITY_RECEIPT_V014.json").write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
print(json.dumps(output,indent=2,sort_keys=True))
