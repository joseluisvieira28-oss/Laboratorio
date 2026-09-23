#!/usr/bin/env python3
import datetime as dt, json
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

REPO="solarchive/solarchive"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SOLARCHIVE_HF_MIRROR_RECEIPT_V0.2.json")
KAMINO_START=dt.date(2023,11,17)
SAVE11_START=dt.date(2024,7,19)
END=dt.date(2025,1,1)

def dr(a,b):
    d=a
    while d<b:
        yield d
        d+=dt.timedelta(days=1)

receipt={
 "schema_version":"0.2",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "source":"HuggingFace mirror of solarchive/solarchive",
 "repo_id":REPO,
 "classification":"SOLARCHIVE_HF_MIRROR_PROBE_BLOCKED",
 "firewall":{
   "transaction_rows_read":False,"prices":False,"returns":False,"pnl":False,
   "direction":False,"economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
   "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
   "paid_source":False,"account_creation":False,"merge_main":False
 }
}
try:
    api=HfApi()
    nodes=list(api.list_repo_tree(REPO,path_in_repo="txs",recursive=False,repo_type="dataset",expand=False))
    names=[]
    for n in nodes:
        path=getattr(n,"path",None)
        if isinstance(path,str):
            names.append(path)
    dirs=sorted({p.split("/")[-1] for p in names if p.startswith("txs/") and len(p.split("/"))==2 and p.split("/")[-1][:4].isdigit()})
    required_k=[d.isoformat() for d in dr(KAMINO_START,END)]
    required_s=[d.isoformat() for d in dr(SAVE11_START,END)]
    setd=set(dirs)
    receipt["txs_top_level_entry_count"]=len(names)
    receipt["partition_dir_count"]=len(dirs)
    receipt["partition_first"]=dirs[:10]
    receipt["partition_last"]=dirs[-10:]
    receipt["kamino_required_dates"]=len(required_k)
    receipt["kamino_present_dates"]=sum(x in setd for x in required_k)
    receipt["kamino_missing_dates"]=[x for x in required_k if x not in setd]
    receipt["save11_required_dates"]=len(required_s)
    receipt["save11_present_dates"]=sum(x in setd for x in required_s)
    receipt["save11_missing_dates"]=[x for x in required_s if x not in setd]

    schema_path=hf_hub_download(REPO,filename="schemas/transactions.json",repo_type="dataset")
    schema=json.loads(Path(schema_path).read_text(encoding="utf-8"))
    receipt["transaction_schema"]=schema
    blob=json.dumps(schema,sort_keys=True).lower()
    receipt["schema_terms"]={
      "signature":"signature" in blob,
      "slot_or_block":("block_slot" in blob or '"slot"' in blob),
      "accounts":"accounts" in blob,
      "log_messages":"log_messages" in blob,
      "instructions":"instruction" in blob,
      "inner_instructions":("inner_instruction" in blob or "innerinstructions" in blob),
      "raw_message":("message" in blob),
      "raw_instruction_data":("instruction_data" in blob or '"data"' in blob),
      "status_or_err":("status" in blob or '"err"' in blob),
    }

    full_k=all(x in setd for x in required_k)
    full_s=all(x in setd for x in required_s)
    exact_ix=receipt["schema_terms"]["instructions"] and receipt["schema_terms"]["raw_instruction_data"]
    inner=receipt["schema_terms"]["inner_instructions"] or (
       receipt["schema_terms"]["raw_message"] and receipt["schema_terms"]["log_messages"]
    )
    if full_k and full_s and exact_ix and inner:
        receipt["classification"]="SOLARCHIVE_HF_MIRROR_ROUTE_SCHEMA_CANDIDATE_PASS"
    elif full_k or full_s or len(dirs)>0:
        receipt["classification"]="SOLARCHIVE_HF_MIRROR_ROUTE_PARTIAL"
    else:
        receipt["classification"]="SOLARCHIVE_HF_MIRROR_ROUTE_NO_PARTITIONS"
except Exception as e:
    receipt["error"]=type(e).__name__
    receipt["detail"]=str(e)[:2000]

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({
 "classification":receipt.get("classification"),
 "partition_dir_count":receipt.get("partition_dir_count"),
 "partition_first":receipt.get("partition_first"),
 "partition_last":receipt.get("partition_last"),
 "kamino_present_dates":receipt.get("kamino_present_dates"),
 "save11_present_dates":receipt.get("save11_present_dates"),
 "schema_terms":receipt.get("schema_terms"),
 "error":receipt.get("error")
},indent=2,sort_keys=True))
