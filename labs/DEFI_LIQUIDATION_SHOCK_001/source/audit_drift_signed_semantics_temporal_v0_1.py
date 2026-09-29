#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, re, subprocess, urllib.request
from pathlib import Path

LOWER="2022-11-04T15:17:54Z"
UPPER="2025-01-01T00:00:00Z"
REPO_ID=497045217
FILES=[
 "programs/drift/src/controller/liquidation.rs",
 "programs/drift/src/math/orders.rs",
 "programs/drift/src/state/user.rs",
 "programs/drift/src/state/events.rs",
]
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_2022_2024_SIGNED_SEMANTICS_TEMPORAL_AUTHORITY_RECEIPT_V0.1.json")

def sh(*args, cwd=None, check=True):
    p=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(f"command_failed rc={p.returncode} cmd={args!r} stderr={p.stderr[:1000]!r}")
    return p.stdout

def git(repo,*args):
    return sh("git",*args,cwd=repo)

def show(repo,commit,path):
    p=subprocess.run(["git","show",f"{commit}:{path}"],cwd=repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:
        return None
    return p.stdout

def brace_block(text,start):
    b=text.find("{",start)
    if b<0: return None
    depth=0
    in_str=False; esc=False; in_char=False
    i=b
    while i<len(text):
        c=text[i]
        if in_str:
            if esc: esc=False
            elif c=="\\": esc=True
            elif c=='"': in_str=False
            i+=1; continue
        if in_char:
            if esc: esc=False
            elif c=="\\": esc=True
            elif c=="'": in_char=False
            i+=1; continue
        if c=='"': in_str=True
        elif c=="'": in_char=True
        elif c=="{": depth+=1
        elif c=="}":
            depth-=1
            if depth==0: return text[start:i+1]
        i+=1
    return None

def fn_block(text,name):
    pats=[rf"\bpub\s+fn\s+{re.escape(name)}\b",rf"\bfn\s+{re.escape(name)}\b"]
    for pat in pats:
        m=re.search(pat,text)
        if m:
            return brace_block(text,m.start())
    return None

def struct_block(text,name):
    m=re.search(rf"\bpub\s+struct\s+{re.escape(name)}\b",text)
    return brace_block(text,m.start()) if m else None

def norm(s):
    if s is None:return None
    s=re.sub(r"//[^\n]*","",s)
    s=re.sub(r"/\*.*?\*/","",s,flags=re.S)
    s=re.sub(r"\s+"," ",s).strip()
    return s

def fields(block):
    if not block:return None
    body=block[block.find("{")+1:block.rfind("}")]
    out=[]
    for m in re.finditer(r"\bpub\s+(\w+)\s*:\s*([^,]+),",body,re.S):
        typ=re.sub(r"\s+"," ",m.group(2)).strip()
        out.append([m.group(1),typ])
    return out

def contains_all(s, needles):
    return s is not None and all(x in s for x in needles)

def state_audit(repo,commit):
    src={p:show(repo,commit,p) for p in FILES}
    errors=[]
    if any(v is None for v in src.values()):
        for p,v in src.items():
            if v is None: errors.append(f"missing_file:{p}")
        return {"commit":commit,"errors":errors}

    orders=fn_block(src[FILES[1]],"get_position_delta_for_fill")
    user_dir=fn_block(src[FILES[2]],"get_direction")
    user_close=fn_block(src[FILES[2]],"get_direction_to_close")
    liq=fn_block(src[FILES[0]],"liquidate_perp")
    lr=struct_block(src[FILES[3]],"LiquidationRecord")
    lpr=struct_block(src[FILES[3]],"LiquidatePerpRecord")

    if not contains_all(norm(orders),[
        "PositionDirection::Long => base_asset_amount.cast()?",
        "PositionDirection::Short => -base_asset_amount.cast()?"
    ]):
        errors.append("position_delta_sign_invariant_unproven")

    nd=norm(user_dir)
    if not (nd and "base_asset_amount >= 0" in nd and
            "PositionDirection::Long" in nd and "PositionDirection::Short" in nd):
        errors.append("existing_position_direction_invariant_unproven")

    nc=norm(user_close)
    if not (nc and "base_asset_amount >= 0" in nc and
            "PositionDirection::Short" in nc and "PositionDirection::Long" in nc):
        errors.append("direction_to_close_invariant_unproven")

    nl=norm(liq)
    if not (nl and re.search(r"user_position_delta\s*=\s*get_position_delta_for_fill\s*\([^;]+get_direction_to_close\s*\(\)",nl)):
        errors.append("liquidated_user_delta_from_direction_to_close_unproven")
    if not (nl and re.search(r"base_asset_amount\s*:\s*user_position_delta\.base_asset_amount",nl)):
        errors.append("liquidation_record_signed_delta_binding_unproven")

    f_lr=fields(lr); f_lpr=fields(lpr)
    if not f_lr:
        errors.append("liquidation_record_layout_unresolved")
    if not f_lpr:
        errors.append("liquidate_perp_record_layout_unresolved")
    if f_lr:
        names=[x[0] for x in f_lr]
        if "liquidate_perp" not in names:
            errors.append("liquidation_record_missing_liquidate_perp")
        else:
            f_lr=f_lr[:names.index("liquidate_perp")+1]
    if f_lpr:
        fmap=dict(f_lpr)
        if fmap.get("base_asset_amount")!="i64":
            errors.append("signed_base_field_not_i64")
        for req in ("market_index","base_asset_amount"):
            if req not in fmap: errors.append(f"liquidate_perp_record_missing_{req}")

    return {
      "commit":commit,
      "errors":errors,
      "orders_semantics_sha256":hashlib.sha256((norm(orders) or "").encode()).hexdigest(),
      "direction_semantics_sha256":hashlib.sha256(((norm(user_dir) or "")+"|"+(norm(user_close) or "")).encode()).hexdigest(),
      "liquidate_perp_semantics_sha256":hashlib.sha256((norm(liq) or "").encode()).hexdigest(),
      "liquidation_record_prefix_fields":f_lr,
      "liquidate_perp_record_fields":f_lpr,
    }

ap=argparse.ArgumentParser()
ap.add_argument("--protocol-repo",required=True)
args=ap.parse_args()
repo=Path(args.protocol_repo)

api=json.load(urllib.request.urlopen(f"https://api.github.com/repositories/{REPO_ID}",timeout=60))
remote=git(repo,"remote","get-url","origin").strip()
default_branch=api.get("default_branch") or "master"
git(repo,"checkout","--detach",f"origin/{default_branch}")
tip=git(repo,"rev-parse","HEAD").strip()

base=git(repo,"rev-list","-1",f"--before={LOWER}",tip).strip()
if not base: raise SystemExit("no_base_commit")

raw=git(repo,"log","--format=%H|%cI","--since="+LOWER,"--until="+UPPER,tip,"--",*FILES)
pairs=[]
for line in raw.splitlines():
    if not line.strip(): continue
    h,t=line.split("|",1);pairs.append((h,t))
pairs.sort(key=lambda x:(x[1],x[0]))
states=[base]+[h for h,_ in pairs if h!=base]
# preserve chronological unique sequence
seen=set();states=[x for x in states if not (x in seen or seen.add(x))]

audits=[]
layout_map={}
for idx,c in enumerate(states):
    rec=state_audit(repo,c)
    rec["committer_date"]=git(repo,"show","-s","--format=%cI",c).strip()
    rec["subject"]=git(repo,"show","-s","--format=%s",c).strip()
    audits.append(rec)
    k=json.dumps({
      "liquidation_record_prefix_fields":rec.get("liquidation_record_prefix_fields"),
      "liquidate_perp_record_fields":rec.get("liquidate_perp_record_fields")
    },sort_keys=True,separators=(",",":"))
    if rec.get("liquidation_record_prefix_fields") and rec.get("liquidate_perp_record_fields"):
        layout_map.setdefault(k,{"first_commit":c,"first_date":rec["committer_date"],"states":0})
        layout_map[k]["states"]+=1

failures=[a for a in audits if a["errors"]]
layouts=[]
for k,v in layout_map.items():
    obj=json.loads(k); obj.update(v)
    obj["layout_id"]="sha256:"+hashlib.sha256(k.encode()).hexdigest()
    layouts.append(obj)
layouts.sort(key=lambda x:(x["first_date"],x["layout_id"]))

classification="DRIFT_2022_2024_SIGNED_SEMANTICS_TEMPORAL_PASS" if not failures and layouts else "DRIFT_2022_2024_SIGNED_SEMANTICS_TEMPORAL_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,
 "interval":{"lower":LOWER,"upper_exclusive":UPPER},
 "source_repository":{
   "expected_repository_id":REPO_ID,"observed_repository_id":api.get("id"),
   "observed_full_name":api.get("full_name"),"default_branch":default_branch,
   "remote_url":remote,"tip":tip
 },
 "state_rule":"latest default-branch state at/before lower bound + every default-branch commit before upper bound touching a frozen target file",
 "target_files":FILES,
 "base_commit":base,
 "state_count":len(audits),
 "failure_count":len(failures),
 "distinct_layout_count":len(layouts),
 "layouts":layouts,
 "failures":[{"commit":x["commit"],"date":x["committer_date"],"subject":x["subject"],"errors":x["errors"]} for x in failures],
 "states":audits,
 "invariants":{
   "long_fill_base_delta":"positive",
   "short_fill_base_delta":"negative",
   "positive_existing_position":"Long",
   "negative_existing_position":"Short",
   "long_closes":"Short",
   "short_closes":"Long",
   "liquidated_user_delta_source":"get_direction_to_close",
   "canonical_signed_field":"LiquidatePerpRecord.base_asset_amount"
 },
 "firewall":{"prices":False,"returns":False,"pnl":False,"market_outcomes":False,
   "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,
   "orders":False,"wallets":False,"exchange_mutation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":classification,
 "repository_id":api.get("id"),"full_name":api.get("full_name"),
 "state_count":len(audits),"failure_count":len(failures),
 "distinct_layout_count":len(layouts),
 "failures":receipt["failures"][:20],
 "layouts":[{"layout_id":x["layout_id"],"first_date":x["first_date"],"states":x["states"],
   "liq_prefix":x["liquidation_record_prefix_fields"],"perp":x["liquidate_perp_record_fields"]} for x in layouts]
},indent=2))
if classification.endswith("_BLOCKED"): raise SystemExit(2)
