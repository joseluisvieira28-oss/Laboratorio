#!/usr/bin/env python3
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CHAINS = {
    0: {
        "name": "Ethereum",
        "rpc": "https://eth-mainnet.public.blastapi.io",
        "message_transmitter": "0x0a992d191deec32afe36203ad87d7d289a738f81",
        "token_messenger": "0xbd3fa81b58ba92a82136038b25adec7066af3155",
    },
    1: {
        "name": "Avalanche",
        "rpc": "https://api.avax.network/ext/bc/C/rpc",
        "message_transmitter": "0x8186359af5f57fbb40c6b14a588d2a59c0c29880",
        "token_messenger": "0x6b25532e1060ce10cc3b0a99e5683b91bfde6982",
    },
}
TOPIC_MESSAGE_SENT = "0x8c5261668696ce22758910d05bab8f186d6eb247ceac2af2e82c7dc17669b036"
TOPIC_MESSAGE_RECEIVED = "0x58200b4c34ae05ee816d710053fff3fb75af4395915d3d2a771b24aa10e3cc5d"
TOPIC_DEPOSIT_FOR_BURN = "0x2fa9ca894982930190727e75500a97d8dc500233a5065e0f3126c48fbe0343c0"
TOPIC_MINT_AND_WITHDRAW = "0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6"

START_TS = int(datetime(2023, 8, 20, tzinfo=timezone.utc).timestamp())
END_TS = int(datetime(2023, 8, 21, tzinfo=timezone.utc).timestamp()) - 1
OUT = Path("artifacts/cclm_cctp_v1_source_smoke_2023_08_20.json")

def rpc(url, method, params, timeout=45):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"content-type": "application/json", "user-agent": "CryptoLab-CCLM-001/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        response = json.loads(r.read().decode())
    if response.get("error"):
        raise RuntimeError(f"{method}:{response['error']}")
    return response.get("result")

def get_block(url, number):
    return rpc(url, "eth_getBlockByNumber", [hex(number), False])

def block_timestamp(block):
    return int(block["timestamp"], 16)

def find_block_at_or_after(url, target_ts):
    lo = 0
    hi = int(rpc(url, "eth_blockNumber", []), 16)
    while lo < hi:
        mid = (lo + hi) // 2
        b = get_block(url, mid)
        if b is None:
            raise RuntimeError(f"MISSING_BLOCK:{mid}")
        if block_timestamp(b) < target_ts:
            lo = mid + 1
        else:
            hi = mid
    return lo

def get_logs(url, address, topic0, start, end, span=5000):
    rows = []
    cur = start
    while cur <= end:
        hi = min(end, cur + span - 1)
        try:
            batch = rpc(
                url,
                "eth_getLogs",
                [{"fromBlock": hex(cur), "toBlock": hex(hi), "address": address, "topics": [topic0]}],
                timeout=60,
            )
            rows.extend(batch or [])
            cur = hi + 1
        except Exception:
            if span <= 50:
                raise
            return get_logs(url, address, topic0, start, end, max(50, span // 2))
    return rows

def decode_dynamic_bytes(data_hex):
    raw = bytes.fromhex(data_hex[2:] if data_hex.startswith("0x") else data_hex)
    if len(raw) < 64:
        return None
    offset = int.from_bytes(raw[0:32], "big")
    if offset + 32 > len(raw):
        return None
    n = int.from_bytes(raw[offset:offset+32], "big")
    start = offset + 32
    end = start + n
    if end > len(raw):
        return None
    return raw[start:end]

def parse_message(message):
    if message is None or len(message) != 248:
        return None
    body = message[116:]
    if len(body) != 132:
        return None
    return {
        "version": int.from_bytes(message[0:4], "big"),
        "source_domain": int.from_bytes(message[4:8], "big"),
        "destination_domain": int.from_bytes(message[8:12], "big"),
        "nonce": int.from_bytes(message[12:20], "big"),
        "sender": "0x" + message[20:52].hex(),
        "recipient": "0x" + message[52:84].hex(),
        "destination_caller": "0x" + message[84:116].hex(),
        "body_version": int.from_bytes(body[0:4], "big"),
        "burn_token": "0x" + body[4:36].hex(),
        "mint_recipient": "0x" + body[36:68].hex(),
        "amount_atomic": int.from_bytes(body[68:100], "big"),
        "message_sender": "0x" + body[100:132].hex(),
        "body_hex": "0x" + body.hex(),
        "raw_sha256": hashlib.sha256(message).hexdigest(),
    }

def address_as_bytes32_hex(address):\n    return "0x" + ("0" * 24) + address.lower().replace("0x", "")\n\ndef decode_message_received(log):
    topics = log.get("topics") or []
    raw = bytes.fromhex(log.get("data", "0x")[2:])
    if len(topics) < 3 or len(raw) < 128:
        return None
    source_domain = int.from_bytes(raw[0:32], "big")
    sender = "0x" + raw[32:64].hex()
    offset = int.from_bytes(raw[64:96], "big")
    if offset + 32 > len(raw):
        return None
    n = int.from_bytes(raw[offset:offset+32], "big")
    body = raw[offset+32:offset+32+n]
    return {
        "source_domain": source_domain,
        "nonce": int(topics[2], 16),
        "sender": sender,
        "body_hex": "0x" + body.hex(),
        "tx_hash": log["transactionHash"].lower(),
        "block_number": int(log["blockNumber"], 16),
    }

def decode_mint(log):
    topics = log.get("topics") or []
    raw = bytes.fromhex(log.get("data", "0x")[2:])
    if len(topics) < 3 or len(raw) < 32:
        return None
    return {
        "amount_atomic": int.from_bytes(raw[0:32], "big"),
        "mint_recipient": "0x" + topics[1][-40:].lower(),
        "mint_token": "0x" + topics[2][-40:].lower(),
        "tx_hash": log["transactionHash"].lower(),
    }

receipt = {
    "lab_id": "CROSSCHAIN-LIQUIDITY-MIGRATION-001",
    "child_id": "CCLM-CCTP-USDC-001",
    "stage": "CCTP_V1_HISTORICAL_SOURCE_SMOKE",
    "window": {"source_start": "2023-08-20T00:00:00Z", "source_end": "2023-08-20T23:59:59Z", "destination_pair_end": "2023-08-22T23:59:59Z"},
    "market_outcomes_opened": False,
    "pnl_opened": False,
    "mutation": False,
    "chains": {},
    "routes": [],
    "errors": [],
}

try:
    bounds = {}
    for domain, cfg in CHAINS.items():
        start_block = find_block_at_or_after(cfg["rpc"], START_TS)
        end_block = find_block_at_or_after(cfg["rpc"], END_TS + 1) - 1
        bounds[domain] = (start_block, end_block)
        receipt["chains"][str(domain)] = {
            "name": cfg["name"],
            "start_block": start_block,
            "end_block": end_block,
        }

    logs = {}
    for domain, cfg in CHAINS.items():
        start_block, end_block = bounds[domain]
        sent = get_logs(cfg["rpc"], cfg["message_transmitter"], TOPIC_MESSAGE_SENT, start_block, end_block)
        received = get_logs(cfg["rpc"], cfg["message_transmitter"], TOPIC_MESSAGE_RECEIVED, start_block, end_block)
        mints = get_logs(cfg["rpc"], cfg["token_messenger"], TOPIC_MINT_AND_WITHDRAW, start_block, end_block)
        deposits = get_logs(cfg["rpc"], cfg["token_messenger"], TOPIC_DEPOSIT_FOR_BURN, start_block, end_block)
        logs[domain] = {"sent": sent, "received": received, "mints": mints, "deposits": deposits}
        receipt["chains"][str(domain)].update({
            "message_sent_logs": len(sent),
            "message_received_logs": len(received),
            "mint_and_withdraw_logs": len(mints),
            "deposit_for_burn_logs": len(deposits),
        })

    for source_domain, destination_domain in ((0, 1), (1, 0)):
        source_messages = []
        for log in logs[source_domain]["sent"]:
            payload = decode_dynamic_bytes(log.get("data", "0x"))
            parsed = parse_message(payload)
            if not parsed:
                continue
            if parsed["source_domain"] != source_domain or parsed["destination_domain"] != destination_domain:
                continue
            parsed["source_tx"] = log["transactionHash"].lower()
            parsed["source_block"] = int(log["blockNumber"], 16)
            try:
                parsed["message_hash"] = rpc(CHAINS[source_domain]["rpc"], "web3_sha3", ["0x" + payload.hex()])
            except Exception:
                parsed["message_hash"] = None
            source_messages.append(parsed)

        received_index = {}
        for log in logs[destination_domain]["received"]:
            item = decode_message_received(log)
            if item and item["source_domain"] == source_domain:
                received_index.setdefault((source_domain, item["nonce"]), []).append(item)

        mint_index = {}
        for log in logs[destination_domain]["mints"]:
            item = decode_mint(log)
            if item:
                mint_index.setdefault(item["tx_hash"], []).append(item)

        paired = 0
        unpaired = 0
        ambiguous = 0
        mint_or_amount_mismatch = 0
        samples = []

        for item in source_messages:
            candidates = []
            for dest in received_index.get((source_domain, item["nonce"]), []):
                if dest["sender"].lower() != item["sender"].lower():
                    continue
                if dest["body_hex"].lower() != item["body_hex"].lower():
                    continue
                candidates.append(dest)

            if len(candidates) == 0:
                unpaired += 1
                continue
            if len(candidates) != 1:
                ambiguous += 1
                continue

            dest = candidates[0]
            mints = [m for m in mint_index.get(dest["tx_hash"], []) if m["amount_atomic"] == item["amount_atomic"]]
            if len(mints) != 1:
                mint_or_amount_mismatch += 1
                continue

            paired += 1
            if len(samples) < 5:
                samples.append({
                    "nonce": item["nonce"],
                    "amount_atomic": item["amount_atomic"],
                    "source_tx": item["source_tx"],
                    "destination_tx": dest["tx_hash"],
                    "message_hash": item["message_hash"],
                })

        receipt["routes"].append({
            "source_domain": source_domain,
            "destination_domain": destination_domain,
            "source_messages": len(source_messages),
            "paired": paired,
            "unpaired": unpaired,
            "ambiguous": ambiguous,
            "mint_or_amount_mismatch": mint_or_amount_mismatch,
            "samples": samples,
        })

    total_source = sum(x["source_messages"] for x in receipt["routes"])
    total_paired = sum(x["paired"] for x in receipt["routes"])
    receipt["pair_rate"] = (total_paired / total_source) if total_source else None
    if total_source == 0:
        receipt["classification"] = "SOURCE_SMOKE_NO_EVENTS"
    elif total_paired == total_source:
        receipt["classification"] = "SOURCE_SMOKE_PASS"
    else:
        receipt["classification"] = "SOURCE_SMOKE_PARTIAL"

except Exception as exc:
    receipt["classification"] = "SOURCE_SMOKE_TECHNICAL_FAILURE"
    receipt["errors"].append(f"{type(exc).__name__}:{str(exc)[:500]}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "classification": receipt.get("classification"),
    "pair_rate": receipt.get("pair_rate"),
    "routes": receipt.get("routes"),
    "errors": receipt.get("errors"),
}, indent=2))
