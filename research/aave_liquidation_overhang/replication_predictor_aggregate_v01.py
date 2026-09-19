#!/usr/bin/env python3
"""Aggregate 8 reserve shards into the frozen 2024 Aave liquidation-overhang replication predictor."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator


LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"


def load_one(root:str,classification:str)->dict[str,Any]:
    xs=[]
    for p in Path(root).rglob("*.json"):
        o=json.loads(p.read_text())
        if o.get("classification")==classification: xs.append(o)
    if len(xs)!=1: raise RuntimeError(f"expected one {classification} under {root}, got {len(xs)}")
    return xs[0]


def percent_mul(value:int,pct:int)->int:
    return (value*pct+5000)//10000


def grouped_rows(path:Path)->Iterator[tuple[int,list[dict[str,Any]]]]:
    current=None; rows=[]
    with gzip.open(path,"rt",encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            r=json.loads(line); d=int(r["d"])
            if current is None: current=d
            if d!=current:
                yield current,rows
                current=d; rows=[]
            rows.append(r)
    if current is not None: yield current,rows


def verify_rows_hash(path:Path,expected:str)->None:
    h=hashlib.sha256()
    with gzip.open(path,"rt",encoding="utf-8") as f:
        for line in f: h.update(line.encode())
    if h.hexdigest()!=expected:
        raise RuntimeError(f"row digest mismatch {path.name}")


def main()->int:
    out=Path("replication_predictor_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_REPLICATION_PREDICTOR_2024_V0_1.json"
    receipt={}
    try:
        cal=load_one("downloaded_replication_calendar","REPLICATION_CALENDAR_PASS")
        glob=load_one("downloaded_replication_global","REPLICATION_GLOBAL_SOURCE_PASS")
        snaps=cal["snapshots"]
        if len(snaps)!=366: raise RuntimeError("snapshot count mismatch")

        meta_files=sorted(Path("downloaded_replication_reserves").rglob("replication_reserve_shard_*_meta.json"))
        row_files=sorted(Path("downloaded_replication_reserves").rglob("replication_reserve_shard_*_rows.jsonl.gz"))
        if len(meta_files)!=8 or len(row_files)!=8:
            raise RuntimeError(f"expected 8 reserve meta + row files, got {len(meta_files)} + {len(row_files)}")
        metas=[json.loads(p.read_text()) for p in meta_files]
        if any(x.get("classification")!="REPLICATION_RESERVE_SHARD_PASS" for x in metas):
            raise RuntimeError("one or more reserve shards did not PASS")
        ids=sorted(int(x["shard_id"]) for x in metas)
        if ids!=list(range(8)): raise RuntimeError(f"reserve shard ids mismatch {ids}")
        reserves=[]
        reserve_decimals={}
        for x in metas:
            reserves.extend(x["selected_reserves"])
            reserve_decimals.update({k:int(v) for k,v in (x.get("decimals") or {}).items()})
        if len(reserves)!=37 or len(set(reserves))!=37:
            raise RuntimeError(f"canonical reserve master union is not exact 37: {len(reserves)} / {len(set(reserves))}")
        if len(reserve_decimals)!=37:
            raise RuntimeError(f"active 2024 reserve decimals union is not exact 37: {len(reserve_decimals)}")
        if not set(reserve_decimals).issubset(set(reserves)):
            raise RuntimeError("active 2024 reserve decimals escaped canonical reserve master")

        by_id={int(x["shard_id"]):x for x in metas}
        row_by_id={}
        for p in row_files:
            # Parse fixed filename suffix.
            sid=int(p.name.split("_")[2])
            row_by_id[sid]=p
        if set(row_by_id)!=set(range(8)): raise RuntimeError("row shard filenames mismatch")
        for sid,p in row_by_id.items():
            verify_rows_hash(p,by_id[sid]["row_sha256"])

        gens={sid:grouped_rows(row_by_id[sid]) for sid in range(8)}
        heads={}
        for sid,g in gens.items():
            try: heads[sid]=next(g)
            except StopIteration: heads[sid]=None

        user_events=sorted(glob.get("user_emode_events") or [],key=lambda x:(int(x["block"]),int(x["logIndex"])))
        cat_events=sorted(glob.get("emode_category_events") or [],key=lambda x:(int(x["block"]),int(x["logIndex"])))
        user_mode={}; categories={}; ui=0; ci=0
        daily=[]; predictor_hash=hashlib.sha256()

        for d,snap in enumerate(snaps):
            b=int(snap["block"])
            while ci<len(cat_events) and int(cat_events[ci]["block"])<=b:
                e=cat_events[ci]; categories[int(e["category"])]={
                    "liquidationThreshold":int(e["liquidationThreshold"]),
                    "oracle":e["oracle"],
                }; ci+=1
            while ui<len(user_events) and int(user_events[ui]["block"])<=b:
                e=user_events[ui]; user=str(e["user"]).lower(); mode=int(e["category"])
                if mode==0: user_mode.pop(user,None)
                else: user_mode[user]=mode
                ui+=1

            users=defaultdict(lambda:{"debt":0,"coll":0,"w":0,"s5":0,"s10":0,"s20":0})
            source_rows=0
            for sid in range(8):
                head=heads[sid]
                if head is None: continue
                hd,hrows=head
                if hd<d: raise RuntimeError(f"shard {sid} row day regressed")
                if hd>d: continue
                for r in hrows:
                    user=str(r["u"]).lower(); coll=int(r["c"]); debt=int(r["q"])
                    normal_lt=int(r["lt"]); reserve_cat=int(r["ec"])
                    mode=int(user_mode.get(user,0))
                    if mode>0 and reserve_cat==mode:
                        if mode not in categories:
                            raise RuntimeError(f"undefined eMode category {mode} at {snap['date']}")
                        if int(categories[mode]["oracle"],16)!=0:
                            raise RuntimeError(f"nonzero eMode oracle escaped global gate for category {mode}")
                        lt=int(categories[mode]["liquidationThreshold"])
                    else:
                        lt=normal_lt
                    u=users[user]
                    u["debt"]+=debt; u["coll"]+=coll
                    u["w"]+=percent_mul(coll,lt)
                    u["s5"]+=percent_mul((coll*9500)//10000,lt)
                    u["s10"]+=percent_mul((coll*9000)//10000,lt)
                    u["s20"]+=percent_mul((coll*8000)//10000,lt)
                    source_rows+=1
                try: heads[sid]=next(gens[sid])
                except StopIteration: heads[sid]=None

            over5=over10=over20=0
            count5=count10=count20=0
            latent_coll10=0; baseline_liq_debt=0; borrowers_with_debt=0
            min_positive_hf_num=None; min_positive_hf_den=None
            for _user,u in users.items():
                debt=u["debt"]
                if debt<=0: continue
                borrowers_with_debt+=1
                if u["w"]<=debt:
                    baseline_liq_debt+=debt
                    continue
                if u["s5"]<=debt:
                    over5+=debt; count5+=1
                if u["s10"]<=debt:
                    over10+=debt; count10+=1; latent_coll10+=u["coll"]
                if u["s20"]<=debt:
                    over20+=debt; count20+=1

            row={
                "date":snap["date"],"snapshot_block":b,
                "overhang_debt_10":str(over10),
                "latent_borrower_count_10":count10,
                "latent_collateral_value_10":str(latent_coll10),
                "baseline_liquidatable_debt":str(baseline_liq_debt),
                "overhang_debt_5":str(over5),"latent_borrower_count_5":count5,
                "overhang_debt_20":str(over20),"latent_borrower_count_20":count20,
                "borrowers_with_debt":borrowers_with_debt,
                "reserve_partial_rows":source_rows,
            }
            daily.append(row)
            predictor_hash.update((json.dumps(row,separators=(",",":"),sort_keys=True)+"\n").encode())

        if any(v is not None for v in heads.values()):
            raise RuntimeError("reserve row stream contains unexpected extra day indexes")
        if len(daily)!=366: raise RuntimeError("daily predictor count mismatch")

        receipt={
            "lab_id":LAB_ID,
            "classification":"REPLICATION_PREDICTOR_PASS",
            "protocol":"AAVE_LIQUIDATION_OVERHANG_001_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1",
            "execution_authority":"AAVE_LIQUIDATION_OVERHANG_001_2024_REPLICATION_EXECUTION_AUTHORITY_V0_1",
            "snapshot_count":len(daily),
            "reserve_count":27,
            "full_r1_reserve_count":37,
            "predictor_sha256":predictor_hash.hexdigest(),
            "daily_predictor":daily,
            "days_overhang_10_positive":sum(1 for x in daily if int(x["overhang_debt_10"])>0),
            "reserve_decimals":dict(sorted(reserve_decimals.items())),
            "source_shard_digests":{str(x["shard_id"]):x["row_sha256"] for x in metas},
            "safety":{
                "health_factor_computed":True,"overhang_computed":True,
                "future_liquidation_outcomes_opened":False,
                "opened_2024_predictor":True,"opened_2024_outcomes":False,
                "opened_2025_or_2026":False,
                "market_returns_opened":False,"pnl_opened":False,
                "live_trading":False,"exchange_mutation":False,
            },
        }
    except Exception as exc:
        receipt={
            "lab_id":LAB_ID,"classification":"REPLICATION_RECONSTRUCTION_FAILURE",
            "failure":f"{type(exc).__name__}: {str(exc)[:1600]}",
            "safety":{"health_factor_computed":True,"overhang_computed":False,
                      "future_liquidation_outcomes_opened":False,
                      "opened_2024_predictor":True,"opened_2024_outcomes":False,
                      "opened_2025_or_2026":False,"market_returns_opened":False,
                      "pnl_opened":False,"live_trading":False,"exchange_mutation":False},
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"snapshots":receipt.get("snapshot_count"),
                      "days_overhang_10_positive":receipt.get("days_overhang_10_positive"),
                      "predictor_sha256":receipt.get("predictor_sha256"),
                      "future_liquidation_outcomes_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="REPLICATION_PREDICTOR_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())
