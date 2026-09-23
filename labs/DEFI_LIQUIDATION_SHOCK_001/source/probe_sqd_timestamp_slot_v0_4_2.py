#!/usr/bin/env python3
import json, time, urllib.request, urllib.error, datetime as dt
from pathlib import Path

TS_BASE="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_TIMESTAMP_SLOT_PROBE_RECEIPT_V0.4.2.json")

controls=[
  {"name":"kamino_first_success","ts":1700232504,"expected_event_slot":230572965},
  {"name":"save11_first_success","ts":1721417452,"expected_event_slot":278496102},
  {"name":"window_end","ts":1735689600,"expected_event_slot":None},
]

def req_get(url,retries=8):
    last=None
    for i in range(retries):
        try:
            r=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-dls-sqd-ts/0.4.2"})
            with urllib.request.urlopen(r,timeout=45) as resp:
                return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            body=e.read().decode("utf-8","replace")
            last={"http":e.code,"body":body[:500]}
            if e.code in (429,529) or 500<=e.code<600:
                time.sleep(min(30,2**i)); continue
            return int(e.code),dict(e.headers),body
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(30,2**i))
    raise RuntimeError(f"get_exhausted:{last}")

def req_post(body,retries=8):
    raw=json.dumps(body,separators=(",",":")).encode()
    last=None
    for i in range(retries):
        try:
            r=urllib.request.Request(STREAM,data=raw,method="POST",headers={
              "Content-Type":"application/json","Accept":"application/x-ndjson,application/json",
              "User-Agent":"crypto-lab-dls-sqd-ts/0.4.2"})
            with urllib.request.urlopen(r,timeout=60) as resp:
                return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            bodytxt=e.read().decode("utf-8","replace")
            last={"http":e.code,"body":bodytxt[:500]}
            if e.code in (429,529) or 500<=e.code<600:
                time.sleep(min(30,2**i)); continue
            return int(e.code),dict(e.headers),bodytxt
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(30,2**i))
    raise RuntimeError(f"post_exhausted:{last}")

def unix(v):
    if isinstance(v,(int,float)): return int(v)
    if isinstance(v,str):
        try: return int(dt.datetime.fromisoformat(v.replace("Z","+00:00")).timestamp())
        except Exception: return None
    return None

def resolve(target):
    status,h,txt=req_get(f"{TS_BASE}/{target}/block")
    if status!=200:
        return {"ok":False,"stage":"seed","http_status":status,"body":txt[:500]}
    try: obj=json.loads(txt)
    except Exception as e:
        return {"ok":False,"stage":"seed_parse","detail":str(e),"raw":txt[:500]}
    seed=obj.get("block_number")
    if not isinstance(seed,int):
        return {"ok":False,"stage":"seed_shape","parsed":obj}

    body={
      "type":"solana","fromBlock":seed,"toBlock":seed+64,
      "fields":{"block":{"number":True,"timestamp":True}}
    }
    st,hh,nd=req_post(body)
    if st not in (200,204):
        return {"ok":False,"stage":"stream","seed":seed,"http_status":st,"body":nd[:500]}
    blocks=[]
    if st==200:
        for line in nd.splitlines():
            if not line.strip(): continue
            try: b=json.loads(line)
            except Exception as e:
                return {"ok":False,"stage":"stream_parse","seed":seed,"detail":str(e),"line":line[:300]}
            hdr=b.get("header") or {}
            n=hdr.get("number")
            t=unix(hdr.get("timestamp"))
            if isinstance(n,int) and isinstance(t,int):
                blocks.append((n,t))
    blocks.sort()
    selected=next(((n,t) for n,t in blocks if t>=target),None)
    if selected is None:
        return {"ok":False,"stage":"no_first_block_ge_target","seed":seed,"block_count":len(blocks),
                "last":blocks[-1] if blocks else None}
    return {
      "ok":True,"seed_block":seed,"selected_slot":selected[0],"selected_timestamp":selected[1],
      "stream_block_count":len(blocks),"x_sqd_data_source":hh.get("x-sqd-data-source")
    }

rows=[]
for c in controls:
    try:
        r=resolve(c["ts"])
    except Exception as e:
        r={"ok":False,"stage":"exception","error":type(e).__name__,"detail":str(e)[:500]}
    r.update({"name":c["name"],"target_timestamp":c["ts"],"expected_event_slot":c["expected_event_slot"]})
    if r.get("ok") and c["expected_event_slot"] is not None:
        r["known_boundary_consistent"]=(
          r["selected_timestamp"]>=c["ts"] and
          r["selected_slot"]<=c["expected_event_slot"] and
          c["expected_event_slot"]-r["selected_slot"]<=64
        )
    rows.append(r)

known_ok=all(r.get("ok") and r.get("known_boundary_consistent") for r in rows[:2])
end_ok=rows[2].get("ok") and isinstance(rows[2].get("selected_slot"),int)
classification="SQD_TIMESTAMP_SLOT_RESOLVER_PASS" if known_ok and end_ok else "SQD_TIMESTAMP_SLOT_RESOLVER_FAIL_CLOSED"

receipt={
 "schema_version":"0.4.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,"rows":rows,
 "firewall":{
  "prices":False,"balances":False,"token_balances":False,"amounts":False,
  "transactions":False,"instructions":False,"returns":False,"pnl":False,
  "direction":False,"economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
  "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
  "paid_source":False,"account_creation":False,"merge_main":False
 }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="SQD_TIMESTAMP_SLOT_RESOLVER_PASS":
    raise SystemExit(2)
