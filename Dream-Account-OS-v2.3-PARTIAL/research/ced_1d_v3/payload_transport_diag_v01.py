#!/usr/bin/env python3
import base64, hashlib, json
from pathlib import Path

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/execution_payload_v02")
OUT=Path("artifacts/ced1d_payload_transport_diag_v01")
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED="36cf28b7221c8907471f69268c6a3114cd4294ab197d428fe22eed4e6602529a"
FILES=[
"part00.b64","part01.b64","part02.b64","part03.b64","part04.b64","part05.b64",
"part06-07.b64","part08.b64","part09.b64","part10a.b64","part10b.b64","part11a.b64","part11b.b64","part12.b64"
]
parts={n:"".join((ROOT/n).read_text().split()) for n in FILES}
target=parts["part10a.b64"]
prefix="".join(parts[n] for n in FILES[:9])
suffix="".join(parts[n] for n in FILES[10:])
receipt={
 "classification":None,
 "expected_sha256":EXPECTED,
 "total_current_base64_chars":sum(len(parts[n]) for n in FILES),
 "part10a_chars":len(target),
 "tested_single_char_removals":len(target),
 "matches":[],
 "market_data_accessed":False,
 "outcomes_computed":False,
 "access_2025":False,
 "access_2026":False
}
for i,ch in enumerate(target):
    candidate=prefix+target[:i]+target[i+1:]+suffix
    try:
        raw=base64.b64decode(candidate, validate=True)
    except Exception:
        continue
    h=hashlib.sha256(raw).hexdigest()
    if h==EXPECTED:
        receipt["matches"].append({
          "remove_index_zero_based":i,
          "removed_char":ch,
          "repaired_part10a_sha256":hashlib.sha256((target[:i]+target[i+1:]).encode()).hexdigest(),
          "decoded_zip_bytes":len(raw)
        })
        (OUT/"part10a.fixed.b64").write_text(target[:i]+target[i+1:])
        (OUT/"payload.fixed.zip").write_bytes(raw)
if len(receipt["matches"])==1:
    receipt["classification"]="UNIQUE_SINGLE_CHAR_TRANSPORT_REPAIR_PASS"
elif len(receipt["matches"])==0:
    receipt["classification"]="NO_SINGLE_CHAR_TRANSPORT_REPAIR_MATCH"
else:
    receipt["classification"]="AMBIGUOUS_SINGLE_CHAR_TRANSPORT_REPAIR"
(OUT/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
raise SystemExit(0 if len(receipt["matches"])==1 else 2)
