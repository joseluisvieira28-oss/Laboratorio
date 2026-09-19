#!/usr/bin/env python3
from __future__ import annotations
import json, sys, time
from datetime import date, datetime, timezone
from pathlib import Path
import requests

LAB_ID="ETH-STAKING-FLOW-001"
GENESIS_TIME=1606824023
EPOCH_SECONDS=384
SLOTS_PER_EPOCH=32
MAX_OFFSET_SECONDS=384

ENDPOINTS=[
    "https://beaconstate-mainnet.chainsafe.io",
    "https://beaconstate.ethstaker.cc",
    "http://testing.mainnet.beacon-api.nimbus.team",
]

CONTROLS={
    "2025-02-24":{"epoch":347738,"unix":1740355415,"pending_queued":0,"active_exiting":5,"net_queue":-5},
    "2025-03-02":{"epoch":349088,"unix":1740873815,"pending_queued":0,"active_exiting":0,"net_queue":0},
    "2025-10-17":{"epoch":400613,"unix":1760659415,"pending_queued":48,"active_exiting":55209,"net_queue":-55161},
}
MISSING=[
    "2025-02-25","2025-02-26","2025-02-27","2025-02-28",
    "2025-03-01","2025-10-18","2025-10-19",
]

def target(ds:str):
    d=date.fromisoformat(ds)
    midnight=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
    epoch=(midnight-GENESIS_TIME + EPOCH_SECONDS-1)//EPOCH_SECONDS
    ts=GENESIS_TIME+epoch*EPOCH_SECONDS
    if not(midnight <= ts <= midnight+MAX_OFFSET_SECONDS):
        raise RuntimeError(f"{ds}: epoch boundary outside frozen +32-slot bound")
    return int(epoch),int(epoch*SLOTS_PER_EPOCH),int(ts)

def fetch_status(session,endpoint,slot,status):
    url=f"{endpoint.rstrip('/')}/eth/v1/beacon/states/{slot}/validators"
    last=None
    for attempt in range(3):
        try:
            r=session.get(url,params=[("status",status)],headers={
                "Accept":"application/json",
                "User-Agent":f"{LAB_ID}/v3-stagea-beacon-remediation-v0.1.4",
            },timeout=(10,120))
            code=r.status_code
            if code!=200:
                body=r.text[:300]
                r.close()
                return {"usable":False,"http_status":code,"error":body,"count":None}
            obj=r.json()
            r.close()
            data=obj.get("data")
            if not isinstance(data,list):
                return {"usable":False,"http_status":code,"error":"response data not list","count":None}
            bad=[x for x in data if str(x.get("status"))!=status]
            if bad:
                return {"usable":False,"http_status":code,"error":f"status filter mismatch count={len(bad)}","count":None}
            return {"usable":True,"http_status":code,"error":None,"count":len(data)}
        except Exception as exc:
            last=f"{type(exc).__name__}: {str(exc)[:300]}"
            if attempt<2:
                time.sleep(2**attempt)
                continue
    return {"usable":False,"http_status":None,"error":last,"count":None}

def main():
    out=Path("eth_staking_beacon_remediation_output")
    out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_V3_STAGEA_BEACON_REMEDIATION_V0_1_4.json"

    all_dates=list(CONTROLS)+MISSING
    rows={}
    technical=False
    provenance=False
    control_mismatch=False

    for ds in all_dates:
        epoch,slot,ts=target(ds)
        if ds in CONTROLS:
            c=CONTROLS[ds]
            if (epoch,ts)!=(c["epoch"],c["unix"]):
                raise RuntimeError(f"{ds}: deterministic epoch geometry mismatch {(epoch,ts)} vs {(c['epoch'],c['unix'])}")
        endpoint_rows={}
        agreed=[]
        for endpoint in ENDPOINTS:
            s=requests.Session()
            p=fetch_status(s,endpoint,slot,"pending_queued")
            e=fetch_status(s,endpoint,slot,"active_exiting")
            s.close()
            usable=bool(p["usable"] and e["usable"])
            erow={"usable":usable,"pending":p,"exiting":e}
            if usable:
                erow["pending_queued_count"]=int(p["count"])
                erow["active_exiting_count"]=int(e["count"])
                erow["net_queue_count"]=int(p["count"])-int(e["count"])
                agreed.append((erow["pending_queued_count"],erow["active_exiting_count"]))
            endpoint_rows[endpoint]=erow

        usable_count=len(agreed)
        uniq=sorted(set(agreed))
        classification="DATE_SOURCE_PASS"
        if usable_count<2:
            classification="DATE_SOURCE_TECHNICAL_FAILURE"; technical=True
        elif len(uniq)!=1:
            classification="DATE_SOURCE_PROVENANCE_FAILURE"; provenance=True

        canonical=None
        if classification=="DATE_SOURCE_PASS":
            canonical={"pending_queued_count":uniq[0][0],"active_exiting_count":uniq[0][1],
                       "net_queue_count":uniq[0][0]-uniq[0][1]}
            if ds in CONTROLS:
                c=CONTROLS[ds]
                if canonical["pending_queued_count"]!=c["pending_queued"] or canonical["active_exiting_count"]!=c["active_exiting"] or canonical["net_queue_count"]!=c["net_queue"]:
                    classification="CONTROL_EQUIVALENCE_FAILURE"
                    control_mismatch=True

        rows[ds]={
            "date":ds,"target_epoch":epoch,"target_slot":slot,"target_unix_time":ts,
            "classification":classification,"usable_endpoint_count":usable_count,
            "endpoint_results":endpoint_rows,"canonical_counts":canonical,
            "is_control":ds in CONTROLS,
        }
        print(json.dumps({"date":ds,"classification":classification,"usable_endpoints":usable_count,
                          "counts":canonical,"signal":False,"market":False,"returns":False,"pnl":False},sort_keys=True),flush=True)

    controls_pass=all(rows[d]["classification"]=="DATE_SOURCE_PASS" for d in CONTROLS)
    missing_pass=all(rows[d]["classification"]=="DATE_SOURCE_PASS" for d in MISSING)

    if provenance:
        final="SOURCE_PROVENANCE_FAILURE"
    elif control_mismatch:
        final="SOURCE_EQUIVALENCE_FAILURE"
    elif technical or not controls_pass or not missing_pass:
        final="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    else:
        final="BEACON_API_EQUIVALENT_SOURCE_RECOVERY_PASS"

    receipt={
        "lab_id":LAB_ID,
        "phase":"V3_STAGE_A_INDEPENDENT_BEACON_STATE_SOURCE_REMEDIATION_V0_1_4",
        "classification":final,
        "control_dates":list(CONTROLS),
        "missing_dates":MISSING,
        "endpoints":ENDPOINTS,
        "date_results":rows,
        "controls_equivalent":controls_pass and not control_mismatch,
        "missing_dates_recovered":missing_pass and controls_pass and not control_mismatch and not provenance,
        "safety":{
            "signal_evaluated":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
            "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
            "source_after_2026_08_31_opened":False,
        }
    }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":final,"controls_equivalent":receipt["controls_equivalent"],
                      "missing_dates_recovered":receipt["missing_dates_recovered"],
                      "signal":False,"market":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if final=="BEACON_API_EQUIVALENT_SOURCE_RECOVERY_PASS" else 2

if __name__=="__main__":
    sys.exit(main())
