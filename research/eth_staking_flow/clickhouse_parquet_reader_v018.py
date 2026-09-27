#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, subprocess, sys, urllib.parse
from pathlib import Path

BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
IMAGE="clickhouse/clickhouse-server:25.8"

CONTROLS={
 "2025-02-24": {"epoch":347738,"unix":1740355415,"pending":0,"exiting":5,"net":-5},
 "2025-03-02": {"epoch":349088,"unix":1740873815,"pending":0,"exiting":0,"net":0},
 "2025-10-17": {"epoch":400613,"unix":1760659415,"pending":48,"exiting":55209,"net":-55161},
}
MISSING={
 "2025-02-25":347963,"2025-02-26":348188,"2025-02-27":348413,
 "2025-02-28":348638,"2025-03-01":348863,"2025-10-18":400838,"2025-10-19":401063,
}

def url_for(d):
    y,m,dd=d.split("-")
    return f"{BASE}/{y}/{int(m)}/{int(dd)}/0.parquet"

def ch(query):
    p=subprocess.run(
        ["docker","run","--rm",IMAGE,"clickhouse","local","--query",query],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=240,
    )
    return p.returncode,p.stdout.strip(),p.stderr.strip()

def read_one(d):
    u=url_for(d)
    q=f"""
WITH (SELECT min(epoch_start_date_time) FROM url('{u}','Parquet')) AS t
SELECT
  toUnixTimestamp(t),
  uniqExact(epoch),
  min(epoch),
  count(),
  countIf(isNull(`index`)),
  uniqExact(`index`),
  countIf(status='pending_queued'),
  countIf(status='active_exiting')
FROM url('{u}','Parquet')
WHERE epoch_start_date_time=t
FORMAT TSVRaw
""".strip()
    rc,out,err=ch(q)
    rec={"date":d,"url":u,"rc":rc,"stderr":err[:2000]}
    if rc!=0 or not out:
        rec["error"]="CLICKHOUSE_READ_FAILURE"
        return rec
    parts=out.split("\t")
    if len(parts)!=8:
        rec["error"]="UNEXPECTED_OUTPUT_SHAPE"
        rec["stdout"]=out[:2000]
        return rec
    try:
        unix,epoch_distinct,epoch_min,row_count,null_idx,uniq_idx,pending,exiting=map(int,parts)
    except Exception as e:
        rec["error"]=f"PARSE_FAILURE:{type(e).__name__}"
        rec["stdout"]=out[:2000]
        return rec
    rec.update(
        selected_unix_time=unix,
        distinct_epoch_count=epoch_distinct,
        selected_epoch=epoch_min,
        row_count=row_count,
        null_index_count=null_idx,
        unique_index_count=uniq_idx,
        pending_queued_count=pending,
        active_exiting_count=exiting,
        net_queue_count=pending-exiting,
    )
    midnight=int(dt.datetime.fromisoformat(d).replace(tzinfo=dt.timezone.utc).timestamp())
    rec["time_geometry_pass"]=midnight <= unix <= midnight+384
    rec["integrity_pass"]=(row_count>0 and null_idx==0 and uniq_idx==row_count and epoch_distinct==1)
    return rec

def main():
    receipt={
      "lab_id":"ETH-STAKING-FLOW-001",
      "stage":"V3_STAGEA_CLICKHOUSE_PARQUET_READER_V0_1_8",
      "engine":{"image":IMAGE},
      "source_only":True,
      "market_data_opened":False,
      "signal_evaluated":False,
      "returns_opened":False,
      "pnl_opened":False,
      "source_after_2026_08_31_opened":False,
      "controls":[],
      "missing_dates":[],
    }
    rc,img,err=ch("SELECT version() FORMAT TSVRaw")
    receipt["engine"]["version_probe_rc"]=rc
    receipt["engine"]["version"]=img
    receipt["engine"]["version_stderr"]=err[:1000]
    if rc!=0:
        receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        return write(receipt,2)

    controls_ok=True
    for d,exp in CONTROLS.items():
        r=read_one(d)
        if "error" not in r:
            r["expected"]=exp
            r["exact_control_pass"]=(
                r["selected_epoch"]==exp["epoch"] and
                r["selected_unix_time"]==exp["unix"] and
                r["pending_queued_count"]==exp["pending"] and
                r["active_exiting_count"]==exp["exiting"] and
                r["net_queue_count"]==exp["net"] and
                r["time_geometry_pass"] and r["integrity_pass"]
            )
        else:
            r["exact_control_pass"]=False
        receipt["controls"].append(r)
        controls_ok = controls_ok and r["exact_control_pass"]

    receipt["control_exact_count"]=sum(1 for x in receipt["controls"] if x.get("exact_control_pass"))
    if not controls_ok:
        # A readable-but-mismatching control is provenance failure; unreadable is technical failure.
        readable=all("error" not in x for x in receipt["controls"])
        receipt["classification"]="SOURCE_PROVENANCE_FAILURE" if readable else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        return write(receipt,2)

    missing_ok=True
    for d,ep in MISSING.items():
        r=read_one(d)
        if "error" not in r:
            r["expected_epoch"]=ep
            r["recovery_pass"]=(
                r["selected_epoch"]==ep and r["time_geometry_pass"] and r["integrity_pass"]
            )
        else:
            r["recovery_pass"]=False
        receipt["missing_dates"].append(r)
        missing_ok = missing_ok and r["recovery_pass"]

    receipt["recovered_missing_date_count"]=sum(1 for x in receipt["missing_dates"] if x.get("recovery_pass"))
    receipt["classification"]="CLICKHOUSE_PARQUET_RECOVERY_PASS" if missing_ok else (
        "SOURCE_PROVENANCE_FAILURE" if all("error" not in x for x in receipt["missing_dates"]) else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    )
    return write(receipt,0 if missing_ok else 2)

def write(x,code):
    out=Path("artifacts/ETH_STAKING_FLOW_001_CLICKHOUSE_PARQUET_RECOVERY_V0_1_8.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    print(json.dumps(x,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
