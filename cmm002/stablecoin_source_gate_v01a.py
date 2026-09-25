#!/usr/bin/env python3
import csv, hashlib, io, json, math, os, statistics, urllib.parse, urllib.request
from datetime import date, datetime, timezone

ROOT=os.path.dirname(__file__)
PARENT=os.path.join(ROOT,"..","cmm001","discovery_results","CMM001_DAILY_STATE_LEDGER_V01.csv")
OUT_DIR=os.path.join(ROOT,"source_results")
os.makedirs(OUT_DIR,exist_ok=True)
UA="CryptoLab-CMM002-SourceGate/0.1A research-only"

def get_bytes(url,timeout=60):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.read(),dict(r.headers),r.status

def percentile_linear(values,q):
    xs=sorted(values)
    if not xs:return None
    if len(xs)==1:return xs[0]
    pos=(len(xs)-1)*q
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi:return xs[lo]
    w=pos-lo
    return xs[lo]*(1-w)+xs[hi]*w

def pearson(xs,ys):
    mx=statistics.fmean(xs); my=statistics.fmean(ys)
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx=math.sqrt(sum((x-mx)**2 for x in xs))
    dy=math.sqrt(sum((y-my)**2 for y in ys))
    return num/(dx*dy) if dx>0 and dy>0 else None

with open(PARENT,"rb") as f:
    parent_sha=hashlib.sha256(f.read()).hexdigest()

parent={}
with open(PARENT,"r",encoding="utf-8-sig",newline="") as f:
    for r in csv.DictReader(f):
        try:
            d=date.fromisoformat(r["date"])
            if date(2024,1,1)<=d<=date(2024,12,31) and r.get("L_raw") not in ("",None):
                parent[d]=float(r["L_raw"])
        except Exception:
            pass

target="https://stablecoins.llama.fi/stablecoincharts/all"
params=[
 ("url",target),
 ("from","2025"),
 ("to","20251231235959"),
 ("output","json"),
 ("filter","statuscode:200"),
 ("fl","timestamp,original,statuscode,mimetype,digest"),
 ("collapse","digest"),
]
cdx="https://web.archive.org/cdx/search/cdx?"+urllib.parse.urlencode(params,doseq=True)

receipt={
 "lab_id":"CMM-002-V01",
 "gate":"HOLDOUT_SAFE_STABLECOIN_SOURCE_V01A",
 "outcomes_opened":False,
 "parent_daily_state_sha256":parent_sha,
 "cdx_url":cdx,
}
try:
    b,_,status=get_bytes(cdx,90)
    rows=json.loads(b.decode("utf-8"))
    hdr=rows[0] if rows else []
    data=[dict(zip(hdr,row)) for row in rows[1:]] if hdr else []
    valid=[r for r in data if r.get("timestamp","") < "20260101000000" and r.get("statuscode")=="200"]
    if not valid:
        raise RuntimeError("NO_BOUNDED_2025_WAYBACK_SNAPSHOT")
    snap=max(valid,key=lambda r:r["timestamp"])
    ts=snap["timestamp"]
    replay=f"https://web.archive.org/web/{ts}id_/{target}"
    rb,_,rstatus=get_bytes(replay,120)
    payload=json.loads(rb.decode("utf-8"))
    if not isinstance(payload,list):
        raise RuntimeError("ARCHIVE_PAYLOAD_NOT_LIST")

    supply={}
    max_d=None
    min_d=None
    for x in payload:
        try:
            d=datetime.fromtimestamp(int(x["date"]),timezone.utc).date()
            v=float(x["totalCirculatingUSD"]["peggedUSD"])
            if v<=0 or not math.isfinite(v): continue
            supply[d]=v
            min_d=d if min_d is None or d<min_d else min_d
            max_d=d if max_d is None or d>max_d else max_d
        except Exception:
            pass

    forbidden=[d.isoformat() for d in supply if d>=date(2026,1,1)]
    if forbidden:
        raise RuntimeError(f"ARCHIVE_PAYLOAD_CONTAINS_2026 rows={len(forbidden)}")

    def latest_leq(cut):
        ds=[d for d in supply.keys() if d<=cut]
        if not ds:return None
        d=max(ds); return d,supply[d]

    archived_l={}
    for d in sorted(parent):
        a=latest_leq(d.replace() - __import__("datetime").timedelta(days=1))
        z=latest_leq(d.replace() - __import__("datetime").timedelta(days=31))
        if a and z and a[1]>0 and z[1]>0:
            archived_l[d]=math.log(a[1]/z[1])

    overlap=sorted(set(parent)&set(archived_l))
    xs=[parent[d] for d in overlap]
    ys=[archived_l[d] for d in overlap]
    diffs=[abs(a-b) for a,b in zip(xs,ys)]
    corr=pearson(xs,ys)
    med=statistics.median(diffs) if diffs else None
    p95=percentile_linear(diffs,.95) if diffs else None

    coverage_2025=sum(1 for d in supply if date(2025,1,1)<=d<=date(2025,12,31))
    checks={
      "snapshot_before_2026":ts<"20260101000000",
      "payload_no_2026":not forbidden,
      "coverage_2025_ge_360":coverage_2025>=360,
      "overlap_n_ge_300":len(overlap)>=300,
      "corr_ge_0_995":corr is not None and corr>=0.995,
      "median_abs_diff_le_0_002":med is not None and med<=0.002,
      "p95_abs_diff_le_0_010":p95 is not None and p95<=0.010,
    }
    passed=all(checks.values())
    receipt.update({
      "classification":"SOURCE_DATA_PASS" if passed else "SOURCE_BLOCKED",
      "archive_timestamp":ts,
      "archive_replay_url":replay,
      "archive_http_status":rstatus,
      "archive_payload_sha256":hashlib.sha256(rb).hexdigest(),
      "archive_min_date":min_d.isoformat() if min_d else None,
      "archive_max_date":max_d.isoformat() if max_d else None,
      "coverage_2025":coverage_2025,
      "semantic_overlap_n":len(overlap),
      "pearson":corr,
      "median_abs_diff":med,
      "p95_abs_diff":p95,
      "checks":checks,
    })
except Exception as e:
    receipt.update({"classification":"SOURCE_BLOCKED","error":repr(e)})

path=os.path.join(OUT_DIR,"CMM002_STABLECOIN_SOURCE_GATE_V01A.json")
with open(path,"w",encoding="utf-8") as f:
    json.dump(receipt,f,indent=2,sort_keys=True,allow_nan=False)

md=[
 "# CMM-002 — HOLDOUT-SAFE STABLECOIN SOURCE GATE V0.1A",
 "",
 f"Classification: **{receipt['classification']}**",
 "",
 "No CMM-002 2025 BTC outcome or PnL was opened.",
 f"Parent daily-state SHA256: {receipt['parent_daily_state_sha256']}",
]
for k in ("archive_timestamp","archive_min_date","archive_max_date","coverage_2025","semantic_overlap_n","pearson","median_abs_diff","p95_abs_diff","error"):
    if k in receipt: md.append(f"- {k}: {receipt[k]}")
if "checks" in receipt:
    md.append("")
    md.append("## Checks")
    for k,v in receipt["checks"].items(): md.append(f"- {k}: {'PASS' if v else 'FAIL'}")
with open(os.path.join(OUT_DIR,"CMM002_STABLECOIN_SOURCE_GATE_V01A.md"),"w",encoding="utf-8") as f:
    f.write("\n".join(md)+"\n")

print(json.dumps(receipt,indent=2,allow_nan=False))
if receipt["classification"]!="SOURCE_DATA_PASS":
    raise SystemExit(2)
