#!/usr/bin/env python3
"""Offline-only replay of pinned BINANCE011 action artifact; no market requests."""
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
INPUT=Path("binance011r-input")
WORK=Path("binance011r-work")
RESULT=Path("binance011r-results")
RUN=45337495640
ARTIFACT_ID=14895554598
RAW_SHA="83ff8d37e2fcf9477cd7e8e125f243063167ffa702cd5c6ae9b12292c8760cac"
LAST_CHAIN="2291d3e97e2ed98762bdd5376e7a150d24daed36eb4d57c04e095672b9390c6a"
PINS={
 "research/binance_diamante003/book_core.py":"9b2a92455d36dc251ec99a2754c07a7f91a9af91",
 "research/binance_diamante003/capture.py":"490ad52bef283dedb4036e8793f6892788803a0e",
 "research/binance_diamante004/study.py":"58cf6af9c0ba26da2ac9efa700c103b93c7580b5",
 "research/binance_diamante004/verify_offline.py":"33ca9731cbbb2d4f22db8d5309d4616bfe3ca616",
 "research/binance_diamante010/runner.py":"4c58e496c048e8a4d032cfcd022995fa20ba21b7"
}
KNOWN={
 "PRIMARY":(21,-31.17594879113982,0),
 "FLOW_ONLY_CONTROL":(18,-31.158937486804135,0),
 "UNCONDITIONAL_BASELINE":(42,-32.66348502066176,0)
}
class Stop(Exception):pass

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as fd:
  for part in iter(lambda:fd.read(1048576),b""):h.update(part)
 return h.hexdigest()

def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def pins():
 for p,x in PINS.items():
  if blob((ROOT/p).read_bytes())!=x:raise Stop("PINNED_ORIGINAL_SOURCE_CHANGED_"+p)
 if os.getenv("GITHUB_REPOSITORY") not in ("", "joseluisvieira28-oss/Laboratorio"):
  raise Stop("WRONG_REPOSITORY")
 if os.getenv("GITHUB_EVENT_NAME") not in ("", "pull_request"):
  raise Stop("UNAUTHORIZED_GITHUB_TRIGGER")
 return True

def receipt(name):
 p=INPUT/name
 sig=INPUT/(name+".sha256")
 if not p.is_file() or not sig.is_file():raise Stop("MISSING_RECEIPT_"+name)
 if sha(p)!=sig.read_text().strip().split()[0]:raise Stop("RECEIPT_TAMPERED_"+name)
 return json.loads(p.read_bytes())

def validate_metadata():
 if not INPUT.is_dir() or (INPUT/"journal.jsonl").exists():raise Stop("ARCHIVE_MISSING_OR_RAW_UNEXPECTED")
 idx=receipt("lossless_segments_manifest.json")
 src=receipt("source_manifest.json")
 original=receipt("forward_verdict.json")
 final=receipt("segmented_archive_final_receipt.json")
 verification=receipt("segmented_archive_verification.json")
 if (idx.get("raw_utf8_sha256"),idx.get("journal_last_chain_sha256"))!=(RAW_SHA,LAST_CHAIN):
  raise Stop("PINNED_ARCHIVE_SOURCE_OR_CHAIN_MISMATCH")
 if (idx.get("chunk_count"),idx.get("raw_utf8_bytes"),idx.get("compressed_total_bytes"),
     idx.get("total_chained_records"))!=(7,98597308,19716712,91729):
  raise Stop("ORIGINAL_CHUNK_COUNT_OR_SOURCE_LENGTH_MISMATCH")
 if src.get("journal_file_sha256")!=RAW_SHA or src.get("journal_chain_sha256")!=LAST_CHAIN:
  raise Stop("SOURCE_MANIFEST_PIN_MISMATCH")
 if (src.get("status")!="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE" or
     src.get("completed_source_window") is not True or
     src.get("source_replay_exact") is not True or
     src.get("seconds_post_bridge_target")!=1800 or
     src.get("captured_journal_events")!=91729 or src.get("ws_frames")!=91726):
  raise Stop("NOT_FULL_ORIGINAL_CAPTURE")
 if (src.get("snapshot_count")!=3 or
     set(src.get("source_books",{}))!={"BTCUSDT","ETHUSDT","SOLUSDT"} or
     any(v.get("status")!="SYNCED" for v in src["source_books"].values())):
  raise Stop("NOT_THREE_SYNCED_ORIGINAL_BOOKS")
 if final.get("status")!="LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS" or final.get("original_uncompressed_file_retained_in_public_artifact") is not False:
  raise Stop("ORIGINAL_ARCHIVE_NOT_LOSSLESS_PROVEN")
 if verification.get("status")!="LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS":
  raise Stop("ORIGINAL_PRE_UPLOAD_ARCHIVE_VERIFICATION_FAILED")
 if original.get("windows_evaluated")!=180 or original.get("window_valid")!=180:
  raise Stop("NOT_ORIGINAL_180_VALID_WINDOWS")
 if original.get("real_fills")!=0 or original.get("economic_go") is not False:
  raise Stop("ORIGINAL_NOT_SHADOW_ONLY")
 if not (INPUT/"forward_ledger.json").is_file() or sha(INPUT/"forward_ledger.json")!=original.get("ledger_sha256"):
  raise Stop("ORIGINAL_SHADOW_LEDGER_HASH_INVALID")
 for kind,(count,mean,positive) in KNOWN.items():
  group=original["groups"][kind];data=group["hypothetical"]["1000_STRESS_5BPS"]
  if group["matured"]!=count or data["positive_count"]!=positive or abs(data["mean_net_bps"]-mean)>1e-9:
   raise Stop("CHANGED_ALREADY_OBSERVED_QUOTE_"+kind)
 return idx,src,original

def decompress_exact(idx,output):
 chunks=idx["chunks"]
 if not isinstance(chunks,list) or len(chunks)!=7:raise Stop("NOT_7_SEGMENTS")
 raw_total=0;gz_total=0;rows_total=0;prev=0;whole=hashlib.sha256()
 with Path(output).open("xb") as raw:
  for i,c in enumerate(chunks,1):
   name="journal-part-%04d.jsonl.gz"%i
   if c["file"]!=name or c["record_seq_first"]!=prev+1:
    raise Stop("SEQUENCE_GAP_OR_CHANGED_PART_ORDER")
   if c["record_seq_last"]-c["record_seq_first"]+1!=c["records"]:
    raise Stop("SEGMENT_EVENT_COUNT_DIFF")
   prev=c["record_seq_last"]
   p=INPUT/name
   if not p.is_file() or p.stat().st_size!=c["gzip_bytes"] or sha(p)!=c["gzip_sha256"]:
    raise Stop("MISSING_OR_TAMPERED_GZIP_"+name)
   gz_total+=c["gzip_bytes"]
   if gz_total>160000000:raise Stop("COMPRESSED_CAP_EXCEEDED")
   digest=hashlib.sha256();chunk_rows=0;chunk_bytes=0
   with gzip.open(p,"rb") as f:
    while True:
     block=f.read(1048576)
     if not block:break
     chunk_bytes+=len(block);raw_total+=len(block)
     if chunk_bytes>16000000 or raw_total>520000000:
      raise Stop("ORIGINAL_BYTE_CAP_EXCEEDED")
     digest.update(block);whole.update(block)
     chunk_rows+=block.count(b"\n")
     raw.write(block)
   if digest.hexdigest()!=c["original_sha256"] or chunk_bytes!=c["original_bytes"] or chunk_rows!=c["records"]:
    raise Stop("DECOMPRESSED_SEGMENT_BYTES_OR_LINES_DIFFER_"+name)
   rows_total+=chunk_rows
 if (gz_total,raw_total,rows_total,prev,whole.hexdigest())!=(19716712,98597308,91729,91729,RAW_SHA):
  raise Stop("RECONSTRUCTED_ORIGINAL_SOURCE_DIFF")
 return {"raw_source_sha256":whole.hexdigest(),"raw_bytes":raw_total,"gzip_bytes":gz_total,
         "records":rows_total,"segments":len(chunks),"byte_identical_to_original":True}

def replay_004(work):
 # Import SHA-pinned 010 extension under unique name; restore exact 60 windows
 # AND its last-decision=1680sec in memory. Never connect to market.
 base=ROOT/"research/binance_diamante004"
 runner=ROOT/"research/binance_diamante010/runner.py"
 sys.path.insert(0,str(base))
 m=importlib.util.spec_from_file_location("binance011r_frozen010_clock",runner)
 old=importlib.util.module_from_spec(m);sys.modules[m.name]=old;m.loader.exec_module(old)
 old.guard()
 _,study=old.setup()
 study.OUT=Path(work)
 if study.CAPTURE_NS!=1800*10**9 or study.LATEST_DECISION_NS!=1680*10**9:
  raise Stop("REPLAY_CLOCK_DIFFERS_FROM_011")
 # Critical bugfix: load 004/verify_offline.py by ABSOLUTE PATH, not
 # 'import verify_offline' (which previously bound 003 lacking check()).
 p=base/"verify_offline.py"
 spec=importlib.util.spec_from_file_location("binance011r_exact_004_verifier",p)
 audit=importlib.util.module_from_spec(spec);sys.modules[spec.name]=audit
 spec.loader.exec_module(audit)
 if Path(audit.__file__).resolve()!=p.resolve() or not callable(getattr(audit,"check",None)):
  raise Stop("WRONG_VERIFIER_IMPORTED")
 ret=audit.check()
 result=json.loads((Path(work)/"independent_replay_verdict.json").read_text())
 if ret!=0 or result.get("status")!="RAW_SOURCE_AND_DETERMINISTIC_LEDGER_PASS_ONLY":
  raise Stop("ORIGINAL_004_VERIFIER_FAILED_"+str(result.get("error"))[:150])
 return result

def save(result):
 RESULT.mkdir(exist_ok=True)
 p=RESULT/"binance011r_offline_verdict.json"
 p.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
 (RESULT/"binance011r_offline_verdict.sha256").write_text(sha(p)+"  "+p.name+"\n")

def main():
 result={"study":"BINANCE011R","status":"REPLAY_BLOCKED",
         "original_pr":390,"original_action_run_id":RUN,"original_artifact_id":ARTIFACT_ID,
         "original_source_utc_day":"2026-11-24",
         "new_market_observations":0,"actual_orders":0,"real_fills":0,
         "economic_go":False,"live_trading_go":False,
         "independent_out_of_sample_replication":False}
 try:
  pins()
  idx,src,original=validate_metadata()
  WORK.mkdir(exist_ok=True)
  for name in ("source_manifest.json","source_manifest.sha256","forward_verdict.json",
               "forward_verdict.sha256","forward_ledger.json"):
   shutil.copyfile(INPUT/name,WORK/name)
  original_file=WORK/"journal.jsonl"
  result["archived_original_roundtrip"]=decompress_exact(idx,original_file)
  result["frozen_004_verifier"]=replay_004(WORK)
  ledger=json.loads((WORK/"forward_ledger.json").read_text())
  if len(ledger["windows"])!=180:
   raise Stop("REPLAY_NOT_180_WINDOWS")
  if any(w["allowed_before_cutoff"]!=(w["end_t0_seconds"]<=1680) for w in ledger["windows"]):
   raise Stop("DECISION_CUTOFF_CHANGED")
  if any(e["decision_t0_sec"]>1680 for e in ledger["events"]):
   raise Stop("FUTURE_DECISION_FOUND")
  if len(ledger["events"])!=sum(x["decisions"] for x in original["groups"].values()):
   raise Stop("SIGNAL_EVENT_LEDGER_MISMATCH")
  with original_file.open("rb") as f:
   first=json.loads(f.readline());last=first
   for line in f:last=json.loads(line)
  dates={dt.datetime.fromtimestamp(x["utc_ns"]/1e9,tz=dt.timezone.utc).strftime("%Y-%m-%d")
         for x in (first,last)}
  if dates!={"2026-11-24"}:raise Stop("RAW_UTC_DAY_CHANGED")
  if original.get("source_clock_invalid_frames")!=0:raise Stop("BAD_ORIGINAL_SOURCE_CLOCK")
  result.update({"status":"REPLAY_PASS_SAME_SCIENCE_ONLY_NO_LIVE_GO",
                 "source_integrity":"SHA256_AND_ORIGINAL_004_REPLAY_PASS",
                 "valid_30_second_symbol_windows":180,
                 "groups":original["groups"],
                 "scientific_note":"Previously observed 011 quote outcomes; same-code exact deterministic replay, not independent holdout",
                 "statistical_independent_utc_days":1})
 except Exception as exc:
  result["failure_type"]=type(exc).__name__
  result["failure_reason"]=str(exc)[:320]
 finally:
  (WORK/"journal.jsonl").unlink(missing_ok=True)
  save(result)
  concise={k:v for k,v in result.items() if k!="groups"}
  print(json.dumps(concise,indent=2,sort_keys=True))
 return 0 if result["status"]=="REPLAY_PASS_SAME_SCIENCE_ONLY_NO_LIVE_GO" else 2

if __name__=="__main__":raise SystemExit(main())
