#!/usr/bin/env python3
import json, time, urllib.request, urllib.error, base64, hashlib
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
PREFIX=bytes.fromhex("b1479abce2854a37")
CANDIDATES=[
(307588986,"37bfneBLcVoWnqWEoP7Y4EnJREUeaHeEYgnQ9kjBGpsN3tMjP2AceURMpbgQDeR8hmxZ4L5JVSokepJ7WhsuTDnK"),
(307654780,"wDFKuazySEqv1wLuvN6iKp5y58Bzg1xcgEmWNE98LdNbYNKY9ZmM1GP1pRnz7V6qEvzZUiT1qUqKKqsBmFk24Xz"),
(307655792,"YDgTgU9zmdFFAKr3rpm6cPbDBmztE5VYwMC7oHUTYXG9Vca2CmUgERiEN1ySCAMDxy7Co3N5wbfE6vn4v383VFm"),
(307655972,"hujGMDd4Msq23KybuVjysHdTbQXxzhQxGHvLVbKQYZJi5ZRG9vkfJhGuAbDQuFnGujagmCpA3eqX6Zo879DcFkZ"),
(307656000,"2wgkhaBRjTTMDMm3wrPdKxDFXV4FjQY8mXPKRka39zmSQ123sPhZ7tSTYeJ7WEB5FaxXkyra3FiUHhVriFhYWTDx"),
(307656204,"38a1yzB3FBysa98DzPB8gV1A7EaoTNHfpEwhPofkE1kh9ozW3UYjsZrHy3xkbVjjuTQqGY8Hb9ygf15fCKidRNLe"),
(307656452,"3ph7bf59riz5RTZyfTtE2PyXKb7anobGxy9C5tf8fiYRcE7xr1UKw3PFLSLM89M8q9wmAE7KkNZCJd7tCdgxzCB8"),
(307656687,"44dfVdrKZ7NoBzFuvF896zgZtxxCAqG1VXhFDqWcSk54zorfJVgJ4jVrqGJ1RVRxqD2S4NDndNABmRWxLZABKQPz"),
(307657576,"4mfpc3SUHzSJBQN2GZE5LjhKdz2kNxwTYQe8uunobH4ihKcUsSbdrqiNwUDLv9ArJ3Jd3jtQsAfx7BS1QvkFan5f"),
(307657930,"3ztzG4UxD8AbU6yBcjXGqRp9BAaUdfQpfQaxLCNzHtu641uB5mDqDwoWhcKULHjeHnMxRugMHBdRqYSjvbbU2HWS"),
(307658993,"LGnsykEsQbuvBSFEr9hjV68qqi2rsQomZE6vfui5FvDd9rSnqyJwnX86AHjanNkiAYyBHBhZnJekZ9iw5ZWRv5b"),
(307660186,"ku9XjqKJwHLfwJAPsqaKQ6H3sRomKoQeaoNNfQLtTLb4K7eJyJtDnmbfLWcFKFPPuBa8Wuboj9fZt9MVK3mXU1B"),
(307660187,"3JNZKocXEWTPsJa24Ht5rEdAQoXGgLqo4GY2W92PZebZNwzoNU3K2Vjc2anu8SzaV1a7fALwNrwB9rCEZXbZH6qn"),
(307661047,"2wNAt3FvQR8u69A25eh6AxihnmigL9pGLGw7UFaefrZyuU3rFrmr7k2XgnGyXz2d81LdnzuGL75pZrVGci5cxuWU"),
(307672381,"2jxWmhTre9AkwQjU7XhWivXpjHScDGvmcX5sv9yEXQ6ak7jXqaA48hV9fwPZ6hu5TspT3rtfwCZ4XEVZJYgZbVKF"),
(307726904,"2hRxkwdg5eJs9LnwDYPnZYLBZCqEUUMuGpkuqESzLMgEaPhaW6tNUEnJDbLJYqccjNJDS74G6qT8Dap1mRnspJh1"),
]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for c in s:
        n=n*58+MAP[c]
    out=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    pad=len(s)-len(s.lstrip("1"))
    return b"\x00"*pad+out

def rpc(sig):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","maxSupportedTransactionVersion":0,"commitment":"finalized"}]}).encode()
    req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-source-audit/1.0"})
    last=None
    for i in range(5):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            last=repr(e); time.sleep(2*(i+1))
    return {"transport_error":last}

def all_instructions(result):
    out=[]
    tx=result.get("transaction") or {}
    msg=tx.get("message") or {}
    out.extend(msg.get("instructions") or [])
    meta=result.get("meta") or {}
    for group in meta.get("innerInstructions") or []:
        out.extend(group.get("instructions") or [])
    return out

outdir=Path("dls_kamino_public_rpc_rawverify_v01"); outdir.mkdir(exist_ok=True)
rows=[]
for idx,(slot,sig) in enumerate(CANDIDATES):
    obj=rpc(sig)
    (outdir/f"{idx:02d}_{sig}.json").write_text(json.dumps(obj,indent=2,sort_keys=True))
    rec={"index":idx,"signature":sig,"expected_slot":slot}
    if "transport_error" in obj:
        rec.update(status="TRANSPORT_ERROR",detail=obj["transport_error"]); rows.append(rec); continue
    if obj.get("error"):
        rec.update(status="RPC_ERROR",detail=obj["error"]); rows.append(rec); continue
    res=obj.get("result")
    if res is None:
        rec.update(status="RPC_NULL_HISTORY_UNAVAILABLE"); rows.append(rec); continue
    rec["returned_slot"]=res.get("slot")
    rec["slot_match"]=res.get("slot")==slot
    meta=res.get("meta")
    rec["meta_err_null"]=isinstance(meta,dict) and meta.get("err") is None
    found=False
    for ins in all_instructions(res):
        if ins.get("programId")==PROGRAM and isinstance(ins.get("data"),str):
            try:
                raw=b58decode(ins["data"])
            except Exception:
                continue
            if raw.startswith(PREFIX):
                found=True; break
    rec["program_discriminator_match"]=found
    rec["status"]="RAW_VERIFIED_SUCCESSFUL_KAMINO_LIQUIDATION_REFERENCE" if rec["slot_match"] and rec["meta_err_null"] and found else "CONTENT_MISMATCH_FAIL_CLOSED"
    rows.append(rec)
    time.sleep(1)

verified=sum(r["status"].startswith("RAW_VERIFIED") for r in rows)
transport=sum(r["status"] in ("TRANSPORT_ERROR","RPC_ERROR","RPC_NULL_HISTORY_UNAVAILABLE") for r in rows)
mismatch=sum(r["status"]=="CONTENT_MISMATCH_FAIL_CLOSED" for r in rows)
if verified==16:
    classification="KAMINO_SMOKE_RAW_VERIFICATION_PASS"
elif mismatch>0:
    classification="KAMINO_SMOKE_RAW_VERIFICATION_CONTENT_MISMATCH_FAIL_CLOSED"
elif verified>0 and transport>0:
    classification="KAMINO_SMOKE_RAW_VERIFICATION_PARTIAL_TRANSPORT_BLOCKED"
else:
    classification="KAMINO_PUBLIC_RPC_HISTORY_UNAVAILABLE"
summary={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "endpoint":RPC,"candidate_count":16,"verified_count":verified,"transport_blocked_count":transport,"content_mismatch_count":mismatch,
 "rows":rows,
 "firewalls":{"prices_queried":False,"returns_computed":False,"pnl_computed":False,"direction_tested":False,"new_candidate_search":False,"year_2025_2026_market_outcomes":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False}
}
p=outdir/"DLS_KAMINO_PUBLIC_RPC_RAWVERIFY_RECEIPT_V0.1.json"
p.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,indent=2))
