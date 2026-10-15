"""V06 Windows EXE: authenticated MEXC account preflight, not a trading switch.

This binary includes the real order transport module but intentionally does
NOT expose a way to send an order yet: missing verified position-stop lifecycle
and live decision scheduler. Use with locally stored DPAPI credentials only.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
import os
import sys
from engine.three_convex_v06.mexc_futures_live_transport import (
    FuturesV06Transport,PrivateKey,MEXCTransportHalt,
)


def inspect(client):
    try:
        positions=client.open_positions()
        orders=client.open_orders()
        stops=client.open_stops()
        mode=client.position_mode()
        assets=client.account_assets()
        fees={sym:client.account_fees(sym) for sym in ("SOL_USDT","BNB_USDT")}
    except (MEXCTransportHalt,ValueError,TypeError) as exc:
        return {"status":"READONLY_PREFLIGHT_BLOCKED_NO_ORDER",
                "class":type(exc).__name__,"trading_authority":"NONE"}
    def shape(v):
        if isinstance(v,list):return len(v)
        if isinstance(v,dict) and isinstance(v.get("resultList"),list):
            return len(v["resultList"])
        return "UNVERIFIED_RESPONSE_SHAPE"
    res={
      "checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "status":"AUTHENTICATED_READS_COMPLETE_NO_LIVE_GO",
      "position_mode_response_type":type(mode).__name__,
      "open_positions_count":shape(positions),
      "open_orders_page_size":shape(orders),
      "open_stops_count":shape(stops),
      "assets_response_type":type(assets).__name__,
      "fee_SOL_response_type":type(fees["SOL_USDT"]).__name__,
      "fee_BNB_response_type":type(fees["BNB_USDT"]).__name__,
      "broker_order_transport_present_in_library":True,
      "broker_order_execution_path_armed":False,
      "account_equity_independently_reconciled":False,
      "position_stop_lifecycle_proven":False,
      "trading_authority":"NONE"}
    return res


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--account-check",action="store_true")
    opts=p.parse_args(argv)
    if not opts.account_check:
        print(json.dumps({"status":"NO_COMMAND_REQUESTED","trading_authority":"NONE"}))
        return 2
    try:
        creds=PrivateKey(os.environ.get("MEXC_API_KEY",""),
                         os.environ.get("MEXC_API_SECRET",""))
        client=FuturesV06Transport(creds)
        report=inspect(client)
        print(json.dumps(report,sort_keys=True,indent=2))
        return 0 if report["status"]=="AUTHENTICATED_READS_COMPLETE_NO_LIVE_GO" else 2
    except Exception as exc:
        print(json.dumps({"status":"NO_ORDER_FAIL_CLOSED",
                          "exception_type":type(exc).__name__,
                          "trading_authority":"NONE"}))
        return 2


if __name__=="__main__":
    sys.exit(main())
