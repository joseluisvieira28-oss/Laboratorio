#!/usr/bin/env python3
"""PSRV Kalshi fee-schedule byte snapshot and provenance check."""

from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
import subprocess
import urllib.request
from pathlib import Path

OUT=Path("artifacts/prediction_settlement_rv/kalshi_fee")
PDF_URL="https://kalshi.com/docs/kalshi-fee-schedule.pdf"
UA="CryptoLab-PSRV-FeeSnapshot/0.1"

OUT.mkdir(parents=True,exist_ok=True)
pdf_path=OUT/"kalshi_fee_schedule.pdf"
txt_path=OUT/"kalshi_fee_schedule.txt"

req=urllib.request.Request(PDF_URL,headers={"User-Agent":UA,"Accept":"application/pdf"})
started=dt.datetime.now(dt.timezone.utc)
with urllib.request.urlopen(req,timeout=30) as r:
    raw=r.read()
    status=int(r.status)
    final_url=r.geturl()
    ctype=r.headers.get("content-type","")
finished=dt.datetime.now(dt.timezone.utc)
pdf_path.write_bytes(raw)

receipt={
  "schema":"PSRV_KALSHI_FEE_SNAPSHOT_V0.1",
  "retrieved_at_utc":started.isoformat(),
  "finished_at_utc":finished.isoformat(),
  "requested_url":PDF_URL,
  "final_url":final_url,
  "http_status":status,
  "content_type":ctype,
  "bytes":len(raw),
  "pdf_sha256":hashlib.sha256(raw).hexdigest(),
  "kxbtcd_occurrences":None,
  "general_taker_coefficient_0_07_present":None,
  "general_maker_coefficient_0_0175_present":None,
  "last_updated_effective_lines":[],
  "source_provenance_pass":False,
}

try:
    cp=subprocess.run(["pdftotext",str(pdf_path),str(txt_path)],capture_output=True,text=True,timeout=30)
    receipt["pdftotext_returncode"]=cp.returncode
    if cp.returncode==0 and txt_path.exists():
        text=txt_path.read_text(encoding="utf-8",errors="replace")
        low=text.lower()
        receipt["kxbtcd_occurrences"]=low.count("kxbtcd")
        receipt["general_taker_coefficient_0_07_present"]=bool(re.search(r"0\.07",text))
        receipt["general_maker_coefficient_0_0175_present"]=bool(re.search(r"0\.0175",text))
        lines=[ln.strip() for ln in text.splitlines() if "last updated" in ln.lower() or "effective:" in ln.lower()]
        receipt["last_updated_effective_lines"]=lines[:10]
        receipt["extracted_text_sha256"]=hashlib.sha256(text.encode()).hexdigest()
        receipt["source_provenance_pass"]=bool(
            status==200
            and len(raw)>1000
            and receipt["general_taker_coefficient_0_07_present"]
            and receipt["general_maker_coefficient_0_0175_present"]
        )
except Exception as exc:
    receipt["pdftotext_error"]=type(exc).__name__+": "+str(exc)

receipt["economic_outputs_computed"]=False
receipt["orders"]=False
receipt["source_data_pass"]=False
(OUT/"kalshi_fee_snapshot_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps({k:receipt[k] for k in [
 "http_status","pdf_sha256","kxbtcd_occurrences",
 "general_taker_coefficient_0_07_present","general_maker_coefficient_0_0175_present",
 "last_updated_effective_lines","source_provenance_pass","source_data_pass"
]},indent=2,sort_keys=True))
