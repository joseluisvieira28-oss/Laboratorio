#!/usr/bin/env python3
"""Independent, offline source-data verifier for STABLECOIN-EXCHANGE-FLOW-001.

No network. No BTC prices. No returns/PnL. Designed and committed before seeing the
full acquisition result. Pass an extracted acquisition artifact directory.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED_START=dt.date(2022,11,11)
EXPECTED_END=dt.date(2024,12,30)
EXPECTED_ROWS=781
EXPECTED_COLS=['date_utc','external_in_count','external_out_count','external_in_raw','external_out_raw','net_flow_raw','external_in_usdt','external_out_usdt','net_flow_usdt','first_block','last_block']
EXPECTED_USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
EXPECTED_RPC='https://rpc.mevblocker.io'
EXPECTED_BASKET={x.lower() for x in [
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']}

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def fail(errors,msg): errors.append(msg)
def as_int(v,name,errors,signed=False):
 try:
  if str(v).strip()=='' or any(c in str(v) for c in '.eE'): raise ValueError
  x=int(v)
  if not signed and x<0: raise ValueError
  return x
 except Exception:
  fail(errors,f'BAD_INTEGER:{name}:{v!r}'); return None
def dec(v,name,errors):
 try:return Decimal(v)
 except (InvalidOperation,ValueError):fail(errors,f'BAD_DECIMAL:{name}:{v!r}');return None

def main():
 ap=argparse.ArgumentParser();ap.add_argument('artifact_dir');args=ap.parse_args();root=Path(args.artifact_dir)
 csvp=root/'daily_binance_public_usdt_flow_20221111_20241230.csv'; manp=root/'extraction_manifest.json'; recp=root/'DATA_ACQUISITION_RECEIPT.json'; errors=[]
 for p in (csvp,manp,recp):
  if not p.is_file():fail(errors,f'MISSING_FILE:{p.name}')
 if errors:
  print(json.dumps({'classification':'DATA_GATE_VERIFY_FAIL','errors':errors},indent=2));return 2
 manifest=json.loads(manp.read_text()); receipt=json.loads(recp.read_text())
 with csvp.open(newline='',encoding='utf-8') as f:
  rd=csv.DictReader(f)
  if rd.fieldnames!=EXPECTED_COLS:fail(errors,f'BAD_COLUMNS:{rd.fieldnames}')
  rows=list(rd)
 if len(rows)!=EXPECTED_ROWS:fail(errors,f'BAD_ROW_COUNT:{len(rows)}')
 dates=[]; agg_in=0;agg_out=0
 for i,r in enumerate(rows,1):
  try:d=dt.date.fromisoformat(r['date_utc'])
  except Exception:fail(errors,f'BAD_DATE:row{i}:{r.get("date_utc")!r}');continue
  dates.append(d)
  inc=as_int(r['external_in_count'],f'row{i}.external_in_count',errors);outc=as_int(r['external_out_count'],f'row{i}.external_out_count',errors)
  inv=as_int(r['external_in_raw'],f'row{i}.external_in_raw',errors);outv=as_int(r['external_out_raw'],f'row{i}.external_out_raw',errors);net=as_int(r['net_flow_raw'],f'row{i}.net_flow_raw',errors,signed=True)
  iu=dec(r['external_in_usdt'],f'row{i}.external_in_usdt',errors);ou=dec(r['external_out_usdt'],f'row{i}.external_out_usdt',errors);nu=dec(r['net_flow_usdt'],f'row{i}.net_flow_usdt',errors)
  if None not in (inv,outv,net) and net!=inv-outv:fail(errors,f'NET_ARITHMETIC_MISMATCH:row{i}')
  if inv is not None and iu is not None and iu!=Decimal(inv)/Decimal(1_000_000):fail(errors,f'IN_UNIT_MISMATCH:row{i}')
  if outv is not None and ou is not None and ou!=Decimal(outv)/Decimal(1_000_000):fail(errors,f'OUT_UNIT_MISMATCH:row{i}')
  if net is not None and nu is not None and nu!=Decimal(net)/Decimal(1_000_000):fail(errors,f'NET_UNIT_MISMATCH:row{i}')
  if inc is not None:agg_in+=inc
  if outc is not None:agg_out+=outc
 expected=[EXPECTED_START+dt.timedelta(days=i) for i in range(EXPECTED_ROWS)]
 if dates!=expected:fail(errors,'CALENDAR_NOT_EXACT_CONTIGUOUS_781_DAY_SEQUENCE')
 if len(set(dates))!=len(dates):fail(errors,'DUPLICATE_DATES')
 if any(d.year>=2025 for d in dates):fail(errors,'PROTECTED_YEAR_IN_CSV')
 # receipt
 if receipt.get('classification')!='DATA_ACQUISITION_PASS':fail(errors,f'BAD_ACQUISITION_CLASSIFICATION:{receipt.get("classification")}')
 for k in ('access_2025','access_2026','btc_market_data_accessed','returns_computed','pnl_computed'):
  if receipt.get(k) is not False:fail(errors,f'RECEIPT_FIREWALL_NOT_FALSE:{k}:{receipt.get(k)!r}')
 if receipt.get('row_count')!=EXPECTED_ROWS or receipt.get('expected_row_count')!=EXPECTED_ROWS:fail(errors,'RECEIPT_ROW_COUNT_MISMATCH')
 if receipt.get('first_date')!='2022-11-11' or receipt.get('last_date')!='2024-12-30':fail(errors,'RECEIPT_DATE_RANGE_MISMATCH')
 if receipt.get('aggregate_external_in_count')!=agg_in:fail(errors,'RECEIPT_IN_COUNT_MISMATCH')
 if receipt.get('aggregate_external_out_count')!=agg_out:fail(errors,'RECEIPT_OUT_COUNT_MISMATCH')
 csha=sha(csvp);msha=sha(manp)
 if receipt.get('csv_sha256')!=csha:fail(errors,'CSV_SHA_MISMATCH')
 if receipt.get('manifest_sha256')!=msha:fail(errors,'MANIFEST_SHA_MISMATCH')
 # manifest
 if manifest.get('source_endpoint')!=EXPECTED_RPC:fail(errors,f'BAD_SOURCE_ENDPOINT:{manifest.get("source_endpoint")}')
 if str(manifest.get('usdt_contract','')).lower()!=EXPECTED_USDT:fail(errors,'BAD_USDT_CONTRACT')
 if {str(x).lower() for x in manifest.get('basket',[])}!=EXPECTED_BASKET:fail(errors,'BAD_FROZEN_BASKET')
 if manifest.get('protected_start')!='2022-11-11' or manifest.get('protected_end')!='2024-12-30':fail(errors,'BAD_MANIFEST_PROTECTED_DATES')
 if manifest.get('base_chunk_blocks')!=3200:fail(errors,'BAD_BASE_CHUNK')
 for k in ('access_2025','access_2026','btc_market_data_accessed','returns_computed','pnl_computed'):
  if manifest.get(k) is not False:fail(errors,f'MANIFEST_FIREWALL_NOT_FALSE:{k}:{manifest.get(k)!r}')
 qm=manifest.get('query_manifest')
 if not isinstance(qm,list) or not qm:fail(errors,'EMPTY_QUERY_MANIFEST')
 else:
  for j,q in enumerate(qm):
   if q.get('direction') not in ('inbound','outbound'):fail(errors,f'BAD_QUERY_DIRECTION:{j}')
   for k in ('from_block','to_block','result_count'):
    if not isinstance(q.get(k),int):fail(errors,f'BAD_QUERY_FIELD:{j}:{k}')
   if not q.get('logical_sha256') and not q.get('wire_sha256'):fail(errors,f'MISSING_QUERY_HASH:{j}')
 result={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'DATA_GATE_VERIFY_PASS' if not errors else 'DATA_GATE_VERIFY_FAIL','errors':errors,'verified_rows':len(rows),'csv_sha256':csha,'manifest_sha256':msha,'aggregate_external_in_count':agg_in,'aggregate_external_out_count':agg_out,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
