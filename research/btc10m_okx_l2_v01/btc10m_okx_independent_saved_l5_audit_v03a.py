#!/usr/bin/env python3
"""Independent offline proof of 4 original partial source hashes, L5 features and 10 signed outcomes."""
import hashlib,json,math,pathlib
D=pathlib.Path("downloaded");O=pathlib.Path("artifacts/btc10m_okx_l2_independent_saved_states_v03a")
O.mkdir(parents=True,exist_ok=True)
dates=("2024-01-01","2025-01-01")
def p(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-10)
def validate_l5(state,target):
    assert state["status"]=="VALID_L2_STATE"
    assert state["target_ms"]==target
    assert 0<=target-state["last_ts"]<=2000
    bids=state["bids5"];asks=state["asks5"]
    assert len(bids)==len(asks)==5
    assert all(float(bids[i][0])>float(bids[i+1][0]) for i in range(4))
    assert all(float(asks[i][0])<float(asks[i+1][0]) for i in range(4))
    assert bids[0][0]<asks[0][0]
    bn=sum(float(x[0])*float(x[1]) for x in bids)
    an=sum(float(x[0])*float(x[1]) for x in asks)
    assert bn>0 and an>0
    im=(bn-an)/(bn+an)
    spr=20000*(asks[0][0]-bids[0][0])/(asks[0][0]+bids[0][0])
    mid=(asks[0][0]+bids[0][0])/2
    assert p(im,state["imbalance"]) and p(spr,state["spread_bps"]) and p(mid,state["mid"])
    assert 0<spr<=10
    return im
def main():
    orig=json.loads((D/"receipt.json").read_text())
    assert orig["status"]=="ZERO_SIGNALS_IN_TINY_FIRST_HOUR_HISTORIC_PILOT"
    results={"study":"BTC10M_OKX_ORIGINAL_HISTORIC_L2_V03A_INDEPENDENT_SAVED_STATES_AUDIT",
       "original_run":41240703723,"origin_artifact":13057107103,
       "new_market_api_requests":0,"status":"INDEPENDENT_AUDIT_FAIL","days":[],
       "original_source_partial_sha_verified":0,"frozen_slots_retested":0,
       "pair_samples":0,"opposite_signed_pair_samples":0,
       "individual_threshold_pair_samples":0,
       "three_consecutive_all_pass_signals":0}
    for meta in orig["source_receipts"]:
        filename=meta["partial_raw_filename"]
        with (D/filename).open("rb") as file:
            digest=hashlib.sha256()
            while True:
                chunk=file.read(2*1024*1024)
                if not chunk:break
                digest.update(chunk)
        assert digest.hexdigest()==meta["raw_partial_sha256"]
        assert meta["source_status"]=="ALL_FROZEN_ASOF_TARGETS_RECONSTRUCTED"
        assert meta["valid_asof_state_count"]==21
        results["original_source_partial_sha_verified"]+=1
    for day in dates:
        data=json.loads((D/f"{day}_strict_asof_reconstruction.json").read_text())
        spot=data["spot_states"];swap=data["swap_states"]
        rows=orig["observations_by_day"][day]
        assert len(rows)==5
        report={"day":day,"slots":5,"revalidated_pairs":0,"qualified":0}
        for row in rows:
            assert row["side"]=="ABSTAIN" and row["status"]=="PAPER_L2_SAMPLE_VALID"
            assert row["qualified_outcome_correct"] is None
            base=row["decision_ms"]-24000
            imbalances=[]
            for seconds in (12000,17000,22000):
                t=base+seconds
                a=validate_l5(spot[str(t)],t)
                b=validate_l5(swap[str(t)],t)
                imbalances.append((a,b))
                report["revalidated_pairs"]+=1
                results["pair_samples"]+=1
                if a*b<0:results["opposite_signed_pair_samples"]+=1
                if (a>=.25 and b<=-.25) or (a<=-.25 and b>=.25):
                    results["individual_threshold_pair_samples"]+=1
            assert all(p(a,prev[0]) and p(b,prev[1]) for (a,b),prev in zip(imbalances,row["three_venue_imbalances"]))
            assert validate_l5(spot[str(base+24000)],base+24000) is not None
            assert validate_l5(spot[str(base+624000)],base+624000) is not None
            ups=all(a>=.25 and b<=-.25 for a,b in imbalances)
            downs=all(a<=-.25 and b>=.25 for a,b in imbalances)
            assert not (ups or downs)  # original 0/10
            results["frozen_slots_retested"]+=1
        results["days"].append(report)
    assert results["original_source_partial_sha_verified"]==4
    assert results["pair_samples"]==30
    assert results["frozen_slots_retested"]==10
    results["status"]="INDEPENDENT_ORIGINAL_L2_FEATURE_AND_ABSTAIN_REPLAY_PASS"
    return results
try:o=main()
except Exception as e:
    o={"study":"BTC10M_OKX_ORIGINAL_HISTORIC_L2_V03A_INDEPENDENT_SAVED_STATES_AUDIT",
       "status":"INDEPENDENT_AUDIT_FAIL",
       "error":type(e).__name__+":"+str(e)[:220],"new_market_api_requests":0}
(O/"receipt.json").write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
print("FINAL_INDEPENDENT_AUDIT",json.dumps(o,sort_keys=True),flush=True)
if o["status"]!="INDEPENDENT_ORIGINAL_L2_FEATURE_AND_ABSTAIN_REPLAY_PASS":raise SystemExit(2)
