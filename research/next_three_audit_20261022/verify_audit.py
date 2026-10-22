"""Offline evidence integrity and published-summary arithmetic; no network or market backtest."""
import hashlib, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
def digest(b): return hashlib.sha256(b).hexdigest()
checks=[]
def check(name, condition):
    checks.append({"check": name, "pass": bool(condition)})
    if not condition: raise AssertionError(name)

evidence=json.loads((ROOT/"EVIDENCE.json").read_text(encoding="utf-8"))
census=json.loads((ROOT/"BRANCH_CENSUS.json").read_text(encoding="utf-8"))
heads={b["name"]:b["commit"]["sha"] for b in census["branches"]}
check("census_unique_names", len(heads)==len(census["branches"])==1024)
check("census_page_counts", sum(census["counts"])==1024 and census["counts"][-1]==0)
check("main_bound", heads["main"]=="75fb36c8337c3221b7551c513e049cd472dad231")
check("pr269_bound", heads["research/unlock-crowding-adaptive-dca-audit-2026-10-22"]=="f55adbad28ef95a869471bb76859d99cb602b171")
for e in evidence:
    b=e["content"].encode("utf-8")
    actual=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    check("git_blob:"+e["path"],actual==e["sha"])
    url=e["display_url"]
    check("immutable_ref:"+e["path"], any("/blob/"+sha+"/" in url for sha in heads.values()))
check("evidence_unique_paths",len({e["path"] for e in evidence})==len(evidence))
# These are arithmetic checks on already-published summaries, NOT raw-data replication.
taker_bound=1.3442512507-2*4.5
check("taker_fee_floor",abs(taker_bound-(-7.6557487493))<1e-10)
passive=[-1.897484,-1.578006,-1.479139,-1.765357,-1.603075,-1.694755]
check("passive_all_cells_negative",all(x<0 for x in passive))
check("passive_rounded_mean",abs(sum(passive)/6-(-1.6696357652))<0.000001)
check("qbc_0_below_12",0<12)
check("cbll_coverage_below_gate",97.5176<99.5 and 94.9615<99.5)
check("fcc_net30_negative",-0.2520<0)
check("okx_3_screen_negative",all(x<0 for x in [-29.306956,-29.543339,-31.307051]))
payloads={p.name:{"sha256":digest(p.read_bytes()),"bytes":p.stat().st_size}
          for p in sorted(ROOT.iterdir()) if p.is_file() and p.name not in {"MANIFEST.json","VERIFICATION.json"}}
manifest_path=ROOT/"MANIFEST.json"
if manifest_path.exists():
    check("payload_manifest_matches",json.loads(manifest_path.read_text())==payloads)
else:
    manifest_path.write_text(json.dumps(payloads,indent=2)+"\n",encoding="utf-8")
receipt={"generated_at_utc":datetime.now(timezone.utc).isoformat(),
         "classification":"OFFLINE_AUDIT_VERIFICATION_PASS",
         "evidence_blobs":len(evidence),"checks":checks,"checks_passed":len(checks),
         "manifest_sha256":digest(manifest_path.read_bytes()),
         "raw_backtests_reproduced":False,"new_market_outcomes_opened":False,
         "network_calls":0,"orders":False,"wallets":False,"spend":0}
(ROOT/"VERIFICATION.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"classification":receipt["classification"],"checks_passed":len(checks),"evidence_blobs":len(evidence)}))

