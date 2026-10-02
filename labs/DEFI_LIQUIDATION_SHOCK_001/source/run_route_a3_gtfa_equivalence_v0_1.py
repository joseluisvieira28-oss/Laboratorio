#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,time,urllib.error,urllib.request,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
SRC=BASE/"source"
sys.path.insert(0,str(SRC))
import run_alternative_source_equivalence_v0_1 as a2

LAB="DEFI-LIQUIDATION-SHOCK-001"
REFS={
 "save0c":{"slot":110526981,"sig":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V"},
 "save11":{"slot":278496102,"sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L"},
 "marginfi":{"slot":177590210,"sig":"2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK"},
 "kamino":{"slot":230572965,"sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv"}
}
OUT=Path("route_a3_evidence")

def digest(b):return hashlib.sha256(b).hexdigest()

def load_jsons(root:Path):
    out=[]
    for p in sorted(root.rglob("*.json")):
        try:out.append((p,json.loads(p.read_text())))
        except Exception:pass
    return out

def find_pair(root:Path,proto:str,sig:str):
    hits=[]
    for p,x in load_jsons(root):
        if not isinstance(x,dict):continue
        if x.get("classification")!="FOUR_CLASS_ARCHIVAL_PAIRED_EVIDENCE_PASS":continue
        for r in x.get("results") or []:
            if isinstance(r,dict) and r.get("protocol")==proto and r.get("signature")==sig:
                hits.append((p,r))
    if len(hits)!=1:raise ValueError(f"pair_receipt_count:{proto}:{len(hits)}")
    return hits[0]

def find_raw(root:Path,sig:str):
    hits=[]
    for p,x in load_jsons(root):
        if not isinstance(x,dict):continue
        r=x.get("result")
        if isinstance(r,dict):
            sigs=(r.get("transaction") or {}).get("signatures") or []
            if sigs and sigs[0]==sig:hits.append((p,r))
    if len(hits)!=1:raise ValueError(f"raw_tx_count:{sig}:{len(hits)}")
    return hits[0]

class GTFA:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY")
        url=os.environ.get("DLS_RPC_URL")
        if key:self.url="https://mainnet.helius-rpc.com/?api-key="+key
        elif url:self.url=url
        else:raise ValueError("credential_absent")
        self.calls=0
    def call(self,address,slot):
        token=None;data=[];pages=0
        while True:
            opts={
              "transactionDetails":"full",
              "sortOrder":"asc",
              "limit":100,
              "filters":{"slot":{"gte":slot,"lte":slot},"status":"succeeded"}
            }
            if token:opts["paginationToken"]=token
            payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransactionsForAddress","params":[address,opts]},separators=(",",":")).encode()
            last=None
            for attempt in range(3):
                time.sleep(.26)
                try:
                    req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json"},method="POST")
                    with urllib.request.urlopen(req,timeout=45) as resp:
                        raw=resp.read()
                    obj=json.loads(raw)
                    if obj.get("error"):
                        code=(obj["error"] or {}).get("code")
                        if code in (-32601,-32602,-32000,-32001,-32005):
                            raise ValueError(f"gtfa_rpc_error_code:{code}")
                        raise ValueError("gtfa_rpc_error")
                    result=obj.get("result")
                    if not isinstance(result,dict) or not isinstance(result.get("data"),list):
                        raise ValueError("gtfa_result_schema")
                    self.calls+=1;pages+=1
                    if pages>10:raise ValueError("gtfa_page_ceiling")
                    data.extend(result["data"])
                    nxt=result.get("paginationToken")
                    if nxt is None:
                        return data,pages
                    if not isinstance(nxt,str) or not nxt or nxt==token:
                        raise ValueError("gtfa_pagination_nonadvancing")
                    token=nxt
                    break
                except urllib.error.HTTPError as e:
                    last=f"http_{e.code}"
                    if e.code in (401,402,403):raise ValueError(f"gtfa_capability_or_credential_rejected:{e.code}") from None
                    if attempt<2:time.sleep(2**attempt)
                except urllib.error.URLError:
                    last="transport"
                    if attempt<2:time.sleep(2**attempt)
            else:raise ValueError("gtfa_transport_exhausted:"+str(last))

def normalize_gtfa_item(x):
    # Full-detail gTFA is expected to expose raw transaction fields accepted by the canonical normalizer.
    if not isinstance(x,dict):raise ValueError("gtfa_item_not_object")
    return a2.normalize(x)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pair-root",required=True)
    ap.add_argument("--raw-root",required=True)
    ap.add_argument("--out",default=str(OUT))
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    cfg=a2.cfg();gtfa=GTFA();results=[];errors=[]
    for proto,ref in REFS.items():
        try:
            pair_path,pair=find_pair(Path(args.pair_root),proto,ref["sig"])
            raw_path,raw=find_raw(Path(args.raw_root),ref["sig"])
            expected_path=pair["instruction_address"]
            items,pages=gtfa.call(cfg[proto]["program"],ref["slot"])
            hits=[]
            for item in items:
                try:n=normalize_gtfa_item(item)
                except Exception:continue
                if n["signature"]==ref["sig"]:hits.append(n)
            checks={"signature_hit_count_exact_one":len(hits)==1}
            if len(hits)==1:
                n=hits[0];old=a2.normalize(raw)
                ms=[ix for p,ix in a2.matches(n,cfg) if p==proto and ix["path"]==expected_path]
                oldms=[ix for p,ix in a2.matches(old,cfg) if p==proto and ix["path"]==expected_path]
                checks.update({
                  "slot_exact":n["slot"]==ref["slot"],
                  "explicit_success":n["err"] is None,
                  "exact_instruction_match_count":len(ms)==1,
                  "canonical_shape_pass":len(ms)==1 and a2.shape(proto,ms[0]),
                  "a2_exact_instruction_match_count":len(oldms)==1,
                  "normalized_raw_fidelity_exact":a2.fidelity(n)==a2.fidelity(old)
                })
                if proto=="save11" and len(ms)==1 and len(oldms)==1:
                    checks["save11_unit_exact"]=a2.unit(n,ms[0])==a2.unit(old,oldms[0])
            passed=all(checks.values())
            results.append({
              "protocol":proto,"signature":ref["sig"],"slot":ref["slot"],
              "expected_instruction_address":expected_path,"gtfa_items_in_exact_slot":len(items),
              "gtfa_pages":pages,"checks":checks,"pass":passed,
              "pair_receipt_member":str(pair_path),"a2_raw_member":str(raw_path)
            })
        except Exception as e:
            reason=str(e)
            if "api-key" in reason.lower():reason="redacted_error"
            errors.append({"protocol":proto,"reason":reason[:240]})
            results.append({"protocol":proto,"signature":ref["sig"],"slot":ref["slot"],"pass":False})
    passed=len(results)==4 and all(r.get("pass") for r in results) and not errors
    receipt={
      "schema_version":"0.1","lab_id":LAB,
      "classification":"ROUTE_A3_GTFA_EQUIVALENCE_PASS" if passed else "ROUTE_A3_GTFA_EQUIVALENCE_BLOCKED",
      "results":results,"errors":errors,"gtfa_rpc_call_count":gtfa.calls,
      "science_changed":False,
      "firewall":{"protected_2025_acquisition":False,"prices":False,"returns":False,"pnl":False,
                  "data_2026":False,"purchases":False,"live_trading":False,"orders":False,
                  "wallets":False,"exchange_mutation":False,"merge_main":False},
      "trading_authority":"NONE"
    }
    p=out/"DLS_ROUTE_A3_GTFA_EQUIVALENCE_RECEIPT_V0.1.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"protocols":{r["protocol"]:r.get("pass",False) for r in results},
                      "gtfa_rpc_call_count":gtfa.calls,"error_reasons":[e["reason"] for e in errors]},indent=2,sort_keys=True))
    if not passed:raise SystemExit(2)
if __name__=="__main__":main()
