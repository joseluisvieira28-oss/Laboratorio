#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

EXPECTED_PACKAGE_SHA256="3da0f466b1db170f8aedc7d45f7b757bb4e843cc7695bffc9953908c21449ba6"
EXPECTED_RUNNER_SHA256="80347c42e1893fbe0284ccc5779fdd841362a3feb24644d39777144f15be2a55"
EXPECTED_HOURS=8760
KNOWN_PRESENT=4889
KNOWN_MISSING=360
KNOWN_ERROR=3511

ALLOWED={"PRESENT","MISSING","ERROR"}

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def load_rows(path: Path):
    if path.suffix.lower()==".json":
        obj=json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj,dict):
            for key in ("rows","inventory","hours"):
                if isinstance(obj.get(key),list):
                    return obj[key]
        if isinstance(obj,list):
            return obj
        raise ValueError("JSON inventory must be a list or contain rows/inventory/hours list")
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def normalize_status(row):
    for k in ("status","source_status","state","classification"):
        if k in row and row[k] is not None:
            s=str(row[k]).strip().upper()
            if s in ALLOWED:
                return s
    raise ValueError(f"row missing recognized status: {row}")

def audit_inventory(path: Path):
    rows=load_rows(path)
    counts={k:0 for k in ALLOWED}
    for row in rows:
        counts[normalize_status(row)]+=1
    total=sum(counts.values())
    return rows,counts,total

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--package",type=Path,required=True)
    ap.add_argument("--inventory",type=Path)
    ap.add_argument("--runner",type=Path)
    ap.add_argument("--allow-progress",action="store_true",
                    help="Allow counts to differ from incident snapshot while enforcing monotonic resolved progress.")
    args=ap.parse_args()

    out={
      "schema_version":"0.1",
      "lab_id":"L2-RESILIENCY-001",
      "scope":"OFFLINE_RESUME_PREFLIGHT_ONLY",
      "package":{},
      "runner":None,
      "inventory":None,
      "guards":{
        "network_requests":0,
        "aws_requests":0,
        "market_data_parsed":False,
        "outcomes_accessed":False,
        "2026_accessed":False,
        "scientific_rules_changed":False
      }
    }

    pkg_sha=sha256_file(args.package)
    out["package"]={"path":str(args.package),"sha256":pkg_sha,"expected_sha256":EXPECTED_PACKAGE_SHA256,"pass":pkg_sha==EXPECTED_PACKAGE_SHA256}
    if pkg_sha!=EXPECTED_PACKAGE_SHA256:
        out["classification"]="PACKAGE_HASH_MISMATCH_FAIL_CLOSED"
        print(json.dumps(out,indent=2,sort_keys=True))
        raise SystemExit(2)

    if args.runner:
        rsha=sha256_file(args.runner)
        out["runner"]={"path":str(args.runner),"sha256":rsha,"expected_sha256":EXPECTED_RUNNER_SHA256,"pass":rsha==EXPECTED_RUNNER_SHA256}
        if rsha!=EXPECTED_RUNNER_SHA256:
            out["classification"]="RUNNER_HASH_MISMATCH_FAIL_CLOSED"
            print(json.dumps(out,indent=2,sort_keys=True))
            raise SystemExit(3)

    if args.inventory:
        _rows,counts,total=audit_inventory(args.inventory)
        inv={"path":str(args.inventory),"counts":counts,"total":total,"expected_hours":EXPECTED_HOURS}
        if total!=EXPECTED_HOURS:
            inv["pass"]=False
            inv["reason"]="TOTAL_HOURS_MISMATCH"
            out["inventory"]=inv
            out["classification"]="INVENTORY_SHAPE_FAIL_CLOSED"
            print(json.dumps(out,indent=2,sort_keys=True))
            raise SystemExit(4)

        if not args.allow_progress:
            expected={"PRESENT":KNOWN_PRESENT,"MISSING":KNOWN_MISSING,"ERROR":KNOWN_ERROR}
            inv["incident_snapshot_expected"]=expected
            inv["pass"]=counts==expected
            if not inv["pass"]:
                out["inventory"]=inv
                out["classification"]="INVENTORY_SNAPSHOT_MISMATCH_FAIL_CLOSED"
                print(json.dumps(out,indent=2,sort_keys=True))
                raise SystemExit(5)
        else:
            # Resume may only reduce ERROR by converting it to PRESENT or MISSING.
            resolved=counts["PRESENT"]+counts["MISSING"]
            baseline_resolved=KNOWN_PRESENT+KNOWN_MISSING
            inv["pass"]=(
                counts["ERROR"] <= KNOWN_ERROR and
                resolved >= baseline_resolved and
                counts["PRESENT"] >= KNOWN_PRESENT and
                counts["MISSING"] >= KNOWN_MISSING
            )
            if not inv["pass"]:
                out["inventory"]=inv
                out["classification"]="NON_MONOTONIC_RESUME_STATE_FAIL_CLOSED"
                print(json.dumps(out,indent=2,sort_keys=True))
                raise SystemExit(6)
        out["inventory"]=inv

    out["classification"]="OFFLINE_RESUME_PREFLIGHT_PASS"
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
