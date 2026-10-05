"""Package all raw receipts into hashed binary parts for repository transport."""
import hashlib,json,pathlib,tarfile
from analyze import ROOT
def main():
    dest=ROOT/'evidence'; dest.mkdir(exist_ok=True)
    archive=dest/'raw_evidence.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for sub in ['raw','forward']:
            for p in sorted((ROOT/sub).glob('*')):
                if p.is_file(): tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
    payload=archive.read_bytes(); parts=[]
    for i,start in enumerate(range(0,len(payload),120000)):
        p=dest/f'raw_evidence.part{i:03d}'; p.write_bytes(payload[start:start+120000]); parts.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest={'archive':'raw_evidence.tar.gz','bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'parts':parts}
    (dest/'package_manifest.json').write_text(json.dumps(manifest,indent=2)); print('parts',len(parts),'compressed_bytes',len(payload))
if __name__=='__main__': main()
