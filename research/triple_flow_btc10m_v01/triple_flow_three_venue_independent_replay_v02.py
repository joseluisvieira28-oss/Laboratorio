#!/usr/bin/env python3
"""Independent replay of original 3-venue public WS source archive. NO outcomes."""
import hashlib,io,json,pathlib,zipfile
from triple_flow_three_venue_stream_source_v02 import make,classify_msg
VENUES=("BYBIT","OKX","MEXC")
EXPECTED={"bybit_source_ws.ndjson","okx_source_ws.ndjson",
          "mexc_source_ws.ndjson","source_receipt.json"}
FIELDS=("subscription_ack","pongs_received","trade_messages","trade_children",
        "index_messages","liquidation_messages","liquidation_children",
        "long_liquidated","short_liquidated","buy_trade_children","sell_trade_children",
        "max_age_ms","min_event_server_ts","max_event_server_ts")
def digest(raw):return hashlib.sha256(raw).hexdigest()
def check_zip(raw_bytes,expected_sha):
    if expected_sha and digest(raw_bytes)!=expected_sha:raise ValueError("EXACT_SERVER_ZIP_HASH_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
        if set(z.namelist())!=EXPECTED:raise ValueError("WRONG_WS_ARCHIVE_FILES")
        receipt=json.loads(z.read("source_receipt.json"))
        if receipt.get("study")!="TRIPLE_FLOW_BTC10M_THREE_PUBLIC_WEBSOCKETS_V02" or receipt.get("duration_seconds_frozen")!=120:
            raise ValueError("NOT_FROZEN_V02_ORIGINAL_SOURCE")
        actual={}
        for venue in VENUES:
            name=venue.lower()+"_source_ws.ndjson"
            stored=z.read(name)
            manifest=[e for e in receipt["raw_manifest"] if e["file"]==name]
            if len(manifest)!=1:raise ValueError("MISSING_RAW_MANIFEST")
            m=manifest[0]
            if digest(stored)!=m["sha256"] or len(stored)!=m["size_bytes"] or stored.count(b"\n")!=m["rows"]:
                raise ValueError("RAW_ARCHIVE_HASH_COUNT_SIZE_MISMATCH")
            state=make(venue);timestamps=[];issues=[]
            for line in stored.splitlines():
                rec=json.loads(line)
                body=rec.get("raw_utf8")
                if rec.get("venue")!=venue or not isinstance(body,str) or digest(body.encode())!=rec.get("source_sha256"):
                    raise ValueError("FORGED_RAW_FRAME_OR_VENUE")
                if type(rec.get("received_ms")) is not int:raise ValueError("MISSING_FRAME_LOCAL_TIME")
                try:
                    classify_msg(venue,body,rec["received_ms"],state)
                except Exception as e:
                    issues.append(type(e).__name__+":"+str(e))
            for field in FIELDS:
                if state.get(field)!=receipt["streams"][venue].get(field):
                    raise ValueError("INDEPENDENT_SEMANTIC_COUNT_MISMATCH_"+venue+"_"+field)
            # A real source gate cannot self-certify a real message if replay finds invalid frames.
            if receipt["status"]=="THREE_PUBLIC_WS_SCHEMA_SOURCE_PASS" and (issues or receipt["streams"][venue]["errors"]):
                raise ValueError("CLEAN_SOURCE_CLAIM_WITH_REPLAY_ERRORS")
            actual[venue]={"frames":m["rows"],
              "trade_children":state["trade_children"],
              "liquidation_children":state["liquidation_children"],
              "index_messages":state["index_messages"],
              "buy_trade_children":state["buy_trade_children"],
              "sell_trade_children":state["sell_trade_children"],
              "max_source_age_ms":state["max_age_ms"],
              "replay_issue_count":len(issues)}
        if receipt["market_10m_outcomes_opened"]!=0 or receipt["model_predictions_issued"]!=0:
            raise ValueError("NOT_A_SOURCE_ONLY_STUDY")
        return {"study":"TRIPLE_FLOW_BTC10M_V02_INDEPENDENT_REAL_SOURCE_REPLAY",
           "status":"EXACT_THREE_VENUE_RAW_COUNTS_RECONSTRUCTED",
           "original_source_status":receipt["status"],
           "liquidation_status":receipt["liquidation_status"],
           "sources":actual,"original_zip_sha256":digest(raw_bytes),
           "10minute_outcomes_read":0,"actual_event_futures_settlement_proven":False,
           "economic_edge_proven":False}
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--zip",required=True);p.add_argument("--sha256")
    args=p.parse_args()
    out=check_zip(pathlib.Path(args.zip).read_bytes(),args.sha256)
    dest=pathlib.Path("artifacts/triple_flow_btc10m_ws_replay_v02")
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"independent_replay.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__":main()
