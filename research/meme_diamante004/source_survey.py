#!/usr/bin/env python3
"""Read-only Hugging Face dataset index probe. No user data, no payments, no orders."""
import urllib.request,json
DATASETS=["launchtape/solana-launch-tape","Slinky21/Pumpfun_Memecoin_Corpus"]
for id_ in DATASETS:
    safe=id_.replace("/","%2F")
    url="https://huggingface.co/api/datasets/"+id_
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-004-ReadOnly/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r: metadata=json.load(r)
    data=[dict(type="file",path=s.get("rfilename",""),size=s.get("size"),lfs=s.get("lfs")) for s in metadata.get("siblings",[])]
    candidates=[]
    for item in data:
        if item.get("type")!="file":continue
        path=item.get("path","")
        if any(x in path.lower() for x in ["trades","curvetape","readme","known_issues","tokens.parquet","snapshots","sample","metadata","launchmeta"]):
            candidates.append({"path":path,"size_bytes":item.get("size"),"lfs":item.get("lfs")})
    print("SOURCE_INDEX="+json.dumps({"dataset":id_,"indexed":len(data),"candidates":candidates[:60]}))
