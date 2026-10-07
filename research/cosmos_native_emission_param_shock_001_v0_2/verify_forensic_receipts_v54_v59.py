"""Verify acquired-byte receipts and fail-closed status, not source authenticity."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def main():
 rows=[]
 for version in range(54,60):
  folder=ROOT/f'forensic_v{version}'
  receipt=json.loads((folder/'receipt.json').read_text(encoding='utf-8'))
  assert receipt['scope']=='SOURCE_ONLY_NO_MARKET_DATA'
  assert receipt.get('H',receipt.get('canonical_H')) is None
  assert receipt.get('T0',receipt.get('canonical_T0')) is None
  for row in receipt['rows']:
   assert row['method']=='GET'
   if row.get('raw'):
    p=folder/row['raw'];body=p.read_bytes()
    assert hashlib.sha256(body).hexdigest()==row['sha256'],str(p)
    assert len(body)==row['bytes']
   rows.append({'id':row['id'],'status':row.get('status'),'sha256':row.get('sha256'),'truncated':row.get('truncated',False)})
 result={'validation':'PASS','meaning':'Receipt-byte integrity and closed gate only; not canonical chain verification or exhaustion',
  'request_count':len(rows),'canonical_H':None,'canonical_T0':None,'certified_family_count':'11/12',
  'source_gate':'SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED','forensic_phase':'OPEN_NOT_EXHAUSTED','rows':rows}
 (ROOT/'SCRT287_FORENSIC_INTEGRITY_V54_V59.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':main()
