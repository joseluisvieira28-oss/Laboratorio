#!/usr/bin/env python3
"""Replay only the six canonical A01 repaired 2022 composites.
Imports the recovered historical repair implementation unchanged, performs no
statistical research, and verifies every daily/provider/composite SHA against
recovered canonical R1 evidence. 2025/2026 are never accessed.
"""
from __future__ import annotations
import argparse, importlib.util, json, hashlib
from pathlib import Path

def sha(p):
 h=hashlib.sha256();
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def loadmod(path):
 spec=importlib.util.spec_from_file_location('hist_repair',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--workspace',required=True); ap.add_argument('--registry',required=True); ap.add_argument('--manifest',required=True); ap.add_argument('--historical-repair',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
 w=Path(a.workspace); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
 reg=json.loads(Path(a.registry).read_text()); mani=json.loads(Path(a.manifest).read_text()); hist=loadmod(Path(a.historical_repair))
 rmap={(x['symbol'],x['month']):x for x in reg}; mmap={(x['symbol'],x['month']):x for x in mani}
 if len(mmap)!=6: raise RuntimeError(f'REPAIR_MANIFEST_NOT_6:{len(mmap)}')
 rows=[]
 for key in sorted(mmap):
  symbol,ym=key
  if ym not in {'2022-02','2022-04'} or symbol not in {'LTCUSDT','SOLUSDT','XRPUSDT'}: raise RuntimeError(f'UNEXPECTED_REPAIR_TARGET:{key}')
  rr=rmap[key]; mm=mmap[key]
  original=w/'RAW'/symbol/f'{symbol}-1m-{ym}.zip'
  expected_orig=str(rr['original_monthly_provider_sha256']).lower()
  if sha(original)!=expected_orig: raise RuntimeError(f'ORIGINAL_MONTHLY_HASH_DRIFT:{key}')
  monthly=hist.read_single_csv_from_zip(original); missing=hist.missing_full_days(monthly,ym)
  if missing!=mm['repair_days']: raise RuntimeError(f'REPAIR_DAY_DRIFT:{key}:{missing}')
  patch=[]; dmeta=[]
  for day in missing:
   meta,drows=hist.acquire_daily(symbol,day,w/'REPAIR_A01'/'DAILY'/symbol); dmeta.append(meta); patch.extend(drows)
  observed_daily=[x['provider_sha256'] for x in dmeta]
  if observed_daily!=mm['daily_provider_sha256s']: raise RuntimeError(f'DAILY_SHA_DRIFT:{key}')
  merged=monthly+patch; merged.sort(key=lambda r:int(r[0])); s,e=hist.month_bounds(ym); hist.validate_rows(merged,s,e,hist.expected_minutes(ym),f'REPLAY:{symbol}:{ym}')
  zp=w/'REPAIR_A01'/'REPAIRED_MONTHLY'/symbol/f'{symbol}-1m-{ym}-REPAIRED-A01.zip'
  comp=hist.deterministic_zip_csv(zp,f'{symbol}-1m-{ym}.csv',merged)
  expected_comp=str(mm['composite_sha256']).lower()
  if comp!=expected_comp or comp!=str(rr['composite_sha256']).lower(): raise RuntimeError(f'COMPOSITE_SHA_DRIFT:{key}:{comp}:{expected_comp}')
  rows.append({'symbol':symbol,'month':ym,'status':'PASS','repair_days':missing,'daily_provider_sha256s':observed_daily,'composite_sha256':comp})
 receipt={'status':'CANONICAL_REPAIR_REPLAY_PASS','records':rows,'record_count':len(rows),'year_2025_accessed':False,'year_2026_accessed':False,'outcomes_computed':False}
 (out/'repair_replay_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)); print(receipt['status'])
if __name__=='__main__': main()
