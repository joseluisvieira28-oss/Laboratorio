"""All input data are invented; no network, real plans or market archives."""
import csv, gzip, io, json, math, tempfile, unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import l2r_crossvenue_discovery_v03 as d

BASE=1704067200000

def row(group='WEAK',identity='01:000000001'):
 x={'event_id':identity,'date':'2024-01-01','direction':'1'}
 for c,rh,yh in d.CELLS:
  x[c+'_group']=group
  for side,index,h in [('r',rh,rh),('y',yh,yh)]:
   x.update({f'{c}_{side}_date':'2024-01-01',f'{c}_{side}_row':str(index),f'{c}_{side}_ts_ms':str(BASE+h)})
 return x

def missing(x,cell,side):
 for suffix in ('date','row','ts_ms'): x[f'{cell}_{side}_{suffix}']=''

def synthetic_source(root):
 items=[]
 for day in d.dates():
  z=root/d.archive_name(day); z.write_bytes(b'invented')
  idx=root/(day+'.idx'); idx.write_bytes(d.REC.pack(BASE,0))
  items.append({'zip':z.name,'date':day,'sha256':d.sha(z),'index_sha256':d.sha(idx)})
 source=root/'source.json'; source.write_text(json.dumps({'classification':'BINANCE_2024_TIMESTAMP_ID_SOURCE_PASS','items':items}))
 return source

class RemediationTests(unittest.TestCase):
 def test_persistent_labels_missing_r_y_or_both_skip_consistently(self):
  for group in ('WEAK','STRONG'):
   for sides in [('r',),('y',),('r','y')]:
    with self.subTest(group=group,sides=sides):
     x=row(group)
     for c,_,_ in d.CELLS:
      for side in sides: missing(x,c,side)
     counts=Counter(); self.assertEqual(d.plan_requirements([x],counts),{}); self.assertEqual(counts,{})
     daily={}; self.assertEqual(d.accumulate_rows([x],{},daily),1)
     self.assertTrue(all(v['weak_n']==v['strong_n']==0 for v in daily[x['date']].values()))
 def test_one_missing_cell_does_not_drop_complete_cells(self):
  x=row(); missing(x,'R1_Y5','y'); counts=Counter()
  wanted=d.plan_requirements([x],counts)
  self.assertEqual(sum(counts.values()),5)
  prices={(day,i):100+i/10000 for day,indices in wanted.items() for i in indices}; daily={}
  d.accumulate_rows([x],prices,daily)
  self.assertEqual(sum(v['weak_n'] for v in daily[x['date']].values()),5)
 def test_six_cells_count_once_and_response_signs_are_preserved(self):
  a=row(); b=row('STRONG','01:000000002'); b['direction']='-1'
  counts=Counter(); wanted=d.plan_requirements([a,b],counts)
  self.assertEqual(sum(counts.values()),12)
  prices={(day,i):100+i/10000 for day,indices in wanted.items() for i in indices}; daily={}
  self.assertEqual(d.accumulate_rows([a,b],prices,daily),2)
  for c,_,_ in d.CELLS:
   v=daily[a['date']][c]; self.assertEqual(v['weak_n'],1); self.assertEqual(v['strong_n'],1)
   self.assertGreater(v['weak_sum'],0); self.assertAlmostEqual(v['weak_sum'],-v['strong_sum'])
 def test_partial_tuple_is_corruption(self):
  x=row(); x['R1_Y5_y_row']=''
  with self.assertRaisesRegex(d.Blocked,'partial'): d.plan_requirements([x],Counter())
 def test_invalid_group_row_direction_or_year_fail(self):
  for key,value in [('R1_Y5_group','OTHER'),('R1_Y5_r_row','-1'),('direction','0'),('R1_Y5_r_date','2025-01-01'),('R1_Y5_r_row','bad')]:
   with self.subTest(key=key):
    x=row(); x[key]=value
    with self.assertRaises(d.Blocked): d.plan_requirements([x],Counter())
 def test_non_forward_or_date_mismatch_fail(self):
  for timestamp in (BASE+1000,BASE+86400000):
   x=row(); x['R1_Y5_y_ts_ms']=str(timestamp)
   with self.assertRaises(d.Blocked): d.plan_requirements([x],Counter())
 def test_duplicate_event_or_wrong_segment_day_fail(self):
  with self.assertRaisesRegex(d.Blocked,'duplicate'): d.plan_requirements([row(),row()],Counter())
  with self.assertRaisesRegex(d.Blocked,'date'): d.plan_requirements([row()],Counter(),'2024-01-02')
 def test_duplicate_or_unsafe_segment_names_fail(self):
  for names in [('2024-01-01.csv.gz',)*2,('../2024-01-01.csv.gz',),('2025-01-01.csv.gz',),('2024-02-30.csv.gz',)]:
   with self.assertRaises(d.Blocked): d.validate_plan_segments([{'name':n} for n in names])
 def test_missing_price_key_and_invalid_prices_fail(self):
  with self.assertRaisesRegex(d.Blocked,'key'): d.accumulate_rows([row()],{}, {})
  wanted=d.plan_requirements([row()],Counter())
  for value in (0,-1,float('nan'),float('inf')):
   prices={(day,i):value for day,indices in wanted.items() for i in indices}
   with self.assertRaisesRegex(d.Blocked,'price'): d.accumulate_rows([row()],prices,{})
 def test_empty_coverage_is_zero(self):
  self.assertEqual(d.coverage_ratio(0,0),0); self.assertEqual(d.coverage_ratio(1,2),.5)
 def test_receipt_publish_never_overwrites_and_has_no_partial_on_error(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'receipt.json'; d.write_receipt_once(p,{'detail':'original','prices_may_have_been_opened':True}); before=p.read_bytes()
   d.record_failure(p,ValueError('outer'),'outcome',True); self.assertEqual(p.read_bytes(),before)
   with self.assertRaises(FileExistsError): d.write_receipt_once(p,{'other':1})
   bad=Path(td)/'bad.json'
   with self.assertRaises(ValueError): d.write_receipt_once(bad,{'nan':float('nan')})
   self.assertFalse(bad.exists()); self.assertEqual(list(Path(td).glob('*.partial')),[])
 def test_wrapper_is_conservative_before_or_after_unknown_price_exposure(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'failure.json'; d.record_failure(p,RuntimeError('incident'),'outcome',True)
   self.assertTrue(json.loads(p.read_text())['prices_may_have_been_opened'])
 def test_production_entries_block_before_any_files_or_prices(self):
  with patch.object(Path,'read_text',side_effect=AssertionError('file read')),patch.object(d,'fetch',side_effect=AssertionError('network')):
   for function,nargs in ((d.issue_authority,11),(d.outcome,13)):
    with self.assertRaisesRegex(d.Blocked,d.REMEDIATION_STATE): function(*(['unused']*nargs))
 def test_truncated_index_blocks_and_exact_lookup_preserved(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'2024-01-01.idx'; p.write_bytes(d.REC.pack(BASE+101,0)+b'x')
   try:
    with self.assertRaisesRegex(d.Blocked,'truncated'): d.idx_lookup(td,BASE*1000000)
   finally: d.clear_indexes()
   p.write_bytes(d.REC.pack(BASE+101,0)+d.REC.pack(BASE+101,1))
   try: self.assertEqual(d.idx_lookup(td,BASE*1000000+100100001),('2024-01-01',0,BASE+101,899999))
   finally: d.clear_indexes()
 def test_source_plan_empty_coverage_writes_blocked_receipt(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); source=synthetic_source(root)
   ledger=root/'ledger.csv.gz'
   with gzip.open(ledger,'wt',newline='') as f: f.write('event_id,anchor_date_utc,pre_depth5\n')
   receipt=root/'plan.json'
   with patch.object(d,'materialized_files',return_value=({},[ledger])),patch.object(d,'sha',wraps=d.sha) as hashfn:
    # The unused parent receipt is invented as well.
    parent=root/'parent.json'; parent.write_text('{}')
    with patch('sys.stdout',new=io.StringIO()): d.source_plan(root,source,parent,root/'plan',receipt)
   result=json.loads(receipt.read_text()); self.assertEqual(result['classification'],'BINANCE_PRICE_BLIND_PLAN_BLOCKED')
   self.assertTrue(all(not v for v in result['gates'].values()))

 def test_cli_preserves_detailed_failure_and_does_not_claim_blindness(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'DISCOVERY_2024_RECEIPT.json'
   d.write_receipt_once(p,{'detail':'inner','prices_may_have_been_opened':True})
   before=p.read_bytes()
   argv=['runner','outcome']
   for option in ('cache','source-receipt','parent-receipt','plan-receipt','plan-dir','protocol','runner','exporter','implementation-lock','authority','authority-commit','marker'):
    argv.extend(['--'+option,'unused'])
   argv.extend(['--outdir',td])
   with patch('sys.argv',argv),patch.object(d,'outcome',side_effect=d.Blocked('synthetic inner failure')):
    with self.assertRaises(d.Blocked): d.main()
   self.assertEqual(p.read_bytes(),before)
 def test_planner_serialized_missing_label_and_outcome_eligibility_agree(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); source=synthetic_source(root)
   ledger=root/'ledger.csv.gz'; event={'event_id':'01:000000001','anchor_date_utc':'2024-01-01','pre_depth5':'10','direction':'1','timing_60000_status':'AVAILABLE','timing_60000_envelope_ns':str((BASE+60000)*1000000)}
   for h in (1000,5000,15000):
    event.update({f'r_{h}_status':'AVAILABLE',f'r_{h}_envelope_ns':str((BASE+h)*1000000),f'r_{h}_class':'WEAK'})
   with gzip.open(ledger,'wt',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(event)); w.writeheader(); w.writerow(event)
   receipt=root/'plan.json'; parent=root/'parent.json'; parent.write_text('{}')
   def lookup(cache,ns):
    h=ns//1000000-BASE
    return None if h==5000 else ('2024-01-01',h,BASE+h,0)
   with patch.object(d,'materialized_files',return_value=({},[ledger])),patch.object(d,'idx_lookup',side_effect=lookup),patch('sys.stdout',new=io.StringIO()):
    d.source_plan(root,source,parent,root/'plan',receipt)
   with gzip.open(root/'plan'/'2024-01-01.csv.gz','rt',newline='') as f: rows=list(csv.DictReader(f))
   self.assertEqual(rows[0]['R1_Y5_group'],'WEAK'); self.assertEqual(rows[0]['R1_Y5_y_row'],'')
   counts=Counter(); d.plan_requirements(rows,counts)
   result=json.loads(receipt.read_text())
   for c,_,_ in d.CELLS: self.assertEqual(counts[('2024-01-01',c,'weak')],result['coverage'][c].get('group_weak',0))
 def test_scientific_constants_and_inference_are_unchanged(self):
  import l2r_crossvenue_discovery_v01 as frozen
  for name in ('CELLS','H','MIN_LATE_NS','PARENT_SHA','MANIFEST_SHA','ANCHOR_SHA','BASE'):
   self.assertEqual(getattr(d,name),getattr(frozen,name))
  current=Path(d.__file__).read_text(); original=Path(frozen.__file__).read_text()
  start='  eligible={c:{} for c,_,_ in CELLS}'; end="  result={'lab_id':LAB"
  self.assertEqual(current[current.index(start):current.index(end,current.index(start))],original[original.index(start):original.index(end,original.index(start))])

 def test_duplicate_source_calendar_rejected_without_archive_reads(self):
  receipt={'classification':'BINANCE_2024_TIMESTAMP_ID_SOURCE_PASS','items':[{'date':'2024-01-01','zip':d.archive_name('2024-01-01')}]*366}
  with self.assertRaisesRegex(d.Blocked,'calendar'): d.validate_source_inventory(receipt)

if __name__=='__main__': unittest.main()
