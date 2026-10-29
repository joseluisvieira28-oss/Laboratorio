#!/usr/bin/env python3
"""Verify completed GitHub Actions artifact server-side *before expiry*.

Private repository access is GitHub's narrow ACTIONS:READ ephemeral token only.
NO exchange account, trading, or public market outcome queries.
"""
import argparse,datetime as dt,hashlib,io,json,os,pathlib,re,urllib.parse,urllib.request,zipfile
from nvda_event10m_expiry_shadow_v06 import digest

API="https://api.github.com"
REPO="joseluisvieira28-oss/Laboratorio"
ARTIFACT_NAME="nvda-event10m-preoutcome-decision"
MAX_ZIP=3_000_000
SHA=re.compile(r"^[0-9a-f]{64}$")
def parse_utc(value):
    d=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if d.utcoffset()!=dt.timedelta(): raise ValueError("TIMEZONE_NOT_UTC")
    return int(d.timestamp()*1000)
def verify_metadata(metadata, obj, expected_run_id, artifact_id):
    if type(metadata.get("id")) is not int or metadata["id"]!=artifact_id:
        raise ValueError("WRONG_ARTIFACT_ID")
    if metadata.get("name")!=ARTIFACT_NAME or metadata.get("expired") is not False:
        raise ValueError("WRONG_OR_EXPIRED_ARTIFACT")
    x=metadata.get("workflow_run") or {}
    if type(x.get("id")) is not int or x["id"]!=expected_run_id:
        raise ValueError("WRONG_PRODUCING_WORKFLOW_RUN")
    if x.get("head_repository_id") is None and x.get("repository_id") is None:
        # workflow_run fields vary; verify run via separate API too.
        pass
    created_ms=parse_utc(metadata["created_at"])
    d=int((obj.get("forecast") or {}).get("decision_ts_ms",0))
    target=int((obj.get("forecast") or {}).get("expiry_target_ms",0))
    if obj.get("study")!="NVIDIA_EVENT10M_INTEGRATED_V05" or target!=d+600000:
        raise ValueError("WRONG_PREOUTCOME_DECISION")
    if not (d-1000<=created_ms<target):
        raise ValueError("SERVER_ARTIFACT_NOT_BEFORE_EXPIRY")
    raw_digest=metadata.get("digest")
    if not isinstance(raw_digest,str) or not raw_digest.startswith("sha256:"):
        raise ValueError("MISSING_GITHUB_ARTIFACT_DIGEST")
    expected_zip=raw_digest.removeprefix("sha256:")
    if not SHA.fullmatch(expected_zip):
        raise ValueError("BAD_SERVER_ARTIFACT_DIGEST")
    return created_ms,expected_zip

def verify_zip(raw, expected_zip_digest, decision_bytes):
    if len(raw)>MAX_ZIP or hashlib.sha256(raw).hexdigest()!=expected_zip_digest:
        raise ValueError("ZIP_HASH_MISMATCH_OR_TOO_LARGE")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if names!=["decision.json"]:
            raise ValueError("ARTIFACT_NOT_EXACT_ONE_DECISION")
        info=z.getinfo(names[0])
        if info.file_size>2_000_000 or info.is_dir():
            raise ValueError("BAD_ZIP_MEMBER")
        archived=z.read(names[0])
        if archived!=decision_bytes:
            raise ValueError("DECISION_BYTES_NOT_IDENTICAL_TO_SERVER_ARCHIVE")
    return hashlib.sha256(archived).hexdigest()

def get_json(url, token):
    req=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json",
      "Authorization":"Bearer "+token,"X-GitHub-Api-Version":"2022-11-28",
      "User-Agent":"CryptoLab-Custody-GithubOnly-v07"})
    with urllib.request.urlopen(req,timeout=20) as r:
        if r.status!=200:raise RuntimeError("GITHUB_API_NOT_200")
        body=r.read(200_001)
    if len(body)>200_000:raise RuntimeError("GITHUB_JSON_TOO_LARGE")
    return json.loads(body)

class NoCrossHostTokenRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        dest=urllib.parse.urlparse(newurl)
        if dest.scheme!="https":
            raise RuntimeError("UNSAFE_ARTIFACT_REDIRECT")
        src=urllib.parse.urlparse(req.full_url)
        h={k:v for k,v in req.header_items() if k.lower()!="authorization"}
        if dest.hostname==src.hostname:
            h["Authorization"]=req.get_header("Authorization","")
        return urllib.request.Request(newurl,headers=h,method="GET")

def get_zip(url,token):
    handler=urllib.request.build_opener(NoCrossHostTokenRedirect())
    req=urllib.request.Request(url,headers={
      "Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
      "User-Agent":"CryptoLab-Custody-GithubOnly-v07"})
    with handler.open(req,timeout=30) as r:
        raw=r.read(MAX_ZIP+1)
    if len(raw)>MAX_ZIP:raise RuntimeError("GITHUB_ARCHIVE_TOO_LARGE")
    return raw

def verify_remote(decision_path,run_id,artifact_id,token,repo=REPO,allow_synthetic=False):
    if repo!=REPO or not token:raise ValueError("WRONG_REPOSITORY_OR_MISSING_GITHUB_TOKEN")
    decision_bytes=pathlib.Path(decision_path).read_bytes()
    obj=json.loads(decision_bytes)
    if allow_synthetic:
        if obj.get("synthetic_fixture") is not True:
            raise ValueError("TEST_ONLY_MODE_REQUIRES_SYNTHETIC_FIXTURE")
    else:
        if obj.get("synthetic_fixture") is True:
            raise ValueError("SYNTHETIC_RECEIPT_CANNOT_BE_PROMOTED")
        from nvda_event10m_forecast_v01 import slot
        slot(int((obj.get("forecast") or {}).get("decision_ts_ms",0)))
    meta=get_json(f"{API}/repos/{REPO}/actions/artifacts/{artifact_id}",token)
    created,digest_zip=verify_metadata(meta,obj,run_id,artifact_id)
    run=get_json(f"{API}/repos/{REPO}/actions/runs/{run_id}",token)
    if run.get("id")!=run_id or run.get("repository",{}).get("full_name")!=REPO:
        raise ValueError("SERVER_WORKFLOW_RUN_REPO_MISMATCH")
    raw=get_zip(f"{API}/repos/{REPO}/actions/artifacts/{artifact_id}/zip",token)
    artifact_file_hash=verify_zip(raw,digest_zip,decision_bytes)
    d=int(obj["forecast"]["decision_ts_ms"])
    target=int(obj["forecast"]["expiry_target_ms"])
    return {
      "anchor_protocol":"GITHUB_API_ZIP_BYTE_CUSTODY_V07_SYNTHETIC_TEST_ONLY" if allow_synthetic else "GITHUB_API_ZIP_BYTE_CUSTODY_V07",
      "decision_canonical_sha256":digest(obj),
      "decision_exact_bytes_sha256":artifact_file_hash,
      "published_ms":created,
      "decision_ms":d,"expiry_target_ms":target,
      "github_artifact_id":artifact_id,"github_artifact_digest_sha256":digest_zip,
      "github_workflow_run_id":run_id,"github_repository":REPO,
      "custody_independently_authenticated":True,
      "status":"SYNTHETIC_CUSTODY_TEST_ONLY" if allow_synthetic else "SERVER_ARCHIVE_AND_PRE_EXPIRY_TIME_VERIFIED"
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--decision",required=True)
    p.add_argument("--artifact-id",type=int,required=True)
    p.add_argument("--run-id",type=int,required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--synthetic-test-only",action="store_true")
    args=p.parse_args()
    anchor=verify_remote(args.decision,args.run_id,args.artifact_id,
                         os.environ.get("GITHUB_TOKEN",""),allow_synthetic=args.synthetic_test_only)
    path=pathlib.Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(anchor,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in anchor.items() if "sha256" not in k},indent=2))
if __name__=="__main__":main()
