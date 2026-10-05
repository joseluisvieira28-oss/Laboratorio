"""Verify repository evidence parts, then safely restore raw/forward receipts."""
import hashlib,json,tarfile
from analyze import ROOT
def main():
    dest=ROOT/'evidence'; m=json.loads((dest/'package_manifest.json').read_text()); blocks=[]
    for part in m['parts']:
        data=(dest/part['file']).read_bytes(); assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256']; blocks.append(data)
    data=b''.join(blocks); assert len(data)==m['bytes'] and hashlib.sha256(data).hexdigest()==m['sha256']
    archive=dest/m['archive']; archive.write_bytes(data)
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar.getmembers():
            target=(ROOT/member.name).resolve()
            assert target.is_relative_to(ROOT.resolve()) and member.isfile() and member.name.split('/')[0] in ['raw','forward']
        tar.extractall(ROOT,filter='data')
    print('verified and restored',len(m['parts']),'parts')
if __name__=='__main__': main()
