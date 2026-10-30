#!/usr/bin/env python3
"""BTC 10m independent GitHub-server pre-expiry custody for a future Nov PAPER decision.
Verifies full ZIP (decision+8 raw HTTP responses), exact SHA and frozen model re-run.
"""
import argparse,datetime as dt,hashlib,io,json,os,pathlib,re,urllib.request,zipfile
from event10m_spot_depth_divergence_v03 import decide
from btc_event10m_source_gates_v04 import asof
REPO="joseluisvieira28-oss/Laboratorio"
ART_NAME="btc-event10m-preexpiry-source-and-decision"
API="https://api.github.com"
SIZE_MAX=3000000
HEX=re.compile(r"^[a-f0-9]{64}$")
FILES={"okx_book_0.json","okx_book_1.json","okx_book_2.json",
 "mexc_book_0.json","mexc_book_1.json","mexc_book_2.json",
 "mexc_event_contract_detail.json","mexc_index.json"}
def hash_bytes(raw):return hashlib.sha256(raw).hexdigest()
def parse_utc(s):return int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
def validate_decision(obj):
    if (obj.get("study")!="BTC_EVENT10M_V05_FROZEN_PROSPECTIVE_PAPER_ONLY" or
        obj.get("status") not in ("PAPER_FORECAST_UNANCHORED","ABSTAIN_PREEXPIRY")):
        raise ValueError("NOT_A_REAL_BTC_FROZEN_PAPER_DECISION")
    if obj.get("synthetic_fixture") is True:raise ValueError("SYNTHETIC_CANNOT_BE_PROMOTED")
    f=obj.get("forecast") or {};data=obj.get("source_receipt") or {}
    if f.get("study")!="EVENT10M_OKX_SPOT_VS_MEXC_PERP_DIVERGENCE_V03":
        raise ValueError("WRONG_FROZEN_MODEL")
    if f.get("asset")!="BTC_USDT" or f.get("target_ms")!=f.get("decision_ms",0)+600000:
        raise ValueError("WRONG_ASSET_OR_DURATION")
    d=int(f["decision_ms"]);target=int(f["target_ms"])
    if d!=data.get("asof_ms") or obj.get("decision_ms")!=d or obj.get("expiry_target_ms")!=target:
        raise ValueError("DECISION_SOURCE_TIME_MISMATCH")
    if data.get("source_gate_all_pass") is not True or not all(
        asof(data["samples"],data["product"],data["index"],d).values()):
        raise ValueError("SOURCE_NOT_VALIDATED")
    expected=decide("BTC_USDT",d,data["samples"],data["product"],data["index"])
    if expected!=f:raise ValueError("FORECAST_NOT_REPRODUCIBLE_FROM_FROZEN_RULE")
    if (f["side"]=="ABSTAIN")!=(obj["status"]=="ABSTAIN_PREEXPIRY"):
        raise ValueError("ABSTAIN_STATUS_NOT_REPRODUCIBLE")
    return d,target
def server_metadata(meta,obj,run_id,artifact_id):
    d,target=validate_decision(obj)
    if type(meta.get("id")) is not int or meta["id"]!=artifact_id:
        raise ValueError("WRONG_ARTIFACT_ID")
    if meta.get("name")!=ART_NAME or meta.get("expired") is not False:
        raise ValueError("WRONG_ARTIFACT_NAME_OR_EXPIRED")
    if (meta.get("workflow_run") or {}).get("id")!=run_id:
        raise ValueError("WRONG_SERVER_RUN")
    created=parse_utc(meta["created_at"])
    # GitHub created_at has second precision. Cannot accept expiry-or-later.
    if not d-1000<=created<target:
        raise ValueError("GITHUB_ARTIFACT_NOT_PUBLISHED_BEFORE_EXPIRY")
    digest=meta.get("digest","")
    if not isinstance(digest,str) or not digest.startswith("sha256:") or not HEX.fullmatch(digest[7:]):
        raise ValueError("NO_GITHUB_ARCHIVE_DIGEST")
    return created,digest[7:]
def verify_archive(raw,official_zip_sha,decision_raw):
    if len(raw)>SIZE_MAX or hash_bytes(raw)!=official_zip_sha:
        raise ValueError("ARCHIVE_SHA_MISMATCH_OR_SIZE")
    obj=json.loads(decision_raw);validate_decision(obj)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist()
        required={"decision.json"}|{"raw/"+f for f in FILES}
        if set(names)!=required or len(names)!=len(required):
            raise ValueError("SOURCE_ARTIFACT_MEMBERS_MISSING_OR_EXTRA")
        for name in names:
            if archive.getinfo(name).file_size>500000:raise ValueError("SOURCE_MEMBER_SIZE")
        if archive.read("decision.json")!=decision_raw:
            raise ValueError("PRE_EXPIRY_DECISION_BYTES_CHANGED")
        data=obj["source_receipt"];want={}
        for pair in data["samples"]:
            for book in ("okx_spot","mexc_futures"):
                pkt=pair[book];want[pkt["raw_file"]]=pkt["sha256"]
        for k in ("product","index"):
            pkt=data[k];want[pkt["raw_file"]]=pkt["sha256"]
        if set(want)!=FILES:raise ValueError("WRONG_CUSTODIED_HTTP_SOURCE_SET")
        for filename,expected in want.items():
            if not HEX.fullmatch(expected) or hash_bytes(archive.read("raw/"+filename))!=expected:
                raise ValueError("SOURCE_RAW_BYTES_NOT_MATCHING_DECISION_"+filename)
    return hash_bytes(decision_raw)
def github_json(url,token):
    req=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json",
       "Authorization":"Bearer "+token,"X-GitHub-Api-Version":"2022-11-28",
       "User-Agent":"CryptoLab-ReadOnly-BtcEvent10m-Custody"})
    with urllib.request.urlopen(req,timeout=20) as res:
        if res.status!=200:raise ValueError("GITHUB_API_NOT_200")
        raw=res.read(150001)
    if len(raw)>150000:raise ValueError("GITHUB_METADATA_TOO_LARGE")
    return json.loads(raw)
def verify_remote(decision_file,zip_file,run_id,artifact_id,token):
    if not token:raise ValueError("GITHUB_READ_ONLY_TOKEN_MISSING")
    decision_raw=pathlib.Path(decision_file).read_bytes()
    obj=json.loads(decision_raw);validate_decision(obj)
    run=github_json(f"{API}/repos/{REPO}/actions/runs/{run_id}",token)
    if run.get("id")!=run_id or (run.get("repository") or {}).get("full_name")!=REPO:
        raise ValueError("ORIGIN_WORKFLOW_NOT_SAME_REPO")
    meta=github_json(f"{API}/repos/{REPO}/actions/artifacts/{artifact_id}",token)
    created,digest=server_metadata(meta,obj,run_id,artifact_id)
    exact=verify_archive(pathlib.Path(zip_file).read_bytes(),digest,decision_raw)
    return {"study":"BTC_EVENT10M_PREEXPIRY_SOURCE_CUSTODY_V05","status":"GITHUB_SERVER_ARCHIVE_VERIFIED",
      "repo":REPO,"workflow_run_id":run_id,"artifact_id":artifact_id,
      "artifact_created_ms":created,"archive_sha256":digest,
      "decision_exact_bytes_sha256":exact,"decision_ms":obj["decision_ms"],
      "expiry_target_ms":obj["expiry_target_ms"],"independent_custody_proven":True,
      "actual_event_futures_price_parity_proven":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--decision",required=True);p.add_argument("--archive",required=True)
    p.add_argument("--run-id",required=True,type=int);p.add_argument("--artifact-id",required=True,type=int)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    out=verify_remote(args.decision,args.archive,args.run_id,args.artifact_id,
                      os.environ.get("GITHUB_TOKEN",""))
    path=pathlib.Path(args.output);path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("BTC_INDEPENDENT_PREEXPIRY_GITHUB_CUSTODY_PASS",out["artifact_id"])
if __name__=="__main__":main()
