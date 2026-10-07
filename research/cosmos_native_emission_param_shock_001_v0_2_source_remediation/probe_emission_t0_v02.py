#!/usr/bin/env python3
import json, urllib.request, urllib.error, ssl, time, hashlib, os
from datetime import datetime, timezone

UA = {"User-Agent": "CryptoLab-Source-Remediation/0.2"}

EVENTS = {
    "SCRT": {
        "proposal_id": None,
        "title_contains": "9% Temporary Inflation",
        "rpc": ["https://rpc.archive.scrt.marionode.com"],
        "api": ["https://lcd.archive.scrt.marionode.com", "https://public.stakewolle.com/cosmos/secretnetwork/rest"],
        "target_hint": "2023-12-07T00:00:00Z",
        "max_probe": 16000000,
    },
    "OSMO": {
        "proposal_id": "539",
        "rpc": ["https://rpc.archive.osmosis.zone", "https://rpc.archive.osmosis.validatus.com", "https://osmosis-rpc.polkachu.com"],
        "api": ["https://lcd.osmosis.zone", "https://osmosis-api.polkachu.com"],
        "target_hint": "2023-06-21T00:00:00Z",
        "max_probe": 16000000,
    },
    "AKT265": {
        "proposal_id": "265",
        "rpc": ["https://akash-rpc.polkachu.com", "https://akash-rpc.publicnode.com", "https://rpc.akashnet.net"],
        "api": ["https://akash-api.polkachu.com"],
        "target_hint": "2024-08-08T00:00:00Z",
        "max_probe": 30000000,
    },
    "AKT283": {
        "proposal_id": "283",
        "rpc": ["https://akash-rpc.polkachu.com", "https://akash-rpc.publicnode.com", "https://rpc.akashnet.net"],
        "api": ["https://akash-api.polkachu.com"],
        "target_hint": "2025-03-13T00:00:00Z",
        "max_probe": 35000000,
    },
    "CTK38": {
        "proposal_id": "38",
        "rpc": ["https://shentu-rpc.polkachu.com"],
        "api": ["https://shentu-api.polkachu.com"],
        "target_hint": "2024-03-28T00:00:00Z",
        "max_probe": 30000000,
    },
    "KAVA": {
        "proposal_id": None,
        "rpc": ["https://rpc.data.kava.io"],
        "api": ["https://api.data.kava.io"],
        "target_hint": "2024-01-01T00:00:00Z",
        "max_probe": 10000000,
        "special": "inflation_stop",
    }
}

def get_json(url, timeout=15, headers=None):
    h = dict(UA)
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            return json.loads(r.read().decode("utf-8")), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def parse_dt(s):
    if not s: return None
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(timezone.utc)

def block_at(rpc, h):
    j,e=get_json(f"{rpc.rstrip('/')}/block?height={h}")
    if e or not j or "result" not in j or not j["result"]:
        return None,e or "no result"
    try:
        hdr=j["result"]["block"]["header"]
        return {"height":int(hdr["height"]), "time":hdr["time"], "hash":j["result"].get("block_id",{}).get("hash")},None
    except Exception as x:
        return None,f"parse: {x}"

def results_at(rpc,h):
    return get_json(f"{rpc.rstrip('/')}/block_results?height={h}")

def find_proposal(api_list, pid=None, title_contains=None):
    out=[]
    if pid:
        paths=[f"/cosmos/gov/v1/proposals/{pid}", f"/cosmos/gov/v1beta1/proposals/{pid}"]
        for api in api_list:
            for p in paths:
                j,e=get_json(api.rstrip('/')+p)
                out.append({"api":api,"path":p,"error":e,"ok":bool(j)})
                if j:
                    prop=j.get("proposal",j.get("result",j))
                    return prop,out
        return None,out
    # bounded historical proposal-ID search, no unbounded latest-state query.
    for candidate in range(250, 351):
        for api in api_list:
            for p in [f"/cosmos/gov/v1/proposals/{candidate}", f"/cosmos/gov/v1beta1/proposals/{candidate}"]:
                j,e=get_json(api.rstrip('/')+p)
                if not j: continue
                prop=j.get("proposal",j.get("result",j))
                title=(prop.get("title") or prop.get("content",{}).get("title") or
                       prop.get("messages",[{}])[0].get("content",{}).get("title") if prop.get("messages") else "")
                desc=prop.get("summary") or prop.get("description") or prop.get("content",{}).get("description","")
                blob=(str(title)+" "+str(desc)).lower()
                if title_contains.lower() in blob:
                    out.append({"api":api,"path":p,"matched":True})
                    return prop,out
        time.sleep(0.02)
    return None,out

def prop_times(prop):
    if not prop: return {}
    return {
        "id": str(prop.get("id") or prop.get("proposal_id") or ""),
        "status": prop.get("status"),
        "submit_time": prop.get("submit_time"),
        "voting_start_time": prop.get("voting_start_time"),
        "voting_end_time": prop.get("voting_end_time"),
        "title": prop.get("title") or prop.get("content",{}).get("title"),
    }

def bracket_and_bisect(rpcs,target,max_probe):
    # fixed historical probes only. No /status and no latest block.
    target_dt=parse_dt(target)
    attempts=[]
    chosen=None
    lo=None
    hi=None
    # 500k fixed-height ladder
    for rpc in rpcs:
        last_valid=None
        last_before=None
        for h in range(500000, max_probe+1, 500000):
            b,e=block_at(rpc,h)
            attempts.append({"rpc":rpc,"height":h,"error":e,"time":b["time"] if b else None})
            if not b:
                # endpoint may prune low heights; continue a few times
                continue
            last_valid=b
            t=parse_dt(b["time"])
            if t < target_dt:
                last_before=b
                continue
            hi=b
            lo=last_before
            chosen=rpc
            break
        if chosen and lo and hi:
            break
    if not (chosen and lo and hi):
        return None,attempts
    l,r=lo["height"],hi["height"]
    # deterministic binary search to first block time >= target
    while l+1<r:
        m=(l+r)//2
        b,e=block_at(chosen,m)
        attempts.append({"rpc":chosen,"height":m,"error":e,"time":b["time"] if b else None})
        if not b:
            # cannot safely infer through a gap
            return None,attempts
        if parse_dt(b["time"]) < target_dt:
            l=m
        else:
            r=m
    b,e=block_at(chosen,r)
    if e: return None,attempts
    prev,_=block_at(chosen,r-1)
    return {"rpc":chosen,"first_ge":b,"prev":prev},attempts

def flatten(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            yield str(k)
            yield from flatten(v)
    elif isinstance(obj,list):
        for v in obj: yield from flatten(v)
    else:
        yield str(obj)

def event_evidence(rpc, center, needles):
    rows=[]
    for h in range(max(1,center-3),center+4):
        j,e=results_at(rpc,h)
        blob=" ".join(flatten(j)).lower() if j else ""
        hits=[n for n in needles if n.lower() in blob]
        rows.append({"height":h,"error":e,"hits":hits,
                     "digest":hashlib.sha256(json.dumps(j,sort_keys=True).encode()).hexdigest() if j else None})
    return rows

report={"generated_at":datetime.now(timezone.utc).isoformat(),"events":{}}

for name,cfg in EVENTS.items():
    only=os.environ.get("ONLY_EVENT")
    if only and name != only:
        continue
    row={"config":cfg}
    if name!="KAVA":
        prop,trail=find_proposal(cfg["api"],cfg.get("proposal_id"),cfg.get("title_contains"))
        row["proposal_lookup"]=trail
        row["proposal"]=prop_times(prop)
        target=row["proposal"].get("voting_end_time") or cfg["target_hint"]
    else:
        target=cfg["target_hint"]
        row["proposal"]={"special":"time-triggered Kava community-module inflation disable",
                         "target_time":target}
    row["target_boundary"]=target
    found,attempts=bracket_and_bisect(cfg["rpc"],target,cfg["max_probe"])
    row["block_search"]=found
    row["probe_count"]=len(attempts)
    row["probe_tail"]=attempts[-12:]
    if found:
        center=found["first_ge"]["height"]
        needles=["inflation_stop"] if name=="KAVA" else [
            str(row["proposal"].get("id","")),
            "proposal_id","proposal","passed","param_change","update_params"
        ]
        needles=[n for n in needles if n]
        row["block_results_evidence"]=event_evidence(found["rpc"],center,needles)
        # exact boundary criterion: prev < target <= first_ge
        try:
            row["canonical_time_bracket_ok"] = (
                parse_dt(found["prev"]["time"]) < parse_dt(target) <= parse_dt(found["first_ge"]["time"])
            )
        except Exception:
            row["canonical_time_bracket_ok"]=False
    report["events"][name]=row

print("===EMISSION_T0_RECOVERY_JSON===")
print(json.dumps(report,indent=2,sort_keys=True))
outfile = "emission_t0_recovery_" + (os.environ.get("ONLY_EVENT","ALL").lower()) + "_v02.json"
with open(outfile,"w") as f:
    json.dump(report,f,indent=2,sort_keys=True)
