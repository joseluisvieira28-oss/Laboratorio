#!/usr/bin/env python3
import datetime as dt,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
D8="5f6f7c6956a9bb22"
START="2022-11-04T15:17:54Z"
END="2025-01-01T00:00:00Z"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_WITH_FILL_CENSUS_RECEIPT_V0.1.json")
ROWS=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_WITH_FILL_CENSUS_V0.1.ndjson")

def iso(s):return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-drift-with-fill/0.1"}
    if data is not None:h["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(60,2**i));continue
            return int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:220]};time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    st,raw=req(f"{TSROOT}/{int(iso(s).timestamp())}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    for k in ("block","block_number","number","slot"):
        if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

lo=int(iso(START).timestamp());hi=int(iso(END).timestamp())
current=ts_slot(START);to=ts_slot(END)+16
rows=[];requests=0;terminations=[];anomalies=[]
while current<=to:
    body={"type":"solana","fromBlock":current,"toBlock":to,
      "fields":{"block":{"number":True,"timestamp":True},
                "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                "instruction":{"programId":True,"data":True,"transactionIndex":True,
                  "instructionAddress":True,"isCommitted":True,"error":True}},
      "instructions":[{"programId":[PROGRAM],"d8":["0x"+D8],"transaction":True}]}
    st,raw=req(STREAM,body);requests+=1
    if st==204:
        terminations.append({"http_status":204,"from_slot":current});break
    if st!=200:raise RuntimeError(f"stream_http_{st}")
    docs=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
    if not docs:
        terminations.append({"http_status":200,"from_slot":current,"reason":"empty_ndjson"});break
    last=None
    for b in docs:
        hdr=b.get("header") or {};slot=hdr.get("number");ts=hdr.get("timestamp")
        if isinstance(slot,int):last=slot if last is None else max(last,slot)
        if isinstance(ts,(int,float)):ts=dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat().replace("+00:00","Z")
        if not isinstance(ts,str):continue
        try:bt=int(iso(ts).timestamp())
        except Exception:continue
        if not(lo<=bt<hi):continue
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM:continue
            data=ix.get("data") or ""
            # SQD d8 filter is authority; retain raw source data for audit.
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict):
                anomalies.append({"reason":"missing_parent_transaction","slot":slot});continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            addr=ix.get("instructionAddress")
            if not sig or not isinstance(addr,list):
                anomalies.append({"reason":"bad_identity","slot":slot});continue
            if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:
                continue
            # Decode first bytes from base58 only to re-prove discriminator + market index.
            alpha="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";mp={c:i for i,c in enumerate(alpha)}
            try:
                n=0
                for ch in data:n=n*58+mp[ch]
                dec=(b"\x00"*(len(data)-len(data.lstrip("1"))) + (n.to_bytes((n.bit_length()+7)//8,"big") if n else b""))
            except Exception:
                anomalies.append({"reason":"instruction_base58_decode_failed","signature":sig,"instructionAddress":addr});continue
            if len(dec)<10 or dec[:8].hex()!=D8:
                anomalies.append({"reason":"d8_reconciliation_conflict","signature":sig,"instructionAddress":addr,"len":len(dec),"prefix":dec[:8].hex()});continue
            rows.append({"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,
                         "transactionIndex":ti,"instruction_data_base58":data,
                         "instruction_data_byte_length":len(dec),"market_index":int.from_bytes(dec[8:10],"little")})
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1

ded={};conflicts=[]
for r in rows:
    k=r["signature"]+"|"+json.dumps(r["instructionAddress"],separators=(",",":"))
    if k in ded and ded[k]!=r:conflicts.append({"reason":"dedup_conflict","key":k})
    ded[k]=r
rows=sorted(ded.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"],json.dumps(r["instructionAddress"],separators=(",",":"))))
with ROWS.open("w") as f:
    for r in rows:f.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")
errors=anomalies+conflicts
if errors:classification="DRIFT_WITH_FILL_CENSUS_BLOCKED"
elif rows:classification="DRIFT_WITH_FILL_CENSUS_PASS"
else:classification="DRIFT_WITH_FILL_CENSUS_ZERO"
by_market={}
for r in rows:by_market[str(r["market_index"])]=by_market.get(str(r["market_index"]),0)+1
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "discriminator_hex":D8,"window":{"start":START,"end_exclusive":END},"realized_count":len(rows),
 "market_index_counts":by_market,"request_count":requests,"terminations":terminations,
 "error_count":len(errors),"errors":errors[:200],
 "census_file":str(ROWS),"census_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"market_2025_opened":False,"market_2026_opened":False,
  "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"realized_count":len(rows),"market_index_counts":by_market,"error_count":len(errors)},indent=2))
if classification=="DRIFT_WITH_FILL_CENSUS_BLOCKED":raise SystemExit(2)
