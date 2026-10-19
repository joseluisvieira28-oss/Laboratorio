"""V05B: two raw official public OKX historical L2 archive audits, no orders.

Pure personal-use research: raw prices and files NEVER uploaded, only sanitized
source status, schema, hashes, counts and causal age. No historical multiplier/fill.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,tarfile,tempfile,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from research.convex_okx_l2_v05.catalogue_gate import CASES,ENDPOINT,SameOriginRedirects
from research.convex_okx_l2_v05.l2_reconstructor import Book,SourceRejected,update

MAX_ZIP=190_000_000
MAX_UNPACKED=2_000_000_000
MAX_LINES=10_000_000
CHUNK=4_194_304
CASES_AT_T0={
    "SOL-USDT":1685376300000,
    "BNB-USDT":1698854700000
}

def metadata(case):
    fam,inst,day,epoch=case
    url=ENDPOINT+"?"+urllib.parse.urlencode({
        "module":"4","instType":"SWAP","instFamilyList":fam,
        "dateAggrType":"daily","begin":epoch,"end":epoch
    })
    req=urllib.request.Request(url,headers={"Accept":"application/json"})
    with urllib.request.build_opener(SameOriginRedirects).open(req,timeout=10) as x:
        if x.status!=200:raise ValueError("CATALOGUE_NON200")
        raw=x.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError("CATALOGUE_EXCEEDS_CAP")
    payload=json.loads(raw.decode("utf-8"))
    if str(payload.get("code"))!="0":raise ValueError("CATALOGUE_NOT_ZERO")
    data=payload.get("data")
    if type(data) is not list or len(data)!=1:raise ValueError("CATALOGUE_CARDINALITY")
    details=data[0].get("details")
    if type(details) is not list or len(details)!=1:
        raise ValueError("DETAILS_CARDINALITY")
    d=details[0]
    if d.get("instType")!="SWAP" or d.get("instFamily")!=fam:
        raise ValueError("CATALOGUE_FAMILY_MISMATCH")
    # instId may be empty for instFamily-list catalogue query.
    grouped=d.get("groupDetails")
    if type(grouped) is not list or len(grouped)!=1:raise ValueError("FILE_COUNT_NOT_ONE")
    f=grouped[0]
    filename=f.get("filename")
    if (not isinstance(filename,str) or
        not filename.startswith(inst) or day not in filename or
        not filename.endswith(".tar.gz")):
        raise ValueError("HISTORICAL_FILENAME_NOT_EXACT_INSTRUMENT_AND_DAY")
    v=urllib.parse.urlsplit(f.get("url",""))
    if (v.scheme!="https" or v.hostname!="static.okx.com" or v.username
        or v.password or v.fragment or not v.path.endswith(".tar.gz")
        or v.query or not v.path.endswith(filename)):
        raise ValueError("UNAPPROVED_ARCHIVE_ORIGIN_OR_FILENAME")
    ts=int(f.get("dateTs"))
    if not epoch<=ts<epoch+86400000:raise ValueError("WRONG_SOURCE_DAY")
    expected_sz=f.get("sizeMB")
    return {"source_url":f["url"],"filename":filename,
        "reported_MB":str(expected_sz),"catalogue_sha256":hashlib.sha256(raw).hexdigest(),
        "source_day":day,"instrument":inst,"family":fam}

class OneHostRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        dest=urllib.parse.urlsplit(newurl)
        if dest.scheme!="https" or dest.hostname!="static.okx.com":
            raise ValueError("OFF_PUBLISHER_ARCHIVE_REDIRECT")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def download_to_temp(meta,tempfile_path):
    uri=meta["source_url"]
    req=urllib.request.Request(uri,headers={"User-Agent":"CryptoLab-Personal-Historical-Research/0.5"})
    used=0
    h=hashlib.sha256()
    with urllib.request.build_opener(OneHostRedirects).open(req,timeout=35) as resp:
        if resp.status!=200:raise ValueError("ARCHIVE_HTTP_NON200")
        with open(tempfile_path,"wb") as output:
            while True:
                buf=resp.read(CHUNK)
                if not buf:break
                used+=len(buf)
                if used>MAX_ZIP:raise ValueError("ARCHIVE_190MB_CAP")
                h.update(buf);output.write(buf)
    return {"download_bytes":used,"transport_sha256_no_publisher_hash":h.hexdigest()}

def audit_tar(path,meta,t0):
    first=None;last=None;total=0;shape=None;member_hashes=[]
    book=Book(symbol=meta["instrument"])
    started=False;rejected=None
    source_end=False
    day_ms=int(datetime.strptime(meta["source_day"],"%Y-%m-%d").replace(
        tzinfo=timezone.utc).timestamp()*1000)
    try:
        with open(path,"rb") as source:
            with tarfile.open(fileobj=source,mode="r|gz") as tar:
                for member in tar:
                    if not member.isfile() or member.issym() or member.islnk():
                        raise ValueError("UNSAFE_NONREGULAR_ARCHIVE_MEMBER")
                    if member.size>MAX_UNPACKED:
                        raise ValueError("INFLATED_PAYLOAD_CAP")
                    if (".." in member.name.split("/") or member.name.startswith("/")):
                        raise ValueError("ARCHIVE_UNSAFE_MEMBER_PATH")
                    if not (member.name.endswith(".json") or member.name.endswith(".jsonl")
                            or member.name.endswith(".ndjson")):
                        raise ValueError("UNSUPPORTED_ARCHIVE_MEMBER_EXTENSION")
                    member_hashes.append(hashlib.sha256(member.name.encode()).hexdigest())
                    if len(member_hashes)>3:raise ValueError("TOO_MANY_ARCHIVE_MEMBERS")
                    fh=tar.extractfile(member)
                    if fh is None:raise ValueError("ARCHIVE_MEMBER_NOT_READABLE")
                    for line in fh:
                        total+=1
                        if total>MAX_LINES:raise ValueError("ARCHIVE_RECORD_LIMIT")
                        if len(line)>2_000_000:raise ValueError("NDJSON_LINE_TOO_LARGE")
                        try:doc=json.loads(line)
                        except Exception as exc:raise ValueError("NDJSON_NOT_JSON") from exc
                        if type(doc) is not dict:raise ValueError("NDJSON_ROW_NOT_OBJECT")
                        if shape is None:shape=sorted(doc.keys())
                        stamp=doc.get("ts")
                        if type(stamp) is str and stamp.isdecimal():stamp=int(stamp)
                        if type(stamp) is not int:raise ValueError("NDJSON_NO_TIMESTAMP")
                        if not day_ms<=stamp<day_ms+86400000:
                            raise ValueError("EVENT_OUTSIDE_FROZEN_DAY")
                        if last is not None and stamp<last:
                            raise ValueError("NDJSON_OUT_OF_ORDER")
                        first=stamp if first is None else first
                        if stamp>t0:
                            source_end=True
                            break
                        last=stamp
                        # Exact archive-level instrument provenance (not fabricated individual payload metadata).
                        event=dict(doc)
                        event.setdefault("instId",meta["instrument"])
                        event["ts"]=stamp
                        try:
                            update(book,event)
                            started=True
                        except SourceRejected as exc:
                            rejected=str(exc)
                            raise ValueError("L2_STATE_REPLAY_REJECTED_"+str(exc)) from exc
                    if source_end:break
    except (tarfile.TarError,EOFError) as exc:
        raise ValueError("TAR_GZIP_INVALID") from exc
    if not started:raise ValueError("NO_ACCEPTABLE_PRIOR_COMPLETE_SNAPSHOT")
    if last is None:raise ValueError("NO_SOURCE_RECORD_BEFORE_SIGNAL")
    age=t0-last
    if age<0 or age>2000:raise ValueError("CAUSAL_L2_TOO_STALE")
    if book.sequence_mode is not True:
        # Can parse book but cannot prove incremental continuity without seq chain.
        raise ValueError("L2_SEQUENCE_METADATA_NOT_VERIFIABLE")
    return {"status":"PRELIMINARY_CAUSAL_BOOK_SOURCE_ONLY",
        "archive_member_name_sha256":member_hashes,
        "events_up_to_first_future":total,
        "first_event_time_ms":first,
        "latest_past_event_time_ms":last,
        "signal_quote_age_ms":age,
        "top_level_count_asks":len(book.asks),
        "top_level_count_bids":len(book.bids),
        "source_schema_keys":shape,
        "historical_ctVal_verified":False,
        "prices_or_fills_exported":False}

def run(case):
    fam,inst,day,epoch=case
    result={"symbol":inst,"day":day,"signal_ms":CASES_AT_T0[fam],
            "state":"SOURCE_BLOCKED","reason":"",
            "raw_data_published":False,"market_prices_exported":False,
            "proven_historical_ctVal":False,"broker_fill_proven":False,"live_go":False}
    try:
        meta=metadata(case)
        result.update({"reported_archive_MB":meta["reported_MB"],
            "catalogue_sha256":meta["catalogue_sha256"],
            "file_basename_sha256":hashlib.sha256(meta["filename"].encode()).hexdigest()})
        with tempfile.TemporaryDirectory(prefix="okx-l2-personal-v05b-") as root:
            path=Path(root)/"archive-private.tar.gz"
            transfer=download_to_temp(meta,path)
            result.update(transfer)
            result.update(audit_tar(path,meta,CASES_AT_T0[fam]))
            result["state"]=result.pop("status")
    except urllib.error.HTTPError as exc:
        result["reason"]="HTTP_"+str(exc.code)
    except Exception as exc:
        result["reason"]=type(exc).__name__+":"+str(exc)[:150]
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=[]
    for case in CASES:
        x=run(case)
        result.append(x)
        print("V05B_ARCHIVE_GATE",json.dumps(x,sort_keys=True),flush=True)
    doc={"status":"TWO_RAW_ARCHIVE_SOURCE_RESEARCH_ONLY",
        "cases":len(result),"outputs":result,
        "source_download_is_publisher_checksum_verified":False,
        "historical_broker_fill_proven":False,
        "trading_authority":"NONE"}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"V05B_TWO_RAW_ARCHIVE_CUSTODY_ONLY.json").write_text(
        json.dumps(doc,indent=2,sort_keys=True)+"\n")
    print("V05B_SOURCE_VERDICT",doc["status"])
if __name__=="__main__":main()
