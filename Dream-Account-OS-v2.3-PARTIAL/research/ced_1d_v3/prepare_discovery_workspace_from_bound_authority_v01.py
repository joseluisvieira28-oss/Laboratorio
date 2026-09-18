#!/usr/bin/env python3
"""CED-1D-V1 V3 Discovery workspace preparation from directly bound canonical authority.

SOURCE/DATA ONLY. No prices are summarized, no returns/PnL/statistical outcomes are
computed. Downloads only 2021-2024 Binance USD-M monthly 1m archives selected by the
canonical RESEARCH_INPUT_INDEX, and injects only the six canonical repaired composites.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, shutil, time, urllib.request, zipfile
from pathlib import Path, PureWindowsPath

BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
YEARS = {2021, 2022, 2023, 2024}
REPAIR_SHA = {
 ("LTCUSDT","2022-02"):"5da90861fe6a61016f6e35cb0f85d82abe436694916fd164ceb31ca928118bc8",
 ("LTCUSDT","2022-04"):"b9705e7846c2f46ebd2363e53b54dfe80e046a93c716e53a4e1cb1469eeb5368",
 ("SOLUSDT","2022-02"):"462dd3c24772cef6f50a37a48a00e4c346cc70892ac255d9b5b8d1c16820ab13",
 ("SOLUSDT","2022-04"):"e75555985892fda1a5965d6aa53be3e6680b9fa3f54460621147a72d7b9c671f",
 ("XRPUSDT","2022-02"):"87f53beb65ba4727133866dc6d0995f0f79edf8a279f949468dd70f865eb4622",
 ("XRPUSDT","2022-04"):"5da946dafcc979ccd6913fab51e864482957a7e821a50e956c3923f1e7313ef6",
}
UA="CED-1D-V1-V3-DISCOVERY-REPRO/1.0 source-only"

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20), b""): h.update(b)
    return h.hexdigest()

def fetch(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    last=None
    for i in range(4):
        try:
            req=urllib.request.Request(url, headers={"User-Agent":UA})
            with urllib.request.urlopen(req, timeout=180) as r, dest.open("wb") as w:
                shutil.copyfileobj(r,w,1<<20)
            return
        except Exception as e:
            last=e
            if dest.exists(): dest.unlink()
            time.sleep(1.5*(i+1))
    raise last

def check_zip(p: Path):
    with zipfile.ZipFile(p) as zf:
        bad=zf.testzip()
        if bad is not None: raise RuntimeError(f"ZIP_CRC_FAIL:{p}:{bad}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--registry",required=True)
    ap.add_argument("--index",required=True)
    ap.add_argument("--authority",required=True)
    ap.add_argument("--repairs",required=True)
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--workers",type=int,default=16)
    a=ap.parse_args()
    reg=json.loads(Path(a.registry).read_text(encoding="utf-8-sig"))
    idx=json.loads(Path(a.index).read_text(encoding="utf-8-sig"))
    if len(reg)!=600 or len(idx)!=600: raise RuntimeError(f"CANONICAL_600_REQUIRED:{len(reg)}:{len(idx)}")
    rmap={(str(x["symbol"]),str(x["month"])):x for x in reg}
    selected=[]
    for row in idx:
        y=int(str(row["month"])[:4])
        if y in YEARS: selected.append(row)
        elif y!=2025: raise RuntimeError(f"PROTECTED_OR_UNEXPECTED_YEAR_IN_INDEX:{y}")
    if len(selected)!=480: raise RuntimeError(f"DISCOVERY_INDEX_NOT_480:{len(selected)}")
    if any(x.get("classification")!="PASS" for x in idx): raise RuntimeError("INDEX_CONTAINS_NON_PASS")
    official=[x for x in selected if x.get("source_type")=="OFFICIAL_MONTHLY"]
    repaired=[x for x in selected if x.get("source_type")!="OFFICIAL_MONTHLY"]
    if len(official)!=474 or len(repaired)!=6:
        raise RuntimeError(f"EXPECTED_474_PLUS_6:{len(official)}:{len(repaired)}")
    wk=Path(a.workspace); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    repairs_root=Path(a.repairs)
    records=[]

    def official_one(row):
        symbol=str(row["symbol"]); month=str(row["month"]); key=(symbol,month)
        rr=rmap[key]
        if rr.get("status")!="PASS" or rr.get("classification")!="PASS" or rr.get("provider_checksum_match") is not True:
            raise RuntimeError(f"REGISTRY_NOT_PASS:{key}")
        expected=str(rr["local_sha256"]).lower()
        if expected != str(rr["provider_sha256"]).lower() or expected != str(rr.get("zip_sha256",expected)).lower():
            raise RuntimeError(f"REGISTRY_SHA_DISAGREEMENT:{key}")
        name=f"{symbol}-1m-{month}.zip"
        expected_rel=f"RAW\\{symbol}\\{name}"
        if str(row["relative_source_path"])!=expected_rel: raise RuntimeError(f"INDEX_ROUTE_DRIFT:{key}")
        dest=wk / Path(str(row["relative_source_path"]))
        url=f"{BASE}/{symbol}/1m/{name}"
        fetch(url,dest)
        got=sha256_file(dest)
        if got!=expected: raise RuntimeError(f"BYTE_HASH_MISMATCH:{key}:{got}:{expected}")
        check_zip(dest)
        return {"symbol":symbol,"month":month,"source_type":"OFFICIAL_MONTHLY","sha256":got,"status":"PASS"}

    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs=[ex.submit(official_one,r) for r in official]
        for f in concurrent.futures.as_completed(futs):
            records.append(f.result())

    for row in repaired:
        symbol=str(row["symbol"]); month=str(row["month"]); key=(symbol,month)
        if key not in REPAIR_SHA: raise RuntimeError(f"UNEXPECTED_REPAIR:{key}")
        rel=str(row["relative_source_path"])
        name=PureWindowsPath(rel).name
        src=repairs_root/name
        if not src.is_file(): raise RuntimeError(f"MISSING_CANONICAL_REPAIR:{src}")
        got=sha256_file(src)
        if got!=REPAIR_SHA[key]: raise RuntimeError(f"REPAIR_SHA_MISMATCH:{key}:{got}")
        check_zip(src)
        dest=wk / Path(rel); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)
        records.append({"symbol":symbol,"month":month,"source_type":"CANONICAL_REPAIRED_MONTHLY","sha256":got,"status":"PASS"})

    # Place exact index and authority in the historical workspace layout.
    ix_dest=wk/"REPAIR_A01"/"EVIDENCE"/"RESEARCH_INPUT_INDEX.json"
    ix_dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(a.index,ix_dest)
    auth_dest=wk/"AUTHORITY"; auth_dest.mkdir(parents=True,exist_ok=True)
    for name in ["CED-PH2-FROZEN-UNIVERSE.json","phase2_dataset_evidence.json","contract_authority.json","contract.json"]:
        shutil.copy2(Path(a.authority)/name,auth_dest/name)

    if len(records)!=480 or any(r["status"]!="PASS" for r in records): raise RuntimeError("WORKSPACE_RECORD_GATE_FAIL")
    receipt={
      "status":"DISCOVERY_WORKSPACE_474_PLUS_6_PASS",
      "provider_route":"BINANCE_USD_M_FUTURES_MONTHLY_KLINES",
      "discovery_records":480,
      "official_monthly_records":474,
      "canonical_repair_records":6,
      "year_2025_accessed":False,
      "year_2026_accessed":False,
      "outcomes_computed":False,
      "live_trading_authorized":False,
      "exchange_mutation_authorized":False,
      "records":sorted(records,key=lambda x:(x["symbol"],x["month"]))
    }
    (out/"workspace_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(receipt["status"])

if __name__=="__main__":
    main()
