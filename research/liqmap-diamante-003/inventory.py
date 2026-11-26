#!/usr/bin/env python3
"""LIQMAP003 metadata-only free source audit, no financial accounts or paid downloads."""
import collections
import datetime as dt
import hashlib
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"results"
UA={"User-Agent":"CryptoLab-LIQMAP003-Public-Archive-Research/1.0","Accept":"application/vnd.github+json,application/json"}
GITHUB="https://api.github.com/repos/rdemb/hyperquant-data/"
HF="https://huggingface.co/api/datasets/"
DATASETS=("Hydromancer/hyperliquid-reservoir","ProbioticFarmer/hyperliquid-augmented-copytrading")
def get(url,report,limit=3_500_000):
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    request=urllib.request.Request(url,headers=UA)
    status=None;raw=b"";err=None
    try:
        with urllib.request.urlopen(request,timeout=40) as f:
            status=f.status
            raw=f.read(limit+1)
    except urllib.error.HTTPError as e:
        status=e.code
        raw=e.read(3000)
        err="HTTP "+str(e.code)
    except Exception as e:
        err=type(e).__name__+": "+str(e)
    end=dt.datetime.now(dt.timezone.utc).isoformat()
    report["receipts"].append({"url":url,"start_utc":start,"end_utc":end,
           "http_status":status,"bytes":len(raw),"raw_sha256":hashlib.sha256(raw).hexdigest(),
           "error":err,"over_limit":len(raw)>limit})
    if err or len(raw)>limit:raise ValueError(err or "RESPONSE_SIZE_BLOCKED")
    return json.loads(raw)

def check_hyperquant(report):
    out={}
    u=GITHUB+"commits?"+urllib.parse.urlencode({"path":"liq-map/BTC.json","per_page":100})
    commits=get(u,report)
    if not isinstance(commits,list):raise ValueError("GitHub commits not list")
    out["reachable_map_commits_first_page"]=len(commits)
    out["map_commits"]=[{"sha":x.get("sha"),"published_utc":x.get("commit",{}).get("committer",{}).get("date"),
                      "message":x.get("commit",{}).get("message","")[:90],
                      "parents":len(x.get("parents",[]))} for x in commits[:5]]
    out["oldest_reachable_map_commit_utc"]=out["map_commits"][-1]["published_utc"] if out["map_commits"] else None
    # This query has max 100 results per page. If exactly 100 further pages required.
    out["history_complete"]=len(commits)<100
    for branch in ("main","history","ledger","archive"):
        url=GITHUB+"contents/liq-map/BTC.json?"+urllib.parse.urlencode({"ref":branch})
        try:
            obj=get(url,report,120_000)
            out["map_exists_on_"+branch]=obj.get("type")=="file"
            out[branch+"_map_sha"]=obj.get("sha")
        except Exception as e:
            out["map_exists_on_"+branch]=False
            out[branch+"_map_check"]=str(e)[:140]
    for branch in ("main","history"):
        try:
            src=get(GITHUB+"contents/README.md?"+urllib.parse.urlencode({"ref":branch}),report,120_000)
            import base64
            body=base64.b64decode(src["content"]).decode("utf-8","replace")
            out[branch+"_README_one_commit_explicit"]=("jeden commit" in body)
            out[branch+"_README_rolling_seven_days"]=("7 dni" in body or "ostatnich dni" in body)
            out[branch+"_README_mentions_liq_map"]=("liq-map/BTC.json" in body)
        except Exception as e:out[branch+"_README_error"]=str(e)[:130]
    try:
        obj=get(GITHUB+"contents/BTC/2026-11-25.jsonl?ref=ledger",report,2_800_000)
        import base64
        rows=[json.loads(r) for r in base64.b64decode(obj["content"]).decode().splitlines() if r.strip()]
        out["ledger_2026_11_25_records"]=len(rows)
        out["ledger_kind_counts"]=dict(collections.Counter(r.get("kind",r.get("k")) for r in rows))
        out["ledger_actual_liq_map_records"]=sum(
            isinstance(r.get("longs"),list) and isinstance(r.get("shorts"),list) and
            isinstance(r.get("coverage"),dict) for r in rows)
    except Exception as e:out["ledger_error"]=str(e)[:140]
    return out

def hf_tree(repo,path,report):
    parts=path.strip("/")
    base=HF+repo+"/tree/main"+("/"+urllib.parse.quote(parts,safe="/") if parts else "")
    return get(base+"?recursive=true&limit=1000",report,4_000_000)

def hf_inventory(report,repo,preferred):
    result={"repo":repo}
    try:
        root=hf_tree(repo,"",report)
        if not isinstance(root,list):raise ValueError("not an HF tree")
        result["root_entries"]=[{"path":x.get("path"),"type":x.get("type")} for x in root[:100]]
        candidates=[x.get("path") for x in root if
             any(key in x.get("path","").lower() for key in ("position","snapshot"))]
        # Public HF tree root is recursively paginated and may list >1000
        # nested account_values paths before snapshots_perp appears. Query
        # the known folder DIRECTLY; absence from a partial root page
        # is NOT evidence of no archive.
        folder=preferred
        result["selected_tree_folder"]=folder
        if folder is None:
            result["status"]="NO_POSITION_TREE"
            return result
        nodes=hf_tree(repo,folder,report)
        if not isinstance(nodes,list):raise ValueError("no HF nodes")
        files=[x for x in nodes if x.get("type")=="file"]
        result["file_count_first_page"]=len(files)
        result["limit_reached_more_pages_possible"]=len(nodes)>=1000
        m=re.compile(r"(20\d\d-\d\d-\d\d)")
        dates=sorted({d for x in files for d in m.findall(x.get("path",""))})
        result["unique_filename_dates"]=len(dates)
        result["first_filename_date"]=dates[0] if dates else None
        result["last_filename_date"]=dates[-1] if dates else None
        result["sample_first"]=[{"path":x.get("path"),"bytes":x.get("size",x.get("lfs",{}).get("size")),
           "oid":x.get("lfs",{}).get("oid")} for x in files[:4]]
        result["sample_last"]=[{"path":x.get("path"),"bytes":x.get("size",x.get("lfs",{}).get("size")),
           "oid":x.get("lfs",{}).get("oid")} for x in files[-4:]]
        result["files_bytes_reported"]=sum((x.get("size") or x.get("lfs",{}).get("size") or 0) for x in files)
        result["files_without_date_sample"]=[x.get("path") for x in files if not m.search(x.get("path",""))][:7]
        result["status"]="METADATA_PASS"
    except Exception as e:
        result["status"]="SOURCE_BLOCKED"
        result["reason"]=type(e).__name__+": "+str(e)
    return result

def blocklens(report):
    result={"published_docs":"https://docs.blocklens.co/api/liquidation-map-api",
            "free_history_days_docs":30,"pro_full_history":"since 2025-07-29",
            "requires_api_key_even_free":True}
    url="https://api.blocklens.co/v1/liqmap/meta"
    try:
        r=get(url,report,200_000)
        result["no_key_status"]="PUBLIC_READ_UNEXPECTED"
        result["keys"]=list(r)[:15]
    except Exception as e:result["no_key_status"]="AUTH_OR_SOURCE_BLOCKED";result["error"]=str(e)[:150]
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r={"study":"LIQMAP-DIAMANTE-003","date":"2026-11-26",
        "no_trades":True,"no_paid_downloads":True,"no_aws_requester_pays":True,
        "proprietary_Neuron_backtest":False,"receipts":[]}
    try:r["hyperquant"]=check_hyperquant(r)
    except Exception as e:r["hyperquant"]={"status":"SOURCE_BLOCKED","error":str(e)}
    r["free_alternatives"]=[hf_inventory(r,DATASETS[0],"positions"),
                            hf_inventory(r,DATASETS[1],"snapshots_perp")]
    r["blocklens"]=blocklens(r)
    h=r["hyperquant"]
    r["historical_hyperquant_replay_ready"]=(h.get("reachable_map_commits_first_page",0)>=60 and h.get("history_complete"))
    r["verdict"]="HYPERQUANT_HISTORICAL_SOURCE_INSUFFICIENT" if not r["historical_hyperquant_replay_ready"] else "POTENTIAL_MAP_HISTORY_CHECK_NEEDED"
    (OUT/"INVENTORY.json").write_text(json.dumps(r,indent=2)+"\n")
    lines=["# LIQMAP-003 — Forensic archive inventory, no trades","",
      "## Exact HyperQuant 60–180d as-of map history", "",
      "Available map commits: "+str(h.get("reachable_map_commits_first_page")),
      "Oldest reachable commit UTC: "+str(h.get("oldest_reachable_map_commit_utc")),
      "The public branch main keeps current state, not 60–180 prior maps. Other branches do not contain the map file.",
      "Ledger records from another model and 7-day tape/book are NOT the older actual liquidation map.",
      "", "## Alternative public positions snapshot trees", ""]
    for x in r["free_alternatives"]:
        lines += ["- "+x["repo"]+": "+x["status"]+", candidate files "+str(x.get("file_count_first_page")),
                  "  snapshot dates "+str(x.get("unique_filename_dates"))+
                  " from "+str(x.get("first_filename_date"))+" to "+str(x.get("last_filename_date")),
                  "  total bytes reported (first page): "+str(x.get("files_bytes_reported"))]
    lines+=["","## Blocklens access",
      "Requires a user API key even on free tier, which grants last 30 days only. No key supplied; no login/payment attempted.",
      "", "## Source and economic verdict",
      "A current map cannot be paired retrospectively with earlier price candles: that is future leakage.",
      "HyperQuant exact historical backtest: "+r["verdict"],
      "An independent free-position dataset may permit an original LAB reconstructed-map audit only after verifying free download, actual schema, timestamps, and historical price source.",
      "No profits, win rate, real fills or economic edge have been established by this inventory."]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("LIQMAP003",r["verdict"],"hyperquant commits",h.get("reachable_map_commits_first_page"),
        "alternatives",[(x["repo"],x["status"],x.get("unique_filename_dates"),x.get("file_count_first_page")) for x in r["free_alternatives"]],flush=True)
if __name__=="__main__":main()
