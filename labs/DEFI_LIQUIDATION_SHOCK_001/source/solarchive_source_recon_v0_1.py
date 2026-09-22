#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,urllib.request
from pathlib import Path

SCHEMA_URL="https://data.solarchive.org/schemas/solana/transactions.json"
INDEX_URL="https://data.solarchive.org/txs/2024-12-15/index.json"

def get_json(url:str):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"DLS-SOLARCHIVE-RECON/0.1"})
    with urllib.request.urlopen(req,timeout=45) as r:
        body=r.read()
        status=int(r.status)
    return status,body,json.loads(body)

def field_inventory(schema):
    out=[]
    if isinstance(schema,dict):
        fields=schema.get("fields")
        if isinstance(fields,list):
            for f in fields:
                if isinstance(f,dict):
                    out.append({"name":f.get("name"),"type":f.get("type")})
        props=schema.get("properties")
        if isinstance(props,dict) and not out:
            for name,spec in props.items():
                out.append({"name":name,"type":spec.get("type") if isinstance(spec,dict) else None})
    return out

def main():
    out=Path("dls_solarchive_recon"); out.mkdir(exist_ok=True)
    receipt={
      "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"SOLARCHIVE_SOURCE_RECON_BLOCKED",
      "source_data_pass":False,
      "prices":False,"returns":False,"pnl":False,"direction":False,
      "market_response":False,"liquidation_events_decoded":False,
      "first_success_boundary_adjudicated":False,
      "live_trading":False,"orders":False,"wallets":False,
      "exchange_mutation":False,"merge_main":False,
    }
    try:
        ss,sb,schema=get_json(SCHEMA_URL)
        receipt["schema_http_status"]=ss
        receipt["schema_sha256"]=hashlib.sha256(sb).hexdigest()
        receipt["schema_fields"]=field_inventory(schema)

        si,ib,index=get_json(INDEX_URL)
        receipt["index_http_status"]=si
        receipt["index_sha256"]=hashlib.sha256(ib).hexdigest()
        files=index.get("files") if isinstance(index,dict) else None
        receipt["file_count"]=len(files) if isinstance(files,list) else None
        if isinstance(files,list):
            sizes=[]
            urls=[]
            checksum_fields=set()
            for f in files:
                if not isinstance(f,dict):
                    continue
                for k in ("size","size_bytes","bytes","content_length"):
                    if isinstance(f.get(k),(int,float)):
                        sizes.append(int(f[k])); break
                for k in ("url","path","name","file"):
                    if isinstance(f.get(k),str):
                        urls.append(f[k]); break
                for k in f:
                    if "sha" in k.lower() or "checksum" in k.lower() or "md5" in k.lower():
                        checksum_fields.add(k)
            receipt["aggregate_indexed_bytes"]=sum(sizes) if sizes else None
            receipt["files_with_size_count"]=len(sizes)
            receipt["files_with_locator_count"]=len(urls)
            receipt["checksum_field_names"]=sorted(checksum_fields)
            receipt["sample_file_locator"]=urls[0] if urls else None
        receipt["index_top_level_keys"]=sorted(index.keys()) if isinstance(index,dict) else None

        names={str(x.get("name")) for x in receipt["schema_fields"] if x.get("name") is not None}
        likely_raw_fields=sorted(names & {
          "signature","signatures","accounts","account_keys","message","instructions",
          "inner_instructions","log_messages","status","err","block_slot","block_timestamp"
        })
        receipt["likely_raw_transaction_fields"]=likely_raw_fields
        receipt["classification"]="SOLARCHIVE_SCHEMA_INDEX_RECON_PASS"
    except Exception as e:
        receipt["error"]=f"{type(e).__name__}:{e}"

    raw=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["fingerprint"]=hashlib.sha256(raw).hexdigest()
    p=out/"SOLARCHIVE_SOURCE_RECON_RECEIPT_V0.1.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
