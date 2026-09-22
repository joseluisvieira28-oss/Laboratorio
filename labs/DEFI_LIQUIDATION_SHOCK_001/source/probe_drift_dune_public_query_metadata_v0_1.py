#!/usr/bin/env python3
import hashlib, html, json, re, subprocess
from pathlib import Path

QUERIES=[
  {"id":4226524,"url":"https://dune.com/queries/4226524/7110114","expected":"borrowForPerpPnl"},
  {"id":2680764,"url":"https://dune.com/queries/2680764","expected":"liquidateSpot"},
  {"id":3739506,"url":"https://dune.com/queries/3739506/6289034","expected":"Liquidation Txs V3"},
]
MAX_BYTES=8*1024*1024
rows=[]
sql_hits=[]

def fetch(q):
    p=Path(f"dune_query_{q['id']}.html")
    cmd=["curl","-sS","-L","--proto","=https","--proto-redir","=https",
         "--connect-timeout","20","--max-time","60","--max-filesize",str(MAX_BYTES),
         "-A","crypto-lab-dls-source-metadata/0.1","-o",str(p),
         "-w","%{http_code}\n%{url_effective}\n%{size_download}\n",q["url"]]
    r=subprocess.run(cmd,capture_output=True,text=True)
    lines=(r.stdout or "").splitlines()
    status=int(lines[0]) if lines and lines[0].isdigit() else None
    effective=lines[1] if len(lines)>1 else None
    return p,r.returncode,status,effective

for q in QUERIES:
    p,rc,status,effective=fetch(q)
    rec={"query_id":q["id"],"url":q["url"],"expected_title_token":q["expected"],
         "returncode":rc,"http_status":status,"effective_url":effective}
    if p.exists():
        raw=p.read_bytes()
        rec["bytes"]=len(raw)
        rec["sha256"]=hashlib.sha256(raw).hexdigest()
        text=raw.decode("utf-8","replace")
        low=text.lower()
        rec["query_id_present"]=str(q["id"]) in text
        rec["expected_token_present"]=q["expected"].lower() in low

        # Search only embedded JSON/string metadata fields commonly used for query text.
        patterns=[
          r'"querySql"\s*:\s*"((?:\\.|[^"\\])*)"',
          r'"query_sql"\s*:\s*"((?:\\.|[^"\\])*)"',
          r'"sql"\s*:\s*"((?:\\.|[^"\\]){20,})"',
          r'"queryText"\s*:\s*"((?:\\.|[^"\\]){20,})"',
        ]
        found=[]
        for pat in patterns:
            for m in re.finditer(pat,text,re.I):
                val=m.group(1)
                try:
                    val=json.loads('"'+val+'"')
                except Exception:
                    val=html.unescape(val.replace("\\n","\n"))
                if any(tok in val.lower() for tok in ["select "," from ","with "]):
                    found.append(val)
        # Dedup and hash SQL; preserve exact SQL only if public page exposed it.
        uniq=[]
        seen=set()
        for v in found:
            h=hashlib.sha256(v.encode()).hexdigest()
            if h in seen: continue
            seen.add(h)
            uniq.append({"sha256":h,"bytes":len(v.encode()),"sql":v})
        rec["public_sql_candidates"]=uniq
        if uniq:
            sql_hits.append(q["id"])
    rows.append(rec)

reachable=[r for r in rows if r.get("http_status")==200 and r.get("bytes",0)>0]
if sql_hits:
    classification="DRIFT_DUNE_PUBLIC_QUERY_METADATA_PASS"
elif reachable:
    classification="DRIFT_DUNE_PUBLIC_QUERY_METADATA_NO_SQL"
else:
    classification="DRIFT_DUNE_PUBLIC_QUERY_METADATA_BLOCKED"

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,"rows":rows,"sql_query_ids":sql_hits,
 "firewall":{"query_execution":False,"result_rows":False,"prices":False,"returns":False,
             "pnl":False,"direction":False,"protected_market_outcomes_2025_2026":False,
             "credentials":False,"account_creation":False,"paid_source":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "merge_main":False}
}
Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_DUNE_PUBLIC_QUERY_METADATA_PROBE_RECEIPT_V0.1.json").write_text(
 json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in receipt.items() if k!="rows"}|{"rows_summary":[
 {"query_id":r["query_id"],"http_status":r.get("http_status"),"bytes":r.get("bytes"),
  "query_id_present":r.get("query_id_present"),"expected_token_present":r.get("expected_token_present"),
  "public_sql_candidates":len(r.get("public_sql_candidates",[]))} for r in rows]},indent=2,sort_keys=True))
