#!/usr/bin/env python3
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from urllib.request import Request, urlopen

OUTDIR = os.path.join(os.path.dirname(__file__), "receipts")
os.makedirs(OUTDIR, exist_ok=True)

LAB_ID = "COMPOUND-REALIZED-DISPOSAL-FLOW-001"
COMET = "0xc3d688b66703497daa19211eedff47f25384cdc3"
B0 = 16_308_190
B1 = 21_525_890
EXPECTED_BUY_LOGS = 999
BUY_TOPIC = "0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
RPC = "https://eth.blockscout.com/api/eth-rpc"
PROBE_N = 64

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def fetch_json(url, method="GET", data=None, timeout=120):
    headers = {
        "User-Agent": "CryptoLab-CompoundRealizedFlow-V0.1",
        "Accept": "application/json",
    }
    body = None if data is None else json.dumps(data).encode()
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw.decode()), sha256_bytes(raw)

def rpc(method, params):
    obj, raw_sha = fetch_json(
        RPC,
        method="POST",
        data={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=120,
    )
    if not isinstance(obj, dict) or "error" in obj:
        raise RuntimeError(f"{method} RPC failure: {obj!r}")
    return obj.get("result"), raw_sha

def iv(v):
    if isinstance(v, int):
        return v
    s = str(v or "0")
    return int(s, 16) if s.startswith("0x") else int(s)

def topic_addr(v):
    s = str(v or "").lower()
    return "0x" + s[-40:] if len(s) >= 40 else None

def words(data):
    s = str(data or "")
    if s.startswith("0x"):
        s = s[2:]
    if len(s) % 64:
        raise ValueError("malformed event data")
    return [int(s[i:i+64], 16) for i in range(0, len(s), 64)]

def get_buy_logs():
    out = []
    seen = set()
    pages = []
    cur = B0
    chunk = 2_000_000
    while cur <= B1:
        stop = min(B1, cur + chunk - 1)
        url = (
            "https://eth.blockscout.com/api/?module=logs&action=getLogs"
            f"&fromBlock={cur}&toBlock={stop}&address={COMET}&topic0={BUY_TOPIC}"
        )
        time.sleep(1.1)
        obj, raw_sha = fetch_json(url)
        rows = obj.get("result") if isinstance(obj, dict) else None
        if not isinstance(rows, list):
            raise RuntimeError(f"invalid Blockscout logs response {cur}-{stop}: {obj!r}")
        if len(rows) >= 1000:
            raise RuntimeError(f"possible Blockscout truncation {cur}-{stop}: {len(rows)}")
        pages.append({"from": cur, "to": stop, "count": len(rows), "sha256": raw_sha})
        for x in rows:
            key = (
                str(x.get("blockNumber", "")).lower(),
                str(x.get("transactionHash", "")).lower(),
                str(x.get("logIndex", "")).lower(),
            )
            if key not in seen:
                seen.add(key)
                out.append(x)
        cur = stop + 1
    return out, pages

def decode_buy(lg):
    topics = lg.get("topics") or []
    w = words(lg.get("data"))
    if len(topics) < 3 or len(w) < 2:
        raise ValueError("BuyCollateral log missing indexed topics/data")
    return {
        "block": iv(lg.get("blockNumber")),
        "tx_index": iv(lg.get("transactionIndex")),
        "log_index": iv(lg.get("logIndex")),
        "tx": str(lg.get("transactionHash", "")).lower(),
        "buyer": topic_addr(topics[1]),
        "asset": topic_addr(topics[2]),
        "base_amount_raw": w[0],
        "collateral_amount_raw": w[1],
    }

def decode_transfer(lg):
    topics = lg.get("topics") or []
    if str(lg.get("address", "")).lower() == "" or len(topics) < 3:
        return None
    if str(topics[0]).lower() != TRANSFER_TOPIC:
        return None
    w = words(lg.get("data"))
    if not w:
        return None
    return {
        "token": str(lg.get("address", "")).lower(),
        "from": topic_addr(topics[1]),
        "to": topic_addr(topics[2]),
        "amount_raw": w[0],
        "log_index": iv(lg.get("logIndex")),
    }

def pct(n, d):
    return round(100.0 * n / d, 4) if d else None

receipt = {
    "program": "COMPOUND_REALIZED_DISPOSAL_FLOW_SOURCE_V0.1",
    "lab_id": LAB_ID,
    "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source": {
        "comet": COMET,
        "window_blocks": [B0, B1],
        "window_utc": ["2023-01-01T00:00:00Z", "2024-12-31T23:59:59Z"],
        "blockscout_rpc": RPC,
        "buy_topic": BUY_TOPIC,
        "transfer_topic": TRANSFER_TOPIC,
        "expected_parent_canary_buy_logs": EXPECTED_BUY_LOGS,
    },
    "firewall": {
        "source_only": True,
        "market_prices_opened": False,
        "returns_computed": False,
        "pnl_computed": False,
        "protected_2025_market_outcomes_opened": False,
        "live_trading": False,
        "orders": False,
        "exchange_mutation": False,
        "capital": False,
        "paid_data": False,
        "main_merge": False,
        "post_outcome_tuning": False,
    },
}

try:
    raw_logs, page_hashes = get_buy_logs()
    buys = [decode_buy(x) for x in raw_logs]
    buys.sort(key=lambda x: (x["block"], x["tx_index"], x["log_index"]))

    buyer_counts = Counter(x["buyer"] for x in buys if x["buyer"])
    asset_counts = Counter(x["asset"] for x in buys if x["asset"])
    tx_to_buys = defaultdict(list)
    for x in buys:
        tx_to_buys[x["tx"]].append(x)

    unique_txs = sorted(tx_to_buys)
    selected = sorted(
        unique_txs,
        key=lambda h: hashlib.sha256(h.encode()).hexdigest()
    )[: min(PROBE_N, len(unique_txs))]

    probe_records = []
    usable_txs = 0
    probed_buy_events = sum(len(tx_to_buys[h]) for h in selected)
    recipient_inferred = 0
    onward_transfer_events = 0
    buyer_eq_tx_sender_events = 0
    tx_errors = []

    for tx_hash in selected:
        try:
            time.sleep(0.15)
            tx, tx_sha = rpc("eth_getTransactionByHash", [tx_hash])
            time.sleep(0.15)
            rcpt, rcpt_sha = rpc("eth_getTransactionReceipt", [tx_hash])
            if not isinstance(tx, dict) or not isinstance(rcpt, dict):
                raise RuntimeError("missing transaction or receipt")
            usable_txs += 1
            sender = str(tx.get("from", "")).lower()
            receipt_logs = rcpt.get("logs") or []
            transfers = [z for z in (decode_transfer(lg) for lg in receipt_logs) if z]

            event_records = []
            for b in tx_to_buys[tx_hash]:
                if b["buyer"] == sender:
                    buyer_eq_tx_sender_events += 1

                candidates = [
                    t for t in transfers
                    if t["token"] == b["asset"]
                    and t["from"] == COMET
                    and t["amount_raw"] == b["collateral_amount_raw"]
                    and t["log_index"] < b["log_index"]
                ]
                candidates.sort(key=lambda t: t["log_index"], reverse=True)
                inferred = candidates[0] if candidates else None
                recipient = inferred["to"] if inferred else None
                onward = False
                onward_count = 0
                if recipient:
                    recipient_inferred += 1
                    later = [
                        t for t in transfers
                        if t["token"] == b["asset"]
                        and t["from"] == recipient
                        and t["log_index"] > b["log_index"]
                        and t["amount_raw"] > 0
                    ]
                    onward_count = len(later)
                    onward = onward_count > 0
                    if onward:
                        onward_transfer_events += 1

                event_records.append({
                    "buy_log_index": b["log_index"],
                    "buyer": b["buyer"],
                    "asset": b["asset"],
                    "base_amount_raw": str(b["base_amount_raw"]),
                    "collateral_amount_raw": str(b["collateral_amount_raw"]),
                    "recipient_inferred": recipient,
                    "recipient_transfer_log_index": inferred["log_index"] if inferred else None,
                    "same_tx_onward_transfer": onward,
                    "same_tx_onward_transfer_count": onward_count,
                    "buyer_equals_tx_sender": b["buyer"] == sender,
                })

            probe_records.append({
                "tx": tx_hash,
                "block": iv(rcpt.get("blockNumber")),
                "tx_sender": sender,
                "tx_to": str(tx.get("to", "")).lower() if tx.get("to") else None,
                "receipt_status": iv(rcpt.get("status", "0x0")),
                "tx_rpc_sha256": tx_sha,
                "receipt_rpc_sha256": rcpt_sha,
                "buy_events": event_records,
            })
        except Exception as e:
            tx_errors.append({"tx": tx_hash, "error": repr(e)})

    total_buys = len(buys)
    unique_buyers = len(buyer_counts)
    unique_assets = len(asset_counts)
    selected_n = len(selected)
    usable_pct = (usable_txs / selected_n) if selected_n else 0.0
    recipient_pct = (recipient_inferred / probed_buy_events) if probed_buy_events else 0.0

    if total_buys != EXPECTED_BUY_LOGS:
        status = "SOURCE_CORPUS_DRIFT"
    elif unique_buyers < 1 or unique_assets < 1 or selected_n < 1:
        status = "SOURCE_REALIZED_FLOW_PARTIAL"
    elif usable_pct < 0.95 or recipient_pct < 0.90:
        status = "SOURCE_REALIZED_FLOW_PARTIAL"
    else:
        status = "SOURCE_REALIZED_FLOW_PASS"

    top_buyers = [
        {"buyer": buyer, "buy_logs": n, "share_pct": pct(n, total_buys)}
        for buyer, n in buyer_counts.most_common(15)
    ]

    receipt.update({
        "status": status,
        "source_pages": page_hashes,
        "corpus": {
            "buy_logs": total_buys,
            "unique_transactions": len(unique_txs),
            "unique_buyers": unique_buyers,
            "unique_assets": unique_assets,
            "buyer_concentration_top15": top_buyers,
            "by_asset": dict(sorted(asset_counts.items())),
        },
        "deterministic_receipt_probe": {
            "selection_rule": "ascending SHA256(lowercase tx hash), first 64 unique BuyCollateral transactions",
            "selected_transactions": selected_n,
            "usable_transactions": usable_txs,
            "usable_transactions_pct": pct(usable_txs, selected_n),
            "probed_buy_events": probed_buy_events,
            "recipient_inferred_events": recipient_inferred,
            "recipient_inferred_pct": pct(recipient_inferred, probed_buy_events),
            "buyer_equals_tx_sender_events": buyer_eq_tx_sender_events,
            "buyer_equals_tx_sender_pct": pct(buyer_eq_tx_sender_events, probed_buy_events),
            "same_tx_onward_transfer_events": onward_transfer_events,
            "same_tx_onward_transfer_pct": pct(onward_transfer_events, recipient_inferred),
            "note": "Onward transfer is a routing/flow diagnostic only; it is not automatically a DEX sale and has no source PASS threshold.",
            "records": probe_records,
            "errors": tx_errors,
        },
        "gate": {
            "exact_999_parent_canary": total_buys == EXPECTED_BUY_LOGS,
            "buyer_and_asset_population_present": unique_buyers >= 1 and unique_assets >= 1,
            "receipt_probe_sample_complete": selected_n == min(PROBE_N, len(unique_txs)),
            "receipt_usable_ge_95pct": usable_pct >= 0.95,
            "recipient_inference_ge_90pct": recipient_pct >= 0.90,
            "onward_transfer_is_non_gate_diagnostic": True,
        },
        "interpretation": {
            "edge_claim": False,
            "direction_claim": False,
            "holding_period_selected": False,
            "economic_test_authorized": False,
            "protected_2025_market_test_authorized": False,
        },
    })
except Exception as e:
    receipt.update({
        "status": "TECHNICAL_FAILURE",
        "error": repr(e),
        "interpretation": {
            "edge_claim": False,
            "direction_claim": False,
            "holding_period_selected": False,
            "economic_test_authorized": False,
            "protected_2025_market_test_authorized": False,
        },
    })

pre = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
receipt["receipt_sha256_pre_self_field"] = sha256_bytes(pre)

out = os.path.join(
    OUTDIR,
    "COMPOUND_REALIZED_DISPOSAL_FLOW_001_SOURCE_RECEIPT_V0.1.json"
)
with open(out, "w", encoding="utf-8") as f:
    json.dump(receipt, f, sort_keys=True, indent=2)
    f.write("\n")

print(json.dumps(receipt, sort_keys=True, indent=2))
print(f"receipt={out}")
