#!/usr/bin/env python3
import json,time,urllib.request,datetime as dt
from pathlib import Path
RPC="https://api.mainnet-beta.solana.com"
ANCHORS=[
{"protocol":"kamino_lend","program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","before":"37bfneBLcVoWnqWEoP7Y4EnJREUeaHeEYgnQ9kjBGpsN3tMjP2AceURMpbgQDeR8hmxZ4L5JVSokepJ7WhsuTDnK"},
{"protocol":"marginfi_v2","program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA","before":"4Woi6qL1sdzaFgTQkrLLqkvnUm9dncraHTWmcnsvpQ8B4EbVwUcMXpDBJT5YEZiFLXwSRhoWvJAkpbnwg4rBSxgH"},
{"protocol":"drift_v2","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","before":"4HxbJXnf4mu5WybzTm6pgu5JbsAbU4hhyM7UKbiZ92dehj7MD6T2qWj1HcWZc2q32y3fFv5wFTSxRNfzHBNsef1d"},
{"protocol":"save_solend","program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","before":"3kefBPaiAPXNDJrnsp6idVtovy1hPgYekLQvKcFf3X4aypJhXpaxGR2CKRP931tDxff46YGAMqfzFgVf4EwyBRzm"},
]
def call(a):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress","params":[a["program"],{"before":a["before"],"limit":1000,"commitment":"finalized"}]}).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-source-feasibility/0.1"})
    last=None
    for i in range(6):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read())
        except Exception as e:
            last=repr(e);time.sleep(min(2*(i+1),10))
    return {"transport_error":last}
rows=[]
rawdir=Path("dls_public_rpc_history_feasibility_v01");rawdir.mkdir(exist_ok=True)
for i,a in enumerate(ANCHORS):
    o=call(a)
    (rawdir/f'{i:02d}_{a["protocol"]}.json').write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    rec={"protocol":a["protocol"],"program":a["program"],"before":a["before"]}
    if "transport_error" in o:
        rec.update(status="TRANSPORT_ERROR",detail=o["transport_error"]);rows.append(rec);continue
    if o.get("error"):
        rec.update(status="RPC_ERROR",detail=o["error"]);rows.append(rec);continue
    xs=o.get("result")
    if not isinstance(xs,list):
        rec.update(status="MALFORMED_RESULT");rows.append(rec);continue
    ts=[x.get("blockTime") for x in xs if isinstance(x.get("blockTime"),int)]
    slots=[x.get("slot") for x in xs if isinstance(x.get("slot"),int)]
    rec.update(
      status="PASS_PAGE",
      returned_rows=len(xs),
      null_blocktime_rows=sum(x.get("blockTime") is None for x in xs),
      newest_blocktime=max(ts) if ts else None,
      oldest_blocktime=min(ts) if ts else None,
      span_seconds=(max(ts)-min(ts)) if ts else None,
      newest_slot=max(slots) if slots else None,
      oldest_slot=min(slots) if slots else None,
      last_signature=(xs[-1].get("signature") if xs else None)
    )
    if rec["span_seconds"] is not None:
        rec["span_hours"]=rec["span_seconds"]/3600
        rec["span_days"]=rec["span_seconds"]/86400
        rec["pages_per_year_linear_estimate"]=(365.25/rec["span_days"]) if rec["span_days"]>0 else None
    rows.append(rec);time.sleep(1)
summary={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"PUBLIC_RPC_HISTORY_PAGINATION_FEASIBILITY_COMPLETE",
 "boundary_adjudication":False,"source_data_pass":False,"endpoint":RPC,"page_limit":1000,
 "rows":rows,
 "firewalls":{"transaction_bodies_queried":False,"liquidation_decoding":False,"prices":False,"returns":False,"pnl":False,"direction":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False}
}
(rawdir/"DLS_PUBLIC_RPC_HISTORY_PAGINATION_FEASIBILITY_RECEIPT_V0.1.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,indent=2,sort_keys=True))
