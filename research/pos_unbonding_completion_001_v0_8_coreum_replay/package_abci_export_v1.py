#!/usr/bin/env python3
import argparse, gzip, hashlib, io, json, pathlib, tarfile

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--export-dir",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    root=pathlib.Path(a.export_dir)
    manifest_path=pathlib.Path(a.manifest)
    m=json.loads(manifest_path.read_text())
    members=[]
    for r in m["records"]:
        p=root/r["file"]; raw=p.read_bytes()
        if len(raw)!=r["bytes"] or sha(raw)!=r["sha256"]:
            raise RuntimeError(f"ABCI member mismatch {r['file']}")
        members.append((r["file"],raw))
    mraw=manifest_path.read_bytes()
    members.append((manifest_path.name,mraw))
    tb=io.BytesIO()
    with tarfile.open(fileobj=tb,mode="w",format=tarfile.PAX_FORMAT) as tf:
        for name,raw in sorted(members):
            ti=tarfile.TarInfo(name);ti.size=len(raw);ti.mtime=0;ti.uid=0;ti.gid=0;ti.uname="";ti.gname="";ti.mode=0o644
            tf.addfile(ti,io.BytesIO(raw))
    gb=io.BytesIO()
    with gzip.GzipFile(filename="",mode="wb",fileobj=gb,mtime=0,compresslevel=9) as gz: gz.write(tb.getvalue())
    pkg=gb.getvalue(); out=pathlib.Path(a.out);out.write_bytes(pkg)
    receipt={
      "schema":"coreum-v08-abci-package-v1",
      "start_height":m["start_height"],"end_height":m["end_height"],
      "record_count":m["record_count"],"package_name":out.name,
      "package_bytes":len(pkg),"package_sha256":sha(pkg),
      "manifest_sha256":sha(mraw),"lossless_member_verification":True,
      "block_results_consumed_from_rpc":False
    }
    rp=out.with_suffix(out.suffix+".receipt.json")
    rp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
if __name__=="__main__": main()
