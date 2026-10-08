#!/usr/bin/env python3
import argparse, gzip, hashlib, json, pathlib, tarfile

PART_SIZE=1500*1024*1024

def hfile(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def add_tree(tf,root,prefix):
    root=pathlib.Path(root)
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rel=pathlib.Path(prefix)/p.relative_to(root)
        ti=tarfile.TarInfo(rel.as_posix());ti.size=p.stat().st_size;ti.mtime=0;ti.uid=0;ti.gid=0;ti.uname="";ti.gname="";ti.mode=0o644
        with p.open("rb") as f: tf.addfile(ti,f)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db-dir",required=True);ap.add_argument("--home-dir",required=True)
    ap.add_argument("--checkpoint-manifest",required=True);ap.add_argument("--out-prefix",required=True)
    a=ap.parse_args()
    prefix=pathlib.Path(a.out_prefix)
    archive=prefix.with_suffix(".tar.gz")
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0,compresslevel=6) as gz:
            with tarfile.open(fileobj=gz,mode="w|",format=tarfile.PAX_FORMAT) as tf:
                add_tree(tf,a.db_dir,"db")
                add_tree(tf,a.home_dir,"home")
                mp=pathlib.Path(a.checkpoint_manifest);data=mp.read_bytes()
                ti=tarfile.TarInfo("checkpoint_manifest.json");ti.size=len(data);ti.mtime=0;ti.uid=0;ti.gid=0;ti.uname="";ti.gname="";ti.mode=0o644
                import io;tf.addfile(ti,io.BytesIO(data))
    archive_sha=hfile(archive);parts=[]
    with archive.open("rb") as src:
        i=0
        while True:
            chunk=src.read(PART_SIZE)
            if not chunk: break
            part=pathlib.Path(f"{a.out_prefix}.part{i:04d}")
            part.write_bytes(chunk)
            parts.append({"file":part.name,"bytes":len(chunk),"sha256":hashlib.sha256(chunk).hexdigest()})
            i+=1
    receipt={
      "schema":"coreum-v08-checkpoint-package-v1","archive_file":archive.name,
      "archive_bytes":archive.stat().st_size,"archive_sha256":archive_sha,
      "part_size_limit":PART_SIZE,"parts":parts,"part_count":len(parts),
      "checkpoint_manifest_sha256":hfile(pathlib.Path(a.checkpoint_manifest)),
      "deterministic_metadata":True
    }
    rp=pathlib.Path(f"{a.out_prefix}.receipt.json")
    rp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
if __name__=="__main__": main()
