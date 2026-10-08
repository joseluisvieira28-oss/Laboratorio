#!/usr/bin/env python3
import argparse
import gzip
import hashlib
import io
import json
import pathlib
import tarfile

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--range-dir", required=True)
    ap.add_argument("--out", required=True)
    a=ap.parse_args()

    root=pathlib.Path(a.range_dir)
    manifest_path=root/"manifest.json"
    manifest=json.loads(manifest_path.read_text())
    expected={x["file"]:(x["bytes"],x["sha256"]) for x in manifest["files"]}

    members=[]
    for name,(want_bytes,want_sha) in sorted(expected.items()):
        p=root/name
        raw=p.read_bytes()
        got_sha=sha256_bytes(raw)
        if len(raw)!=want_bytes or got_sha!=want_sha:
            raise RuntimeError(f"range member mismatch {name}")
        members.append((name,raw,got_sha,len(raw)))
    manifest_raw=manifest_path.read_bytes()
    members.append(("manifest.json",manifest_raw,sha256_bytes(manifest_raw),len(manifest_raw)))

    tar_buf=io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name,raw,sha,n in members:
            ti=tarfile.TarInfo(name=name)
            ti.size=n
            ti.mtime=0
            ti.uid=0
            ti.gid=0
            ti.uname=""
            ti.gname=""
            ti.mode=0o644
            tf.addfile(ti, io.BytesIO(raw))
    tar_raw=tar_buf.getvalue()

    gz_buf=io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gz_buf, mtime=0, compresslevel=9) as gz:
        gz.write(tar_raw)
    package=gz_buf.getvalue()

    out=pathlib.Path(a.out)
    out.write_bytes(package)

    receipt={
        "schema":"coreum-v08-raw-package-v1",
        "chain_id":manifest["chain_id"],
        "start_applied_height":manifest["start_applied_height"],
        "end_applied_height":manifest["end_applied_height"],
        "next_header_height":manifest["next_header_height"],
        "range_manifest_sha256":sha256_bytes(manifest_raw),
        "package_name":out.name,
        "package_bytes":len(package),
        "package_sha256":sha256_bytes(package),
        "uncompressed_tar_sha256":sha256_bytes(tar_raw),
        "members":[{"path":n,"bytes":sz,"sha256":sha} for n,raw,sha,sz in members],
        "lossless_member_verification":True,
        "block_results_requested":False,
        "census_executed":False,
        "market_outcomes_opened":False,
    }
    receipt_path=out.with_suffix(out.suffix+".receipt.json")
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "package":str(out),
        "package_bytes":receipt["package_bytes"],
        "package_sha256":receipt["package_sha256"],
        "members":len(receipt["members"]),
        "receipt":str(receipt_path),
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
