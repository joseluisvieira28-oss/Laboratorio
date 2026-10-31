#!/usr/bin/env python3
"""Independent byte/semantic replay of original BTC Triple Flow public SOURCE-only archive.

Audit does not score a ten-minute forward outcome or invent missing liquidation events.
"""
import hashlib,io,json,pathlib,sys,zipfile
from triple_flow_public_joint_source_v01 import validate_bybit_trade,validate_liquidation,validate_rest,URLS
EXPECTED={"bybit_public_ws.ndjson","okx_mexc_public_rest.ndjson","source_gate_receipt.json"}
def sha(b):return hashlib.sha256(b).hexdigest()
def read_rows(body):
    if not body or not body.endswith(b"\n"):raise ValueError("BAD_NDJSON_TERMINATION")
    for line in body.splitlines():
        row=json.loads(line)
        raw=row.get("raw_utf8")
        if not isinstance(raw,str) or sha(raw.encode("utf-8"))!=row.get("source_sha256"):
            raise ValueError("RAW_SOURCE_ROW_HASH_MISMATCH")
        stamp=row.get("received_ms")
        if type(stamp)!=int or stamp<=0:raise ValueError("MISSING_RECEIPT_TIMESTAMP")
        yield row,json.loads(raw)
def audit(archive,expected_zip_sha=None):
    zipbytes=pathlib.Path(archive).read_bytes()
    if expected_zip_sha is not None and sha(zipbytes)!=expected_zip_sha:
        raise ValueError("GITHUB_INDEPENDENT_ARCHIVE_DIGEST_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(zipbytes)) as f:
        names={n for n in f.namelist() if not n.endswith("/")}
        if names!=EXPECTED:raise ValueError("WRONG_ARCHIVE_MEMBER_SET")
        obj=json.loads(f.read("source_gate_receipt.json"))
        if obj.get("study")!="TRIPLE_FLOW_BTC10M_V01_JOINT_PUBLIC_SOURCE_ONLY" or obj.get("duration_spec_seconds")!=150:
            raise ValueError("WRONG_FROZEN_SOURCE_ONLY_SCOPE")
        for entry in obj["raw_archive_manifest"]:
            raw=f.read(entry["file"])
            if sha(raw)!=entry["sha256"] or len(raw)!=entry["size_bytes"] or raw.count(b"\n")!=entry["rows"]:
                raise ValueError("MANIFEST_HASH_SIZE_OR_LINE_COUNT")
        counts={"trade_frames":0,"trade_children":0,"liquidation_frames":0,
            "liquidation_children":0,"long_liquidated":0,"short_liquidated":0,
            "observed_trade_buy":0,"observed_trade_sell":0,
            "pings":0,"pongs":0}
        schema=[]
        for row,msg in read_rows(f.read("bybit_public_ws.ndjson")):
            if row["venue"]!="BYBIT_PUBLIC_LINEAR_WS":raise ValueError("WRONG_WS_VENUE")
            topic=msg.get("topic");recv=row["received_ms"]
            if msg.get("op")=="pong":counts["pongs"]+=1
            elif topic=="publicTrade.BTCUSDT":
                counts["trade_frames"]+=1
                for d in msg.get("data") or []:
                    try:
                        t=validate_bybit_trade(d,recv)
                        counts["trade_children"]+=1
                        counts["observed_trade_buy" if t["side"]=="Buy" else "observed_trade_sell"]+=1
                    except Exception as e:schema.append(type(e).__name__+":"+str(e))
            elif topic=="allLiquidation.BTCUSDT":
                counts["liquidation_frames"]+=1
                for d in msg.get("data") or []:
                    try:
                        x=validate_liquidation(d,recv)
                        counts["liquidation_children"]+=1
                        counts["long_liquidated" if x["liquidated_position"]=="LONG" else "short_liquidated"]+=1
                    except Exception as e:schema.append(type(e).__name__+":"+str(e))
        reported=obj["bybit"]
        for k,v in counts.items():
            if k=="pings":continue
            if reported.get(k)!=v:raise ValueError("BYBIT_RAW_COUNT_PARITY_FAIL_"+k)
        for k in ("mexc_perp_index","mexc_perp_depth","okx_spot_trades","mexc_perp_deals"):
            if k not in obj["rest"]:raise ValueError("MISSING_REST_SOURCE_"+k)
        metrics={k:{"success":0,"rows_observed":0} for k in URLS}
        for row,msg in read_rows(f.read("okx_mexc_public_rest.ndjson")):
            source=row["venue"]
            if source not in URLS:raise ValueError("UNKNOWN_REST_VENUE")
            d=validate_rest(source,msg,row["received_ms"])
            metrics[source]["success"]+=1
            metrics[source]["rows_observed"]+=d.get("rows",1)
        for k,measured in metrics.items():
            for key,value in measured.items():
                if obj["rest"][k].get(key)!=value:
                    raise ValueError("REST_RAW_COUNT_PARITY_FAIL_"+k+"_"+key)
        status=obj["status"]
        if status=="JOINT_SCHEMA_SOURCE_PASS" and (schema or obj["bybit"]["schema_errors"]):
            raise ValueError("CANNOT_CLAIM_CLEAN_SCHEMA_SOURCE_PASS")
        if obj["bybit"]["liquidation_children"]==0 and obj["liquidation_status"]=="LIQUIDATION_SEMANTICS_OBSERVED":
            raise ValueError("LIQUIDATION_SOURCE_CREDIT_WITH_ZERO_EVENTS")
        if obj["directional_forecasts_issued"]!=0 or obj["market_10m_return_labels_read"]!=0:
            raise ValueError("NOT_ALLOWED_TO_RECLASSIFY_AS_SOURCE_ONLY")
        return {"study":"TRIPLE_FLOW_BTC10M_V01_ORIGINAL_ARCHIVE_INDEPENDENT_AUDIT",
            "status":"EXACT_RAW_SOURCE_COUNTS_AND_SEMANTICS_VERIFIED",
            "real_source_status":obj["status"],"liquidation_status":obj["liquidation_status"],
            "liquidation_child_count":counts["liquidation_children"],
            "trade_child_count":counts["trade_children"],
            "okx_mexc_valid_snapshots":metrics,"bybit_frame_counts":counts,
            "manifest_members_verified":3,"independent_pnl_or_forward_labels_read":0,
            "economic_edge_proven":False,"actual_event_futures_settlement_parity_proven":False}
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--original-zip",required=True)
    p.add_argument("--zip-sha256")
    args=p.parse_args();result=audit(args.original_zip,args.zip_sha256)
    dest=pathlib.Path("artifacts/triple_flow_btc10m_independent_replay_v01")
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"independent_raw_replay_receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":main()
