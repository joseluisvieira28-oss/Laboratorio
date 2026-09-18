#!/usr/bin/env python3
import hashlib, json, sys, time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUT=Path("artifacts/eth_staking_flow_archive_probe_v03"); OUT.mkdir(parents=True,exist_ok=True)
GENESIS=1606824023
DATES=[date(2023,4,12),date(2024,12,31)]
PROVIDERS=[
  "https://lodestar-mainnet.chainsafe.io",
  "http://testing.mainnet.beacon-api.nimbus.team",
  "https://ethereum-beacon-api.publicnode.com",
  "https://rpc.ankr.com/eth_beacon",
  "https://eth-mainnetbeacon.g.alchemy.com/v2/docs-demo",
]
FILTERS=["pending_queued","active_exiting"]

def slot_for_day(d):
    ts=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
    return (ts-GENESIS)//12

def sha(b): return hashlib.sha256(b).hexdigest()

def get(url):
    req=Request(url,headers={"User-Agent":"ETH-STAKING-FLOW-001-archive-probe/0.3","Accept":"application/json"})
    try:
        with urlopen(req,timeout=50) as r:
            return int(r.status),dict(r.headers),r.read()
    except HTTPError as e:
        return int(e.code),dict(e.headers),e.read()
    except (URLError,TimeoutError,OSError) as e:
        return 0,{},str(e).encode()

def valid_validator_array(body):
    try:
        obj=json.loads(body)
    except Exception:
        return False,None
    data=obj.get("data") if isinstance(obj,dict) else None
    if not isinstance(data,list):
        return False,None
    for row in data:
        if not isinstance(row,dict) or "status" not in row or "index" not in row:
            return False,None
    return True,len(data)

receipt={
  "family_id":"ETH-STAKING-FLOW-001",
  "parent_mve":"ESF-NETQUEUE-7D-001",
  "probe_id":"ESF-ARCHIVE-TRANSPORT-PROBE-003",
  "classification":None,
  "providers":[],
  "selected_provider":None,
  "firewall":{"access_2025":False,"access_2026":False,"price_values_opened":False,
    "signal_series_computed":False,"discovery_event_count_computed":False,
    "returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,
    "live_trading":False,"exchange_mutation":False,"wallet_access":False,"merge_to_main":False}
}
selected=None
for base in PROVIDERS:
    pr={"base":base,"boundary_results":[],"pass":False}
    auth_block=False
    for d in DATES:
        target=slot_for_day(d); chosen=None
        attempts=[]
        for off in range(33):
            slot=target+off; slotrows={}; ok=True
            for status_filter in FILTERS:
                url=f"{base}/eth/v1/beacon/states/{slot}/validators?status={status_filter}"
                code,hdr,body=get(url)
                rec={"date":d.isoformat(),"target_slot":target,"slot":slot,"offset":off,
                     "status_filter":status_filter,"http_status":code,"bytes":len(body),"sha256":sha(body)}
                if code in (401,402,403):
                    auth_block=True; ok=False; attempts.append(rec); break
                if code!=200:
                    ok=False; attempts.append(rec); break
                valid,n=valid_validator_array(body)
                rec["schema_valid"]=valid; rec["validator_rows"]=n
                attempts.append(rec)
                if not valid:
                    ok=False; break
                slotrows[status_filter]=n
            if ok and len(slotrows)==2:
                chosen={"date":d.isoformat(),"target_slot":target,"selected_slot":slot,
                        "slot_offset":off,"pending_queued_rows":slotrows["pending_queued"],
                        "active_exiting_rows":slotrows["active_exiting"]}
                break
            if auth_block: break
            time.sleep(0.02)
        pr["boundary_results"].append({"date":d.isoformat(),"chosen":chosen,"attempts":attempts})
        if auth_block: break
    pr["auth_blocked"]=auth_block
    pr["pass"]=(not auth_block and len(pr["boundary_results"])==2 and all(x["chosen"] is not None for x in pr["boundary_results"]))
    receipt["providers"].append(pr)
    print(json.dumps({"provider":base,"pass":pr["pass"],"auth_blocked":auth_block,
                      "boundary_successes":sum(1 for x in pr["boundary_results"] if x["chosen"] is not None)},sort_keys=True),flush=True)
    if pr["pass"]:
        selected=base; break

if selected:
    receipt["classification"]="ARCHIVE_TRANSPORT_PROBE_PASS"
    receipt["selected_provider"]=selected
else:
    any_auth=any(x["auth_blocked"] for x in receipt["providers"])
    receipt["classification"]="ARCHIVE_TRANSPORT_PROBE_BLOCKED" if any_auth else "ARCHIVE_TRANSPORT_PROBE_TECHNICAL_FAILURE"

p=OUT/"probe_receipt.json";p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
(OUT/"manifest.json").write_text(json.dumps({"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"selected_provider":selected,
                  "provider_summary":[{"base":x["base"],"pass":x["pass"],"auth_blocked":x["auth_blocked"]} for x in receipt["providers"]],
                  "firewall":receipt["firewall"]},indent=2,sort_keys=True))
sys.exit(0)
