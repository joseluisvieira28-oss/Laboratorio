from __future__ import annotations
import json, pathlib, urllib.error, urllib.parse, urllib.request

OUT=pathlib.Path(__file__).resolve().parent/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

BLOCK_HASH="0x9edf97c70295a97dab59620b7feec61588563cd10ad1ab7bd85669b9658c8def"
RELAYS={
    "flashbots":"https://boost-relay.flashbots.net",
    "ultrasound":"https://relay.ultrasound.money",
    "titan":"https://titanrelay.xyz",
    "agnostic":"https://agnostic-relay.net",
    "aestus":"https://aestus.live",
}

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-AMM-LVR-001-relay-matrix/0.1","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read().decode("utf-8","ignore")
            try: body=json.loads(raw)
            except Exception: body=raw[:1200]
            return {"status":r.status,"body":body}
    except urllib.error.HTTPError as e:
        raw=e.read(2000).decode("utf-8","ignore")
        try: body=json.loads(raw)
        except Exception: body=raw[:1200]
        return {"status":e.code,"body":body}
    except Exception as e:
        return {"status":None,"error":type(e).__name__+":"+str(e)[:500]}

matrix={}
matches=[]
for name,base in RELAYS.items():
    q=urllib.parse.urlencode({"block_hash":BLOCK_HASH})
    url=base+"/relay/v1/data/bidtraces/proposer_payload_delivered?"+q
    res=get(url)
    body=res.get("body")
    rows=body if isinstance(body,list) else []
    matrix[name]={"status":res.get("status"),"row_count":len(rows),"error":res.get("error")}
    if rows:
        matrix[name]["first"]=rows[0]
        matches.append({"relay":name,"payload":rows[0]})

receipt={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"RELAY_PAYLOAD_MATRIX_V0.1",
    "block_hash":BLOCK_HASH,
    "relay_count":len(RELAYS),
    "matches":matches,
    "matrix":matrix,
    "verdict":"RELAY_PAYLOAD_ATTRIBUTION_PASS" if matches else "RELAY_PAYLOAD_NOT_FOUND_IN_PROBED_RELAYS",
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "note":"Public relay Data API attribution for a frozen forward-observed block. Payload value is block-level proposer payment context, not transaction-specific searcher cost."
}
(OUT/"relay_payload_matrix_v0_1_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
