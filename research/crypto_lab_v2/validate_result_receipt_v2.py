#!/usr/bin/env python3
"""
Crypto Lab V2 result adjudicator.
Mechanically checks whether the declared status is compatible with the
pre-frozen economic hurdle H and the reported confidence interval.

This script does not calculate the interval; the family-specific analysis
must produce it under the frozen multiplicity/inference policy.
"""
from __future__ import annotations
import json
import pathlib
import sys

ALLOWED = {"SURVIVES","NO_EDGE_AT_H","NO_EFFECT_OF_MAGNITUDE_H","INCONCLUSIVE"}

def implied_status(d):
    H=float(d["hurdle_h"])
    lo=float(d["ci_lower"])
    hi=float(d["ci_upper"])
    if lo > hi:
        raise ValueError("ci_lower > ci_upper")
    direction=d["direction"]

    if direction == "POSITIVE":
        if lo > H:
            return "SURVIVES"
        if hi < H:
            return "NO_EDGE_AT_H"
        return "INCONCLUSIVE"

    if direction == "NEGATIVE":
        if hi < -H:
            return "SURVIVES"
        if lo > -H:
            return "NO_EDGE_AT_H"
        return "INCONCLUSIVE"

    if direction == "TWO_SIDED":
        if lo > H or hi < -H:
            return "SURVIVES"
        if lo > -H and hi < H:
            return "NO_EFFECT_OF_MAGNITUDE_H"
        return "INCONCLUSIVE"

    raise ValueError(f"invalid direction {direction!r}")

def validate(path):
    d=json.loads(path.read_text(encoding="utf-8"))
    if d.get("schema_version")!="2.0":
        raise ValueError("schema_version must be 2.0")
    if d.get("stage")!="POST_DEVELOPMENT":
        raise ValueError("stage must be POST_DEVELOPMENT")
    if not isinstance(d.get("preoutcome_gate_commit"),str) or len(d["preoutcome_gate_commit"])<7:
        raise ValueError("preoutcome_gate_commit missing/invalid")
    H=d.get("hurdle_h")
    if not isinstance(H,(int,float)) or H<=0:
        raise ValueError("hurdle_h must be > 0")
    for k in ("estimate","ci_lower","ci_upper","alpha_effective"):
        if not isinstance(d.get(k),(int,float)):
            raise ValueError(f"{k} must be numeric")
    if not (0 < float(d["alpha_effective"]) <= 0.2):
        raise ValueError("alpha_effective must be in (0,0.2]")
    declared=d.get("declared_status")
    if declared not in ALLOWED:
        raise ValueError(f"invalid declared_status {declared!r}")
    implied=implied_status(d)
    if declared != implied:
        raise ValueError(f"declared_status={declared} but interval implies {implied}")
    return implied

def main():
    paths=[pathlib.Path(x) for x in sys.argv[1:]]
    if not paths:
        paths=list(pathlib.Path("research").glob("**/RESULT_RECEIPT_V2.json"))
    if not paths:
        print("CRYPTO_LAB_V2_RESULT: no RESULT_RECEIPT_V2.json files found; nothing to validate")
        return 0
    failed=0
    for p in paths:
        try:
            s=validate(p)
            print(f"PASS {p}: {s}")
        except Exception as e:
            failed+=1
            print(f"FAIL {p}: {e}",file=sys.stderr)
    return 1 if failed else 0

if __name__=="__main__":
    raise SystemExit(main())
