#!/usr/bin/env python3
import hashlib, json, os, re, subprocess, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUTDIR=os.path.join(os.path.dirname(__file__),"receipts"); os.makedirs(OUTDIR,exist_ok=True)
FREEZE_REL="pressure_mining_v0_1/labs/COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1.md"
FREEZE=os.path.join(ROOT,FREEZE_REL)
EXPECTED_BLOB="d36c24bffd8a0f16787e0b7cf72b2d7b60e2f430"
EXPECTED_COMMIT="2191bbf741ced5f801d8ae4034bd126c3b91cbc8"
BASE="https://data.binance.vision/data/spot/monthly/klines"
SYMBOLS=["BTCUSDT","ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"]
MONTHS=[f"2025-{m:02d}" for m in range(1,13)]
SHA_RE=re.compile(r"^[0-9a-fA-F]{64}$")

def sha(b): return hashlib.sha256(b).hexdigest()
def head(url):
    req=Request(url,method="HEAD",headers={"User-Agent":"CryptoLab-Compound30m-Preflight-V0.1"})
    with urlopen(req,timeout=45) as r:
        return {"status":r.status,"length":int(r.headers.get("Content-Length") or 0),"etag":r.headers.get("ETag")}
def get_text(url):
    req=Request(url,headers={"User-Agent":"CryptoLab-Compound30m-Preflight-V0.1","Accept":"text/plain"})
    with urlopen(req,timeout=45) as r:
        raw=r.read()
    return raw.decode(errors="replace"),sha(raw)

receipt={"program":"COMPOUND_REALIZED_DISPOSAL_30M_PREOUTCOME_PREFLIGHT_V0.1",
"lab_id":"COMPOUND-REALIZED-DISPOSAL-FLOW-001",
"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
"canonical_authority":{"file":FREEZE_REL,"commit":EXPECTED_COMMIT,"expected_git_blob":EXPECTED_BLOB},
"firewall":{"outcome_blind":True,"zip_content_downloaded":False,"kline_rows_opened":False,
"market_price_values_opened":False,"returns_computed_from_real_data":False,"pnl_computed_from_real_data":False,
"protected_2025_market_outcomes_opened":False,"protected_2026_market_outcomes_opened":False,
"live_trading":False,"orders":False,"exchange_mutation":False,"capital":False,"main_merge":False}}

try:
    blob=subprocess.check_output(["git","hash-object",FREEZE],cwd=ROOT,text=True).strip()
    identity_ok=(blob==EXPECTED_BLOB)

    objects=[]
    for sym in SYMBOLS:
        for ym in MONTHS:
            zip_url=f"{BASE}/{sym}/1m/{sym}-1m-{ym}.zip"
            chk_url=zip_url+".CHECKSUM"
            rec={"symbol":sym,"month":ym,"zip_url":zip_url,"checksum_url":chk_url}
            try:
                hz=head(zip_url)
                rec["zip_status"]=hz["status"]; rec["zip_content_length"]=hz["length"]; rec["zip_available"]=hz["status"]==200 and hz["length"]>0
            except Exception as e:
                rec["zip_available"]=False; rec["zip_error"]=repr(e)
            try:
                txt,ch= get_text(chk_url)
                tok=txt.strip().split()[0] if txt.strip() else ""
                rec["checksum_status"]=200
                rec["checksum_file_sha256"]=ch
                rec["checksum_token"]=tok.lower()
                rec["checksum_token_valid"]=bool(SHA_RE.match(tok))
                rec["checksum_available"]=True
            except Exception as e:
                rec["checksum_available"]=False; rec["checksum_token_valid"]=False; rec["checksum_error"]=repr(e)
            objects.append(rec)

    zip_ok=sum(bool(x.get("zip_available")) for x in objects)
    chk_ok=sum(bool(x.get("checksum_available")) for x in objects)
    tok_ok=sum(bool(x.get("checksum_token_valid")) for x in objects)
    status="SOURCE_OBJECT_PREFLIGHT_PASS" if identity_ok and zip_ok==60 and chk_ok==60 and tok_ok==60 else "SOURCE_OBJECT_PREFLIGHT_FAIL"
    receipt.update({"status":status,"canonical_identity":{"actual_git_blob":blob,"exact_match":identity_ok},
      "coverage":{"required_objects":60,"zip_available":zip_ok,"checksum_available":chk_ok,"checksum_token_valid":tok_ok,
                  "symbols":SYMBOLS,"months":MONTHS,"objects":objects}})
except Exception as e:
    receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e)})

pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=sha(pre)
p=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_30M_PREOUTCOME_SOURCE_RECEIPT_V0.1.json")
with open(p,"w",encoding="utf-8") as f: json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps({"status":receipt.get("status"),"canonical_identity":receipt.get("canonical_identity"),
"coverage":{k:v for k,v in receipt.get("coverage",{}).items() if k!="objects"},
"receipt_sha256_pre_self_field":receipt["receipt_sha256_pre_self_field"]},sort_keys=True,indent=2))
print("receipt="+p)
