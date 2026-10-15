#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

LAB_ID="TV-FOOTPRINT-CALIBRATION-001"
SENSOR_VERSION="MM-V1"
SYMBOL="BINANCE:BTCUSDT"
TIMEFRAME="5"
BAR_MS=300000
FORWARD_START_MS=1790247600000
MAX_RECEIPT_LATENCY_MS=300000

EXPECTED_KEYS={
 "lab_id","sensor_version","symbol","timeframe","bar_open_ms","bar_close_ms","close",
 "tv_total_volume","tv_buy_volume","tv_sell_volume","tv_delta","tv_delta_pct",
 "poc_mid","poc_migration_bps","vah","val","buy_imbalance_rows",
 "sell_imbalance_rows","footprint_rows","ltf_intrabars","ltf_path_efficiency",
 "ltf_signed_volume_pct","volume_z","bar_return_bps","eth_ret","sol_ret",
 "cme_btc_ret","ndx_ret","dxy_ret"
}

class SentinelError(ValueError): pass

def canon(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()

def sha(obj):
    return hashlib.sha256(canon(obj)).hexdigest()

def finite_or_none(v):
    return v is None or (isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v))

def close(a,b,rtol=1e-6,atol=1e-8):
    return abs(a-b) <= max(atol, rtol*max(abs(a),abs(b),1.0))

def parse_dt_ms(s):
    dt=datetime.fromisoformat(s.replace("Z","+00:00"))
    return int(dt.timestamp()*1000)

def validate_record(rec):
    issues=[]
    hard=[]

    p=rec.get("payload")
    if not isinstance(p,dict):
        return {"eligible":False,"hard":["PAYLOAD_MISSING"],"soft":[]}

    if set(p)!=EXPECTED_KEYS:
        hard.append("SCHEMA_FINGERPRINT_MISMATCH")

    exp={"lab_id":LAB_ID,"sensor_version":SENSOR_VERSION,"symbol":SYMBOL,"timeframe":TIMEFRAME}
    for k,v in exp.items():
        if p.get(k)!=v: hard.append(f"IDENTITY_{k.upper()}_MISMATCH")

    if rec.get("trading_authority")!="NONE":
        hard.append("TRADING_AUTHORITY_NOT_NONE")

    if rec.get("payload_sha256")!=sha(p):
        hard.append("PAYLOAD_SHA256_MISMATCH")

    bo=p.get("bar_open_ms"); bc=p.get("bar_close_ms")
    if not isinstance(bo,int) or not isinstance(bc,int):
        hard.append("BAR_TIMESTAMP_TYPE")
    else:
        if bo % BAR_MS != 0 or bc-bo != BAR_MS: hard.append("BAR_ALIGNMENT")
        if bc < FORWARD_START_MS: hard.append("PRE_FORWARD_BAR")

    for k in EXPECTED_KEYS-{"lab_id","sensor_version","symbol","timeframe","bar_open_ms","bar_close_ms","buy_imbalance_rows","sell_imbalance_rows","footprint_rows","ltf_intrabars"}:
        if not finite_or_none(p.get(k)): hard.append(f"NONFINITE_{k.upper()}")

    for k in ("buy_imbalance_rows","sell_imbalance_rows","footprint_rows","ltf_intrabars"):
        if not isinstance(p.get(k),int) or isinstance(p.get(k),bool):
            hard.append(f"INTEGER_{k.upper()}")

    total=p.get("tv_total_volume"); buy=p.get("tv_buy_volume"); sell=p.get("tv_sell_volume")
    delta=p.get("tv_delta"); dp=p.get("tv_delta_pct")
    if all(isinstance(x,(int,float)) for x in (total,buy,sell,delta)):
        if min(total,buy,sell)<0: hard.append("NEGATIVE_TV_VOLUME")
        if not close(buy+sell,total): hard.append("TV_VOLUME_RECONCILIATION")
        if not close(buy-sell,delta): hard.append("TV_DELTA_RECONCILIATION")
        if total>0 and isinstance(dp,(int,float)) and not close(delta/total,dp):
            hard.append("TV_DELTA_PCT_RECONCILIATION")

    val=p.get("val"); poc=p.get("poc_mid"); vah=p.get("vah")
    if all(isinstance(x,(int,float)) for x in (val,poc,vah)) and not (val <= poc <= vah):
        hard.append("VALUE_AREA_POC_INVARIANT")

    rows=p.get("footprint_rows"); bi=p.get("buy_imbalance_rows"); si=p.get("sell_imbalance_rows")
    if all(isinstance(x,int) for x in (rows,bi,si)):
        if rows<0 or bi<0 or si<0: hard.append("NEGATIVE_ROW_COUNT")
        if bi>rows or si>rows: hard.append("IMBALANCE_EXCEEDS_ROWS")

    eff=p.get("ltf_path_efficiency")
    if isinstance(eff,(int,float)) and not (0 <= eff <= 1):
        hard.append("LTF_PATH_EFFICIENCY_RANGE")

    ltf=p.get("ltf_intrabars")
    if isinstance(ltf,int):
        if not (0 <= ltf <= 5): hard.append("LTF_INTRABARS_RANGE")
        elif ltf != 5: issues.append("LTF_INTRABARS_INCOMPLETE")

    try:
        latency=parse_dt_ms(rec["received_at"])-bc
        if latency < -5000: hard.append("NEGATIVE_RECEIPT_LATENCY")
        elif latency > MAX_RECEIPT_LATENCY_MS: issues.append("RECEIPT_LATE_OVER_5M")
    except Exception:
        hard.append("RECEIVED_AT_INVALID")

    return {"eligible":not hard and not issues,"hard":sorted(set(hard)),"soft":sorted(set(issues))}

def audit(records):
    by_key={}
    hard_global=[]
    duplicate_retries=0

    for rec in records:
        k=rec.get("evidence_key")
        if not isinstance(k,str):
            hard_global.append("EVIDENCE_KEY_MISSING"); continue
        if k in by_key:
            if by_key[k].get("payload_sha256")==rec.get("payload_sha256"):
                duplicate_retries += 1
                continue
            hard_global.append("CONFLICTING_DUPLICATE_KEY")
        else:
            by_key[k]=rec

    rows=sorted(by_key.values(),key=lambda r:r["payload"]["bar_close_ms"])
    per=[]
    for r in rows:
        per.append((r,validate_record(r)))

    gaps=[]
    if rows:
        closes=[r["payload"]["bar_close_ms"] for r in rows]
        have=set(closes)
        for x in range(closes[0],closes[-1]+BAR_MS,BAR_MS):
            if x not in have: gaps.append(x)

    hard_count=sum(bool(v["hard"]) for _,v in per)
    degraded_count=sum(bool(v["soft"]) for _,v in per)
    eligible=sum(v["eligible"] for _,v in per)

    status="PASS"
    reasons=[]
    if hard_global or hard_count:
        status="FAIL_CLOSED"
        reasons=sorted(set(hard_global+[x for _,v in per for x in v["hard"]]))
    elif gaps or degraded_count:
        status="DEGRADED"
        if gaps: reasons.append("MISSING_5M_SLOTS")
        reasons+=sorted(set(x for _,v in per for x in v["soft"]))

    latencies=[]
    for r,_ in per:
        try: latencies.append(parse_dt_ms(r["received_at"])-r["payload"]["bar_close_ms"])
        except Exception: pass

    return {
      "sentinel_id":"TV-SENSOR-ANOMALY-SENTINEL-V0.1",
      "status":status,
      "reasons":reasons,
      "unique_receipts":len(rows),
      "eligible_receipts":eligible,
      "hard_invalid_receipts":hard_count,
      "degraded_receipts":degraded_count,
      "exact_duplicate_retries":duplicate_retries,
      "missing_slots":len(gaps),
      "missing_bar_close_ms":gaps,
      "first_bar_close_ms":rows[0]["payload"]["bar_close_ms"] if rows else None,
      "last_bar_close_ms":rows[-1]["payload"]["bar_close_ms"] if rows else None,
      "max_receipt_latency_ms":max(latencies) if latencies else None,
      "schema_fingerprint_sha256":hashlib.sha256("\n".join(sorted(EXPECTED_KEYS)).encode()).hexdigest(),
      "calibration_authority":"NONE",
      "trading_authority":"NONE"
    }

def load(path):
    out=[]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        obj=json.loads(line)
        if isinstance(obj,dict) and "message" in obj and "TVFP_RECEIPT " in obj["message"]:
            out.append(json.loads(obj["message"].split("TVFP_RECEIPT ",1)[1]))
        elif isinstance(obj,dict) and obj.get("record_type")=="TVFP_RECEIPT":
            out.append(obj)
        elif isinstance(obj,dict) and "payload" in obj and "payload_sha256" in obj:
            obj={"record_type":"TVFP_RECEIPT",**obj}
            out.append(obj)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out")
    args=ap.parse_args()
    result=audit(load(args.input))
    s=json.dumps(result,indent=2,sort_keys=True)
    print(s)
    if args.out: Path(args.out).write_text(s+"\n",encoding="utf-8")
    if result["status"]=="FAIL_CLOSED": raise SystemExit(2)

if __name__=="__main__": main()
