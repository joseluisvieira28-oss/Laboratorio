#!/usr/bin/env python3
import datetime as dt, hashlib, heapq, json, os, sqlite3, sys, tempfile
from pathlib import Path

ROOT=Path(sys.argv[1])
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
CENSUS=BASE/"DRIFT_SQD_EVENT_CENSUS_RECEIPT_V0.1.json"
QUEUE=BASE/"DRIFT_RAW_SAMPLE_QUEUE_V0.1.json"

LOWER=dt.datetime.fromisoformat("2022-11-04T15:17:54+00:00")
UPPER=dt.datetime.fromisoformat("2025-01-01T00:00:00+00:00")
CLASSES={
 "liquidate_perp":"4b2377f7bf128b02",
 "liquidate_spot":"6b00802923e5fb12",
 "liquidate_borrow_for_perp_pnl":"a911205acf94d11b",
 "liquidate_perp_pnl_for_deposit":"ed4bc6ebe9ba4b23",
}

def parse(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def sha_file(p):
    h=hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1024*1024), b""): h.update(block)
    return h.hexdigest()
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def path_class(v): return "inner" if isinstance(v,list) and len(v)>1 else "outer"
def sig_rank(cls,sig): return hashlib.sha256(("drift:"+cls+":"+sig).encode()).hexdigest()

# Evidence selection is frozen: PARTITION_COMPLETE only.
all_manifests=[]; accepted=[]; excluded=[]
for mp in sorted(ROOT.rglob("MANIFEST.json")):
    try:
        with mp.open("r",encoding="utf-8") as fh: m=json.load(fh)
    except Exception:
        continue
    if m.get("protocol")!="drift": continue
    all_manifests.append(str(mp))
    if m.get("classification")=="PARTITION_COMPLETE":
        accepted.append((mp,m))
    else:
        excluded.append({"manifest":str(mp),"classification":m.get("classification"),
                         "reason":"NON_AUTHORITATIVE_PARTIAL_TRANSPORT_EVIDENCE_EXCLUDED"})

summary={
 "schema_version":"0.3",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"DRIFT_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE",
 "aggregation_mode":"STREAMING_DISK_BACKED_EXACT_KEYS",
 "evidence_selection_rule":"PARTITION_COMPLETE_ONLY",
 "manifest_count_seen":len(all_manifests),
 "accepted_manifest_count":len(accepted),
 "excluded_partial_manifest_count":len(excluded),
 "excluded_partial_manifests":excluded,
 "classes":{},
 "firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
 "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
 "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
 "post_outcome_tuning":False,"merge_main":False}
}

# Validate chunks and exact chronological coverage before event aggregation.
slices={}
bad_hash=[]; chunk_errors=[]; duplicate_slices=[]; source_anomalies=[]
for mp,m in accepted:
    base=mp.parent
    for ch in m.get("chunks",[]):
        k=(ch.get("start"),ch.get("end"))
        fp=base/ch["file"]
        if not fp.exists():
            bad_hash.append({"slice":k,"reason":"missing_file","manifest":str(mp)}); continue
        actual=sha_file(fp)
        if actual!=ch.get("sha256"):
            bad_hash.append({"slice":k,"reason":"sha_mismatch","expected":ch.get("sha256"),"actual":actual,"file":str(fp)}); continue
        with fp.open("r",encoding="utf-8") as fh: rec=json.load(fh)
        if rec.get("classification")!="SOURCE_CHUNK_PASS" or rec.get("stream_complete") is not True:
            chunk_errors.append({"slice":k,"classification":rec.get("classification"),
                                 "stream_complete":rec.get("stream_complete"),"file":str(fp)}); continue
        if int(rec.get("anomaly_count") or 0)!=0:
            source_anomalies.append({"slice":k,"anomaly_count":rec.get("anomaly_count"),"file":str(fp)}); continue
        if k in slices:
            duplicate_slices.append({"start":k[0],"end":k[1],"existing":str(slices[k]),"duplicate":str(fp)})
            continue
        slices[k]=fp

ordered=sorted(((parse(a),parse(b),a,b,fp) for (a,b),fp in slices.items()),key=lambda x:(x[0],x[1]))
cursor=LOWER; gaps=[]; overlaps=[]; selected=[]
for s,e,a,b,fp in ordered:
    if e<=LOWER or s>=UPPER: continue
    if s>cursor:
        gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_start":a})
        if e>cursor: cursor=e
    elif s<cursor:
        overlaps.append({"cursor":cursor.isoformat().replace("+00:00","Z"),"observed_start":a,"observed_end":b,"file":str(fp)})
        if e>cursor: cursor=e
    else:
        cursor=e
    selected.append((s,e,fp))
if cursor<UPPER:
    gaps.append({"expected_start":cursor.isoformat().replace("+00:00","Z"),"observed_end":UPPER.isoformat().replace("+00:00","Z")})

# Fail closed before touching event population if transport evidence is not exact.
pre_blocked=bool((not accepted) or bad_hash or chunk_errors or duplicate_slices or source_anomalies or gaps or overlaps)

tmpdir=Path(tempfile.mkdtemp(prefix="dls_drift_agg_"))
db_path=tmpdir/"events.sqlite3"
con=sqlite3.connect(db_path)
cur=con.cursor()
cur.execute("PRAGMA journal_mode=OFF")
cur.execute("PRAGMA synchronous=OFF")
cur.execute("PRAGMA temp_store=FILE")
cur.execute("PRAGMA cache_size=-65536")
cur.execute("""CREATE TABLE IF NOT EXISTS events(
  class TEXT NOT NULL,
  signature TEXT NOT NULL,
  addr TEXT NOT NULL,
  row_hash TEXT NOT NULL,
  state TEXT,
  ts TEXT,
  slot INTEGER,
  row_json TEXT NOT NULL,
  PRIMARY KEY(class,signature,addr)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS success_sigs(
  class TEXT NOT NULL,
  signature TEXT NOT NULL,
  slot INTEGER,
  ts TEXT,
  PRIMARY KEY(class,signature)
)""")
con.commit()

duplicate_instruction_key_count=0
dedup_collisions=[]
batch=0

if not pre_blocked:
    for _,_,fp in selected:
        with fp.open("r",encoding="utf-8") as fh: rec=json.load(fh)
        for r in rec.get("rows") or []:
            cls=r.get("class"); sig=r.get("signature"); addr=addr_key(r.get("instructionAddress"))
            row_json=json.dumps(r,separators=(",",":"),sort_keys=True)
            row_hash=hashlib.sha256(row_json.encode()).hexdigest()
            state=r.get("classification")
            ts=r.get("timestamp"); slot=r.get("slot")
            if cls not in CLASSES or not isinstance(sig,str) or not sig:
                source_anomalies.append({"reason":"invalid_event_identity","class":cls,"signature":sig,"file":str(fp)})
                continue
            try:
                cur.execute("INSERT INTO events(class,signature,addr,row_hash,state,ts,slot,row_json) VALUES(?,?,?,?,?,?,?,?)",
                            (cls,sig,addr,row_hash,state,ts,slot,row_json))
            except sqlite3.IntegrityError:
                duplicate_instruction_key_count+=1
                old=cur.execute("SELECT row_hash FROM events WHERE class=? AND signature=? AND addr=?",(cls,sig,addr)).fetchone()
                if not old or old[0]!=row_hash:
                    dedup_collisions.append({"class":cls,"signature":sig,"addr":addr})
            if state=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
                try:
                    cur.execute("INSERT OR IGNORE INTO success_sigs(class,signature,slot,ts) VALUES(?,?,?,?)",(cls,sig,slot,ts))
                except Exception:
                    source_anomalies.append({"reason":"success_signature_insert_failed","class":cls,"signature":sig})
            batch+=1
            if batch%10000==0: con.commit()
        con.commit()

queues={}
for cls,prefix in CLASSES.items():
    local_anom=[]
    success_count=0; failed_count=0
    first=None; last=None

    for state,cnt in cur.execute("SELECT state,COUNT(*) FROM events WHERE class=? GROUP BY state",(cls,)):
        if state=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": success_count=cnt
        elif state=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED": failed_count=cnt
        else: local_anom.append({"reason":"unexpected_row_class","classification":state,"count":cnt})

    distinct_success=cur.execute("SELECT COUNT(*) FROM success_sigs WHERE class=?",(cls,)).fetchone()[0]

    row=cur.execute("""SELECT row_json FROM events
                       WHERE class=? AND state='SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION'
                       ORDER BY ts ASC, slot ASC, signature ASC, addr ASC LIMIT 1""",(cls,)).fetchone()
    if row: first=json.loads(row[0])
    row=cur.execute("""SELECT row_json FROM events
                       WHERE class=? AND state='SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION'
                       ORDER BY ts DESC, slot DESC, signature DESC, addr DESC LIMIT 1""",(cls,)).fetchone()
    if row: last=json.loads(row[0])

    # deterministic signature sample: mandatory first/last + 30 lowest sha256 ranks
    mandatory=[]
    if first and first.get("signature"): mandatory.append(first["signature"])
    if last and last.get("signature") and last["signature"] not in mandatory: mandatory.append(last["signature"])
    heap=[]
    seen=set(mandatory)
    for (sig,) in cur.execute("SELECT signature FROM success_sigs WHERE class=?",(cls,)):
        if sig in seen: continue
        rank=sig_rank(cls,sig)
        rv=int(rank,16)
        if len(heap)<30:
            heapq.heappush(heap,(-rv,sig))
        elif rv < -heap[0][0]:
            heapq.heapreplace(heap,(-rv,sig))
    ranked=[sig for _,sig in sorted([(-x,s) for x,s in heap],key=lambda z:(z[0],z[1]))]
    selected_sigs=mandatory+[s for s in ranked if s not in mandatory]

    entries=[]
    for sig in selected_sigs:
        rows=cur.execute("""SELECT row_json FROM events
                            WHERE class=? AND signature=? AND state='SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION'
                            ORDER BY addr ASC""",(cls,sig)).fetchall()
        if not rows: continue
        decoded=[json.loads(x[0]) for x in rows]
        slots={r.get("slot") for r in decoded}; tss={r.get("timestamp") for r in decoded}
        if len(slots)!=1 or len(tss)!=1:
            local_anom.append({"reason":"signature_slot_time_inconsistent","signature":sig})
        entries.append({
          "signature":sig,
          "slot":decoded[0].get("slot"),
          "timestamp":decoded[0].get("timestamp"),
          "expected_path_classes":sorted({path_class(r.get("instructionAddress")) for r in decoded}),
          "instruction_addresses":[r.get("instructionAddress") for r in decoded],
          "class":cls,
          "prefix":prefix
        })

    queues[cls]={
      "mandatory_first":first.get("signature") if first else None,
      "mandatory_last":last.get("signature") if last else None,
      "selected_count":len(entries),
      "distinct_successful_signatures":distinct_success,
      "entries":entries
    }
    summary["classes"][cls]={
      "discriminator":prefix,
      "successful_instruction_count":success_count,
      "distinct_successful_signatures":distinct_success,
      "failed_attempt_count":failed_count,
      "anomaly_count":len(local_anom),
      "first_success":first,
      "last_success":last
    }
    source_anomalies.extend({"class":cls,**x} for x in local_anom)

summary.update({
 "coverage_start":LOWER.isoformat().replace("+00:00","Z"),
 "coverage_end":UPPER.isoformat().replace("+00:00","Z"),
 "coverage_through":cursor.isoformat().replace("+00:00","Z"),
 "accepted_slice_count":len(slices),
 "gap_count":len(gaps),"gaps":gaps,
 "overlap_count":len(overlaps),"overlaps":overlaps,
 "bad_chunk_hash":bad_hash,"chunk_errors":chunk_errors,
 "duplicate_slice_count":len(duplicate_slices),"duplicate_slices":duplicate_slices,
 "duplicate_instruction_key_count":duplicate_instruction_key_count,
 "dedup_collision_count":len(dedup_collisions),
 "dedup_collisions":dedup_collisions[:100],
 "anomaly_count":len(source_anomalies)
})

if (pre_blocked or duplicate_instruction_key_count or dedup_collisions or source_anomalies
    or any((summary["classes"].get(c) or {}).get("successful_instruction_count",0)<=0 for c in CLASSES)):
    summary["classification"]="DRIFT_SQD_EVENT_CENSUS_BLOCKED_FAIL_CLOSED"

CENSUS.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
QUEUE.write_text(json.dumps({"schema_version":"0.3","classes":queues},indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":summary["classification"],
 "seen_manifests":len(all_manifests),
 "accepted_manifests":len(accepted),
 "excluded_partials":len(excluded),
 "coverage_through":summary["coverage_through"],
 "gaps":len(gaps),"overlaps":len(overlaps),
 "duplicate_instruction_keys":duplicate_instruction_key_count,
 "anomalies":summary["anomaly_count"],
 "classes":{k:{"success":v["successful_instruction_count"],"failed":v["failed_attempt_count"],
               "distinct_success_signatures":v["distinct_successful_signatures"],
               "first":v["first_success"]} for k,v in summary["classes"].items()}
},indent=2))
con.close()
if summary["classification"]!="DRIFT_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":
    raise SystemExit(2)
