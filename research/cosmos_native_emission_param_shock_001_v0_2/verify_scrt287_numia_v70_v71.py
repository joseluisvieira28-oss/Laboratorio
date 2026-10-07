"""Verify receipt bytes and extract documentary evidence without executing sources."""
import hashlib, html.parser, json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
class Text(html.parser.HTMLParser):
 def __init__(self):
  super().__init__(); self.skip = 0; self.parts = []
 def handle_starttag(self, tag, attrs):
  if tag in ('script','style'): self.skip += 1
 def handle_endtag(self, tag):
  if tag in ('script','style'): self.skip = max(0,self.skip-1)
 def handle_data(self, data):
  if not self.skip and data.strip(): self.parts.append(data.strip())
def main():
 checks=[]; extracts={}
 for stage in ('forensic_numia_v70','forensic_numia_v71'):
  receipt=json.loads((ROOT/stage/'receipt.json').read_text(encoding='utf-8'))
  assert receipt['canonical_H'] is None and receipt['canonical_T0'] is None
  assert not receipt['credentials_used'] and not receipt['authentication_attempted'] and not receipt['sql_executed']
  for row in receipt['rows']:
   if 'raw' not in row:
    checks.append({'id':row['id'],'transport_failure':True}); continue
   body=(ROOT/stage/row['raw']).read_bytes()
   assert len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
   if '--index' in sys.argv:
    path=(ROOT/stage/row['raw']).relative_to(ROOT.parents[1]).as_posix()
    staged=subprocess.check_output(['git','show',':'+path],cwd=ROOT.parents[1])
    assert hashlib.sha256(staged).hexdigest()==row['sha256'], path
   assert not row['truncated'], row['id']
   checks.append({'id':row['id'],'sha256':row['sha256'],'bytes':len(body),'integrity':'PASS'})
   if row['id'].startswith('wayback_') and row.get('content_type','').startswith('text/html'):
    parser=Text(); parser.feed(body.decode('utf-8','replace'))
    extracts[row['id']]=[s for s in parser.parts if re.search(r'2023|2024|genesis|history|historical|backfill|secret_blocks|header|numia-data|immaculate|dataset',s,re.I)]
 result={'integrity':'PASS','verified_raw_files':sum('sha256' in c for c in checks),'checks':checks,'archive_documentary_extracts':extracts,
  'canonical_H':None,'canonical_T0':None,'gate':'SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED'}
 (ROOT/'SCRT287_NUMIA_INTEGRITY_V70_V71.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'verified_raw_files':result['verified_raw_files'],'extracts':extracts},ensure_ascii=True))
if __name__=='__main__': main()
