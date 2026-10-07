#!/usr/bin/env python3
import base64, hashlib, json, ssl, urllib.request, urllib.error, time, os
from datetime import datetime, timezone

UA={"User-Agent":"CryptoLab-Unbonding-V03/0.1"}

CHAINS={
 "cosmoshub":{
   "height":20000000,
   "a":"https://rpc.cosmoshub-4-archive.citizenweb3.com",
   "b":"https://rpc.cosmoshub-main.ccvalidators.com",
   "scan_radius":600,
   "completion_upper":21500000,
 },
 "osmosis":{
   "height":15000000,
   "a":"https://rpc.archive.osmosis.zone",
   "b":"https://rpc.archive.osmosis.validatus.com",
   "scan_radius":600,
   "completion_upper":16500000,
 },
 "kava":{
   "height":9500000,
   "a":"https://rpc.data.kava.io",
   "b":"https://kava-rpc.polkachu.com",
   "scan_radius":800,
   "completion_upper":10300000,
 },
 "dydx":{
   "height":15000000,
   "a":"https://dydx-dao-archive-rpc.polkachu.com",
   "b":"https://dydx-ops-archive-rpc.kingnodes.com",
   "scan_radius":800,
   "completion_upper":17500000,
 },
 "secret":{
   "height":17000000,
   "a":"https://rpc.archive.scrt.marionode.com",
   "b":"https://scrt-rpc.blockpane.com",
   "scan_radius":800,
   "completion_upper":19000000,
 },
 "akash":{
   "height":18000000,
   "a":"https://akash-rpc.polkachu.com",
   "b":"https://rpc.akashnet.net",
   "scan_radius":800,
   "completion_upper":20500000,
 }
}

def get_json(url, timeout=12):
    req=urllib.request.Request(url,headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=timeout,context=ssl.create_default_context()) as r:
            return json.loads(r.read().decode()),None
    except Exception as e:
        return None,f"{type(e).__name__}: {e}"

def rpc(base,path):
    return get_json(base.rstrip("/")+"/"+path.lstrip("/"))

def block(base,h):
    j,e=rpc(base,f"block?height={h}")
    if e or not j or not j.get("result"): return None,e or "no result"
    try:
        b=j["result"]["block"]; hdr=b["header"]
        return {
          "height":int(hdr["height"]), "time":hdr["time"],
          "hash":j["result"].get("block_id",{}).get("hash"),
          "txs":(b.get("data") or {}).get("txs") or []
        },None
    except Exception as x: return None,f"parse:{x}"

def block_results(base,h):
    j,e=rpc(base,f"block_results?height={h}")
    if e or not j or not j.get("result"): return None,e or "no result"
    return j["result"],None

def read_varint(buf,i):
    val=0; shift=0
    while True:
        if i>=len(buf): raise ValueError("varint eof")
        b=buf[i]; i+=1
        val |= (b & 0x7f)<<shift
        if not (b&0x80): return val,i
        shift += 7
        if shift>70: raise ValueError("varint overflow")

def fields(buf):
    i=0; out=[]
    while i<len(buf):
        tag,i=read_varint(buf,i); num=tag>>3; wire=tag&7
        if wire==0:
            v,i=read_varint(buf,i); out.append((num,wire,v))
        elif wire==2:
            n,i=read_varint(buf,i); v=buf[i:i+n]; i+=n; out.append((num,wire,v))
        elif wire==1:
            v=buf[i:i+8]; i+=8; out.append((num,wire,v))
        elif wire==5:
            v=buf[i:i+4]; i+=4; out.append((num,wire,v))
        else:
            raise ValueError(f"unsupported wire {wire}")
    return out

def s(b):
    try:return b.decode()
    except:return None

def first_bytes(fs,n):
    for k,w,v in fs:
        if k==n and w==2:return v
    return None

def all_bytes(fs,n):
    return [v for k,w,v in fs if k==n and w==2]

def decode_coin(buf):
    fs=fields(buf)
    return {"denom":s(first_bytes(fs,1) or b""),"amount":s(first_bytes(fs,2) or b"")}

def decode_msg(type_url,val):
    fs=fields(val)
    if type_url.endswith("MsgUndelegate"):
        amount=first_bytes(fs,3)
        return {"type":"MsgUndelegate","delegator":s(first_bytes(fs,1) or b""),
                "validator":s(first_bytes(fs,2) or b""),
                "amount":decode_coin(amount) if amount else None}
    if type_url.endswith("MsgCancelUnbondingDelegation"):
        amount=first_bytes(fs,3)
        creation=None
        for k,w,v in fs:
            if k==4 and w==0: creation=v
        return {"type":"MsgCancelUnbondingDelegation","delegator":s(first_bytes(fs,1) or b""),
                "validator":s(first_bytes(fs,2) or b""),
                "amount":decode_coin(amount) if amount else None,"creation_height":creation}
    if type_url.endswith("MsgBeginRedelegate"):
        amount=first_bytes(fs,4)
        return {"type":"MsgBeginRedelegate","delegator":s(first_bytes(fs,1) or b""),
                "src_validator":s(first_bytes(fs,2) or b""),
                "dst_validator":s(first_bytes(fs,3) or b""),
                "amount":decode_coin(amount) if amount else None}
    return None

def decode_tx(raw_b64):
    raw=base64.b64decode(raw_b64)
    txhash=hashlib.sha256(raw).hexdigest().upper()
    txfs=fields(raw); body=first_bytes(txfs,1)
    msgs=[]
    if body:
        bfs=fields(body)
        for anybuf in all_bytes(bfs,1):
            afs=fields(anybuf)
            t=s(first_bytes(afs,1) or b""); val=first_bytes(afs,2) or b""
            if t:
                m=decode_msg(t,val)
                if m: m["type_url"]=t; msgs.append(m)
    return txhash,msgs

def attr_text(v):
    if v is None:return ""
    if not isinstance(v,str):v=str(v)
    # modern RPCs return plaintext; legacy sometimes base64. Decode only if valid and printable.
    try:
        d=base64.b64decode(v,validate=True)
        ds=d.decode()
        if ds and sum(c.isprintable() for c in ds)/len(ds)>.95:return ds
    except:pass
    return v

def parse_events(events):
    out=[]
    for ev in events or []:
        attrs={}
        for a in ev.get("attributes") or []:
            k=attr_text(a.get("key")); v=attr_text(a.get("value"))
            attrs.setdefault(k,[]).append(v)
        out.append({"type":attr_text(ev.get("type")),"attrs":attrs})
    return out

def completion_time_from_tx_result(br,idx):
    txrs=br.get("txs_results") or []
    if idx>=len(txrs):return None,[]
    evs=parse_events(txrs[idx].get("events"))
    times=[]
    for ev in evs:
        if ev["type"] in ("unbond","delegate","message","coin_spent","coin_received"):
            for k,vals in ev["attrs"].items():
                if "completion" in k.lower():
                    times += vals
    return (times[0] if times else None),evs

def dt(sv):
    if not sv:return None
    try:return datetime.fromisoformat(sv.replace("Z","+00:00")).astimezone(timezone.utc)
    except:return None

def first_block_ge_time(base,lo,hi,target):
    td=dt(target)
    if not td:return None,"bad target time"
    blo,e=block(base,lo); bhi,e2=block(base,hi)
    if not blo or not bhi:return None,{"lo_error":e,"hi_error":e2}
    if dt(blo["time"])>=td or dt(bhi["time"])<td:return None,"target not bracketed"
    while lo+1<hi:
        m=(lo+hi)//2; bm,em=block(base,m)
        if not bm:return None,{"height":m,"error":em}
        if dt(bm["time"])<td:lo=m
        else:hi=m
    bb,e=block(base,hi)
    return bb,e

def find_complete_event(br,needle):
    phases=[]
    for key in ("finalize_block_events","end_block_events","begin_block_events"):
        for ev in parse_events(br.get(key)):
            if "complete_unbond" in ev["type"].lower():
                phases.append({"phase":key,**ev})
    # exact matching if attrs expose addresses/amount; otherwise retain all complete events for receipt.
    matches=[]
    for ev in phases:
        blob=json.dumps(ev,sort_keys=True)
        score=sum(1 for x in [needle.get("delegator"),needle.get("validator"),
                              (needle.get("amount") or {}).get("amount")] if x and x in blob)
        ev2=dict(ev); ev2["match_score"]=score; matches.append(ev2)
    matches.sort(key=lambda x:x["match_score"],reverse=True)
    return matches[:20]

def scan_chain(name,cfg):
    rec={"chain":name,"fixed_height":cfg["height"],"source_a":cfg["a"],"source_b":cfg["b"]}
    ba,ea=block(cfg["a"],cfg["height"]); bb,eb=block(cfg["b"],cfg["height"])
    bra,era=block_results(cfg["a"],cfg["height"]); brb,erb=block_results(cfg["b"],cfg["height"])
    rec["fixed_reconcile"]={
      "a":{"error":ea,"time":ba["time"] if ba else None,"hash":ba["hash"] if ba else None,"block_results_error":era},
      "b":{"error":eb,"time":bb["time"] if bb else None,"hash":bb["hash"] if bb else None,"block_results_error":erb},
      "block_hash_match":bool(ba and bb and ba["hash"]==bb["hash"])
    }
    if not ba or not bra:
        rec["verdict"]="SOURCE_A_FIXED_HEIGHT_FAIL"; return rec

    # bounded scan around fixed historical height, source-only.
    found=None
    for off in range(0,cfg["scan_radius"]+1):
        hs=[cfg["height"]+off]
        if off: hs.append(cfg["height"]-off)
        for h in hs:
            b,e=block(cfg["a"],h)
            if not b:continue
            if not ("2023-" in b["time"] or "2024-" in b["time"]):
                continue
            br,er=block_results(cfg["a"],h)
            if not br:continue
            for idx,raw in enumerate(b["txs"]):
                try:th,msgs=decode_tx(raw)
                except Exception:continue
                for m in msgs:
                    if m["type"]=="MsgUndelegate":
                        ctime,evs=completion_time_from_tx_result(br,idx)
                        if ctime:
                            found={"height":h,"block_time":b["time"],"tx_index":idx,"tx_hash":th,
                                   "msg":m,"completion_time":ctime,
                                   "tx_event_types":[e["type"] for e in evs]}
                            break
                if found:break
            if found:break
        if found:break
        if off and off%100==0:time.sleep(.1)
    rec["undelegate"]=found
    if not found:
        rec["verdict"]="RAW_DECODE_NO_UNDELEGATE_WITH_COMPLETION_IN_BOUNDED_SCAN"; return rec

    # Locate actual maturity boundary from canonical block time.
    comp,e=first_block_ge_time(cfg["a"],found["height"],cfg["completion_upper"],found["completion_time"])
    rec["completion_boundary"]=comp if comp else {"error":e}
    if not comp:
        rec["verdict"]="COMPLETION_TIME_NOT_BRACKETED"; return rec
    # inspect a tight canonical window because EndBlock/finalize semantics can land at >= comparison boundary.
    ce=[]
    for h in range(max(found["height"],comp["height"]-2),comp["height"]+5):
        br,er=block_results(cfg["a"],h)
        if br:
            ms=find_complete_event(br,found["msg"])
            if ms: ce.append({"height":h,"events":ms})
    rec["complete_unbonding_candidates"]=ce

    # Source B corroboration exactly at initiation and completion boundary.
    b_init,ebi=block(cfg["b"],found["height"])
    b_comp,ebc=block(cfg["b"],comp["height"])
    br_comp_b,erbc=block_results(cfg["b"],comp["height"])
    rec["source_b_corroboration"]={
      "init_error":ebi,"init_hash_match":bool(b_init and b_init["hash"]==block(cfg["a"],found["height"])[0]["hash"]),
      "completion_error":ebc,"completion_hash_match":bool(b_comp and b_comp["hash"]==comp["hash"]),
      "completion_results_error":erbc,
      "completion_events":find_complete_event(br_comp_b,found["msg"]) if br_comp_b else []
    }
    rec["verdict"]="RAW_LIFECYCLE_CAPABILITY_PASS" if ce and b_init and b_comp else "PARTIAL_RAW_LIFECYCLE_CAPABILITY"
    return rec

report={"generated_at":datetime.now(timezone.utc).isoformat(),"market_outcomes_opened":False,"chains":{}}
for name,cfg in CHAINS.items():
    only=os.environ.get("ONLY_CHAIN")
    if only and name != only:
        continue
    try: report["chains"][name]=scan_chain(name,cfg)
    except Exception as e: report["chains"][name]={"chain":name,"verdict":"SCRIPT_EXCEPTION","error":f"{type(e).__name__}: {e}"}

print("===UNBONDING_V03_CAPABILITY_JSON===")
print(json.dumps(report,indent=2,sort_keys=True))
outfile="unbonding_v03_capability_" + os.environ.get("ONLY_CHAIN","all") + ".json"
with open(outfile,"w") as f:json.dump(report,f,indent=2,sort_keys=True)
