#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, datetime as dt, hashlib, json, math, re, statistics, zipfile
from pathlib import Path

try:
    import lz4.frame
except Exception as e:
    raise SystemExit("Missing dependency 'lz4'. The existing validation environment already requires it.") from e

LAB_ID="L2-RESILIENCY-001"
DEFAULT_KEY="market_data/20250101/4/l2Book/BTC.lz4"
EXPECTED_RAW_SHA256="248d0f9f4e3eff470520af97908ca299f34314c97a29a0fac650285d4d705093"
ISO_RE=re.compile(r"^(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2})(?:\\.(\\d+))?Z?$")

def default_base() -> Path:
    return Path.home()/"Desktop"/"L2R_2025_BTC_VALIDATION_LOCAL"

def parse_env_ns(value: str) -> int:
    if not isinstance(value,str):
        raise RuntimeError("envelope time must be string")
    m=ISO_RE.fullmatch(value.strip())
    if not m:
        raise RuntimeError(f"invalid envelope timestamp: {value!r}")
    base,frac=m.groups()
    d=dt.datetime.strptime(base,"%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    ns=((frac or "")+"000000000")[:9]
    return int(d.timestamp())*1_000_000_000+int(ns)

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def percentile(xs,p):
    if not xs: return None
    ys=sorted(xs)
    if len(ys)==1: return ys[0]
    h=(len(ys)-1)*p
    lo=int(math.floor(h)); hi=int(math.ceil(h))
    if lo==hi: return ys[lo]
    f=h-lo
    return ys[lo]*(1-f)+ys[hi]*f

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path,default=default_base())
    ap.add_argument("--key",default=DEFAULT_KEY)
    args=ap.parse_args()

    base=args.base.resolve()
    raw=base/"HL_L2R_2025_BTC_RAW_V0_1"/Path(*args.key.split("/"))
    ev=base/"_EVIDENCE_2025_VALIDATION_V0_1"
    ev.mkdir(parents=True,exist_ok=True)
    receipt=ev/"L2_RESILIENCY_001_2025_SOURCE_CLOCK_DIAGNOSTIC_V0_1.json"
    samples=ev/"L2_RESILIENCY_001_2025_SOURCE_CLOCK_POSITIVE_SKEW_SAMPLE_V0_1.csv"
    bundle=base/"L2_RESILIENCY_001_2025_SOURCE_CLOCK_DIAGNOSTIC_V0_1.zip"

    if not raw.exists():
        raise SystemExit(f"Raw object not found: {raw}")

    observed_sha=sha256_file(raw)
    if args.key==DEFAULT_KEY and observed_sha!=EXPECTED_RAW_SHA256:
        raise SystemExit(f"FAIL CLOSED: offending object SHA256 mismatch: {observed_sha}")

    dec=lz4.frame.LZ4FrameDecompressor()
    pending=b""
    rows=0
    positive=0; zero=0; negative=0
    deltas_ns=[]
    pos_examples=[]
    env_backwards=0
    payload_rewinds=0
    last_env=None; last_payload=None

    with raw.open("rb") as f:
        while True:
            b=f.read(1024*1024)
            if not b: break
            out=dec.decompress(b)
            if not out: continue
            pending+=out
            parts=pending.split(b"\\n"); pending=parts.pop()
            for line in parts:
                if not line.strip(): continue
                o=json.loads(line)
                env=parse_env_ns(o["time"])
                rawmsg=o.get("raw")
                if not isinstance(rawmsg,dict) or rawmsg.get("channel")!="l2Book":
                    raise RuntimeError("wrong raw/channel")
                data=rawmsg.get("data")
                if not isinstance(data,dict) or data.get("coin")!="BTC":
                    raise RuntimeError("wrong data/coin")
                payload=data.get("time")
                if isinstance(payload,bool) or not isinstance(payload,int):
                    raise RuntimeError("payload time not integer ms")

                rows+=1
                delta=payload*1_000_000-env
                deltas_ns.append(delta)
                if delta>0:
                    positive+=1
                    if len(pos_examples)<50:
                        pos_examples.append({
                            "record_index_1based":rows,
                            "envelope_time":o["time"],
                            "payload_ms":payload,
                            "delta_ns":delta,
                            "delta_ms":delta/1_000_000.0,
                        })
                elif delta==0:
                    zero+=1
                else:
                    negative+=1

                if last_env is not None and env<last_env:
                    env_backwards+=1
                if last_payload is not None and payload<last_payload:
                    payload_rewinds+=1
                last_env=env; last_payload=payload

    if pending.strip():
        o=json.loads(pending)
        env=parse_env_ns(o["time"]); payload=o["raw"]["data"]["time"]
        rows+=1; delta=payload*1_000_000-env; deltas_ns.append(delta)
        if delta>0:
            positive+=1
            if len(pos_examples)<50:
                pos_examples.append({"record_index_1based":rows,"envelope_time":o["time"],"payload_ms":payload,"delta_ns":delta,"delta_ms":delta/1_000_000.0})
        elif delta==0: zero+=1
        else: negative+=1
        if last_env is not None and env<last_env: env_backwards+=1
        if last_payload is not None and payload<last_payload: payload_rewinds+=1

    with samples.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["record_index_1based","envelope_time","payload_ms","delta_ns","delta_ms"])
        w.writeheader(); w.writerows(pos_examples)

    pos=[x for x in deltas_ns if x>0]
    obj={
      "schema_version":"0.1",
      "lab_id":LAB_ID,
      "classification":"SOURCE_CLOCK_DIAGNOSTIC_COMPLETE",
      "scope":"TIMESTAMPS_ONLY_NO_MARKET_OUTCOMES",
      "key":args.key,
      "raw_sha256":observed_sha,
      "expected_raw_sha256":EXPECTED_RAW_SHA256 if args.key==DEFAULT_KEY else None,
      "raw_hash_match":(observed_sha==EXPECTED_RAW_SHA256) if args.key==DEFAULT_KEY else None,
      "records":rows,
      "envelope_backwards":env_backwards,
      "payload_rewinds_inside_object":payload_rewinds,
      "payload_minus_envelope":{
        "positive_count":positive,
        "zero_count":zero,
        "negative_count":negative,
        "min_ms":min(deltas_ns)/1_000_000.0 if deltas_ns else None,
        "median_ms":statistics.median(deltas_ns)/1_000_000.0 if deltas_ns else None,
        "p95_ms":percentile(deltas_ns,.95)/1_000_000.0 if deltas_ns else None,
        "p99_ms":percentile(deltas_ns,.99)/1_000_000.0 if deltas_ns else None,
        "max_ms":max(deltas_ns)/1_000_000.0 if deltas_ns else None,
        "positive_min_ms":min(pos)/1_000_000.0 if pos else None,
        "positive_median_ms":statistics.median(pos)/1_000_000.0 if pos else None,
        "positive_max_ms":max(pos)/1_000_000.0 if pos else None,
      },
      "sample_csv_sha256":sha256_file(samples),
      "guards":{
        "levels_read":False,
        "prices_stored":False,
        "sizes_stored":False,
        "midpoint_computed":False,
        "sweeps_computed":False,
        "replenishment_computed":False,
        "returns_computed":False,
        "validation_outcomes_computed":False,
        "pnl_computed":False,
        "access_2026":False,
      }
    }
    receipt.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    with zipfile.ZipFile(bundle,"w",zipfile.ZIP_DEFLATED) as z:
        z.write(receipt,receipt.name); z.write(samples,samples.name)
    print(json.dumps(obj,indent=2,sort_keys=True))
    print("EVIDENCE_BUNDLE",bundle)
    print("EVIDENCE_BUNDLE_SHA256",sha256_file(bundle))

if __name__=="__main__":
    main()
