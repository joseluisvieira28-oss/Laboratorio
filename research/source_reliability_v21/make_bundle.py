"""Package only a completed bounded capture; no network or collection."""
import json,hashlib,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).parent
if __name__=='__main__':
 capture=Path(sys.argv[1]); output=Path(sys.argv[2]); manifest=json.loads((capture/'manifest.json').read_text())
 for name,key in [('PROTOCOL.md','protocol_sha256'),('source.py','code_sha256')]:
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==manifest[key],'FROZEN_FILE_CHANGED'
 assert not output.exists(),'PRESERVE_EXISTING_BUNDLE'
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_STORED) as z:
  for name in ('raw.jsonl.gz','manifest.json','report.json'):z.write(capture/name,name)
  for name in ('PROTOCOL.md','source.py','audit_zip.py','PROVENANCE.json'):z.write(ROOT/name,name)
 digest=hashlib.sha256(output.read_bytes()).hexdigest()
 output.with_suffix(output.suffix+'.sha256').write_text(digest+'  '+output.name+'\n')
 print(json.dumps({'zip':str(output),'zip_bytes':output.stat().st_size,'zip_sha256':digest}))
