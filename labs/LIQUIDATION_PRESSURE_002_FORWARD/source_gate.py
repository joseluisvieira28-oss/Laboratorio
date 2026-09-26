from __future__ import annotations

import asyncio
import json
import pathlib
import time
from datetime import datetime, timezone

import websockets

LAB_ID = "LIQUIDATION-PRESSURE-002-FORWARD"
URL = "wss://stream.bybit.com/v5/public/linear"
SYMBOLS = ["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","BNBUSDT"]
TOPICS = (
    [f"allLiquidation.{s}" for s in SYMBOLS]
    + [f"orderbook.50.{s}" for s in SYMBOLS]
    + [f"publicTrade.{s}" for s in SYMBOLS]
)
DURATION_SEC = 60
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

def utc_now():
    return datetime.now(timezone.utc).isoformat()

async def main():
    receipt = {
        "lab_id": LAB_ID,
        "phase": "FORWARD_SOURCE_GATE_V0.1",
        "started_at_utc": utc_now(),
        "endpoint": URL,
        "symbols": SYMBOLS,
        "topics_requested": TOPICS,
        "subscription_success_messages": 0,
        "orderbook_messages": 0,
        "trade_messages": 0,
        "liquidation_messages": 0,
        "liquidation_records": 0,
        "raw_messages": 0,
        "errors": [],
        "authenticated_endpoint_used": False,
        "orders_submitted": 0,
        "wallet_mutations": 0,
        "economic_outcomes_opened": False,
        "pnl_computed": False,
    }
    raw_path = OUT / "source_gate_raw_v0_1.jsonl"
    deadline = time.monotonic() + DURATION_SEC

    try:
        async with websockets.connect(
            URL, ping_interval=20, ping_timeout=20, close_timeout=5, max_size=2**23
        ) as ws:
            await ws.send(json.dumps({"op": "subscribe", "args": TOPICS}))
            while time.monotonic() < deadline:
                timeout = max(0.1, min(5.0, deadline - time.monotonic()))
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                except asyncio.TimeoutError:
                    continue

                receipt["raw_messages"] += 1
                obj = json.loads(msg)
                with raw_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"received_at_utc": utc_now(), "message": obj}, sort_keys=True) + "\n")

                if obj.get("success") is True and obj.get("op") == "subscribe":
                    receipt["subscription_success_messages"] += 1

                topic = obj.get("topic", "")
                if topic.startswith("orderbook."):
                    receipt["orderbook_messages"] += 1
                elif topic.startswith("publicTrade."):
                    receipt["trade_messages"] += 1
                elif topic.startswith("allLiquidation."):
                    receipt["liquidation_messages"] += 1
                    data = obj.get("data") or []
                    receipt["liquidation_records"] += len(data) if isinstance(data, list) else 1
    except Exception as e:
        receipt["errors"].append(type(e).__name__ + ":" + str(e)[:500])

    transport_pass = (
        receipt["subscription_success_messages"] >= 1
        and receipt["orderbook_messages"] > 0
        and receipt["trade_messages"] > 0
        and not receipt["errors"]
    )
    receipt["transport_verdict"] = "FORWARD_TRANSPORT_PASS" if transport_pass else "SOURCE_BLOCKED"
    receipt["event_population_verdict"] = (
        "EVENT_POPULATION_OBSERVED"
        if receipt["liquidation_records"] > 0
        else "EVENT_POPULATION_NOT_YET_OBSERVED"
    )
    receipt["ended_at_utc"] = utc_now()

    (OUT / "source_gate_receipt_v0_1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))

    if not transport_pass:
        raise SystemExit(2)

asyncio.run(main())
