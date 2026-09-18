#!/usr/bin/env python3
import base64, hashlib, json, zipfile
from pathlib import Path
SRC=Path("Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/evidence/ced_recovered_authority_bundle_v01.zip.b64")
OUT=Path("artifacts/ced1d_authority_bundle_inspect_v01"); OUT.mkdir(parents=True,exist_ok=True)
b64="".join(SRC.read_text().split())
receipt={"source_b64_chars":len(b64),"market_data_accessed":False,"outcomes_computed":False,"access_2025":False,"access_2026":False}
try:
 raw=base64.b64decode(b64,validate=True)
 receipt["decoded_zip_bytes"]=len(raw)
 receipt["zip_sha256"]=hashlib.sha256(raw).hexdigest()
 zp=OUT/"authority_bundle.zip"; zp.write_bytes(raw)
 with zipfile.ZipFile(zp) as z:
  receipt["zip_crc_pass"]=z.testzip() is None
  members=[]
  for n in z.namelist():
   info=z.getinfo(n)
   row={"name":n,"size":info.file_size,"compressed_size":info.compress_size,"is_dir":info.is_dir()}
   if not info.is_dir():
    data=z.read(n); row["sha256"]=hashlib.sha256(data).hexdigest()
   members.append(row)
  receipt["members"]=members
 receipt["classification"]="AUTHORITY_BUNDLE_INSPECTION_PASS"
except Exception as e:
 receipt["classification"]="AUTHORITY_BUNDLE_INSPECTION_FAIL"; receipt["error"]=repr(e)
(OUT/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
raise SystemExit(0 if receipt["classification"].endswith("PASS") else 2)
