#!/usr/bin/env python3
import hashlib, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BLOCK=18433832
ADDRESS="0xbd3fa81b58ba92a82136038b25adec7066af3155"
TOPIC="0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6"
OUT=Path("artifacts/cclm_cctp_v1_sqd_archive_probe_v04.json")

QUERY={
  "type":"evm",
  "fromBlock":BLOCK,
  "toBlock":BLOCK,
  "fields":{
    "block":{"number":True,"timestamp":True,"hash":True},
    "log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
  },
  "logs":[{
    "address":[ADDRESS],
    "topic0":[TOPIC]
  }]
}

def request(url, payload=None, timeout=60):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-CCLM-001-SQD/0.4"},
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read()
        return r.status, dict(r.headers), raw

def parse_any(raw):
    text=raw.decode("utf-8","replace").strip()
    if not text:return None
    try:return json.loads(text)
    except Exception:
        # streaming endpoints can produce NDJSON
        rows=[]
        for line in text.splitlines():
            line=line.strip()
            if not line:continue
            try:rows.append(json.loads(line))
            except Exception:pass
        return rows if rows else None

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def exact_logs(x):
    out=[]
    for d in walk(x):
        addr=d.get("address")
        topics=d.get("topics")
        bn=d.get("blockNumber",d.get("block_number"))
        if isinstance(bn,str):
            try:bn=int(bn,16) if bn.startswith("0x") else int(bn)
            except:bn=None
        if addr and str(addr).lower()==ADDRESS and isinstance(topics,list) and topics and str(topics[0]).lower()==TOPIC:
            # Some archive responses nest log under a known block object and omit blockNumber.
            out.append({
                "address":str(addr).lower(),
                "topics":topics,
                "data_sha256":hashlib.sha256(str(d.get("data","")).encode()).hexdigest(),
                "transaction_hash":d.get("transactionHash") or d.get("transaction_hash"),
                "log_index":d.get("logIndex") or d.get("log_index"),
                "explicit_block_number":bn,
            })
    return out

attempts=[]
matched=[]

# Route 1: current Portal
try:
    status,headers,raw=request("https://portal.sqd.dev/datasets/ethereum-mainnet/stream",QUERY)
    parsed=parse_any(raw)
    logs=exact_logs(parsed)
    attempts.append({"route":"portal.sqd.dev","status":status,"raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw),"exact_log_count":len(logs)})
    if logs:matched=logs
except Exception as e:
    attempts.append({"route":"portal.sqd.dev","error":f"{type(e).__name__}:{str(e)[:400]}"})

# Route 2: legacy v2 only if current route did not prove the fixture
if not matched:
    try:
        status,headers,raw=request(f"https://v2.archive.subsquid.io/network/eth-mainnet/{BLOCK}/worker")
        worker=parse_any(raw)
        if isinstance(worker,dict):
            worker_url=worker.get("url") or worker.get("worker")
        elif isinstance(worker,str):
            worker_url=worker
        else:
            worker_url=None
        if not worker_url:
            # router historically may return raw URL text
            txt=raw.decode("utf-8","replace").strip().strip('"')
            worker_url=txt if txt.startswith("http") else None
        if not worker_url:raise RuntimeError("NO_WORKER_URL")
        legacy_query={
          "fromBlock":BLOCK,
          "toBlock":BLOCK,
          "logs":[{"address":[ADDRESS],"topic0":[TOPIC],"transaction":True}],
          "fields":{"block":{"number":True,"timestamp":True},"log":{"address":True,"topics":True,"data":True},"transaction":{"hash":True}}
        }
        s2,h2,r2=request(worker_url,legacy_query)
        parsed=parse_any(r2)
        logs=exact_logs(parsed)
        attempts.append({"route":"v2.archive.subsquid.io","router_status":status,"worker_status":s2,"worker_url_sha256":hashlib.sha256(worker_url.encode()).hexdigest(),"raw_sha256":hashlib.sha256(r2).hexdigest(),"raw_bytes":len(r2),"exact_log_count":len(logs)})
        if logs:matched=logs
    except Exception as e:
        attempts.append({"route":"v2.archive.subsquid.io","error":f"{type(e).__name__}:{str(e)[:400]}"})

receipt={
 "lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001",
 "child_id":"CCLM-CCTP-USDC-001",
 "stage":"CCTP_V1_ETHEREUM_SQD_ARCHIVE_PROBE_V0.4",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "fixture":{"block":BLOCK,"address":ADDRESS,"topic0":TOPIC},
 "classification":"HISTORICAL_ETHEREUM_ARCHIVE_DATALAKE_PASS" if matched else "SOURCE_ACCESS_BLOCKED_FREE_ETHEREUM_ARCHIVE_DATALAKE",
 "attempts":attempts,
 "matched_logs":matched,
 "market_outcomes_opened":False,
 "pnl_opened":False,
 "mutation":False,
 "access_2025":False,
 "access_2026":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
