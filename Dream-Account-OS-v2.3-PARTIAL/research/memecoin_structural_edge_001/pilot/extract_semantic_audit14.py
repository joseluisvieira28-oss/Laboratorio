#!/usr/bin/env python3
"""Build one compact MSEL-001 semantic-audit bundle for the 14 flagged T+5 transactions.

READ-ONLY / OUTCOMES LOCKED.

Identifies:
  A) buy-only Pump transactions with no target-mint token-balance change recorded;
  B) non-Pump target-mint token-balance-change transactions.

Then fetches each exact transaction with standard Solana getTransaction and writes
one JSON file suitable for manual forensic review.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List, Tuple

EXPECTED_A = 11
EXPECTED_B = 3
EXPECTED_TOTAL = 14


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def load_jsonl(path: pathlib.Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def rpc_url() -> str:
    explicit = os.environ.get("MSEL_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing HELIUS_API_KEY (or MSEL_RPC_URL).")
    return f"https://mainnet.helius-rpc.com/?api-key={key}"


def rpc_get_transaction(url: str, signature: str, request_id: int) -> Dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "getTransaction",
        "params": [
            signature,
            {
                "encoding": "json",
                "commitment": "finalized",
                "maxSupportedTransactionVersion": 0,
            },
        ],
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    decoded = json.loads(raw.decode("utf-8"))
    if decoded.get("error"):
        raise RuntimeError(f"RPC getTransaction failed for {signature}: {decoded['error']}")
    if decoded.get("result") is None:
        raise RuntimeError(f"RPC getTransaction returned null for {signature}")
    return {
        "request_sha256": sha256_bytes(body),
        "response_sha256": sha256_bytes(raw),
        "response": decoded,
    }


def tx_key(row: Dict[str, Any]) -> Tuple[int, int, str, str]:
    return (
        int(row["slot"]),
        int(row["transaction_index"]),
        str(row["signature"]),
        str(row["mint"]),
    )


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    base = here / "data" / "msel001_t5_forensics"
    trades_path = base / "trade_events.jsonl"
    changes_path = base / "token_balance_changes.jsonl"
    out_path = base / "audit14_raw_transactions.json"

    if not trades_path.exists() or not changes_path.exists():
        raise RuntimeError("Required T+5 source files are missing.")

    trades = load_jsonl(trades_path)
    changes = load_jsonl(changes_path)

    trades_by_key: Dict[Tuple[int, int, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in trades:
        trades_by_key[tx_key(row)].append(row)

    change_keys = {tx_key(row) for row in changes}

    flagged_a: List[Dict[str, Any]] = []
    for key, rows in sorted(trades_by_key.items()):
        sides = {str(r.get("side")) for r in rows}
        if sides == {"buy"} and key not in change_keys:
            slot, tx_index, sig, mint = key
            flagged_a.append({
                "reason": "BUY_ONLY_NO_TARGET_MINT_BALANCE_CHANGE",
                "slot": slot,
                "transaction_index": tx_index,
                "signature": sig,
                "mint": mint,
                "pump_instruction_count": len(rows),
                "pump_sides": sorted(sides),
            })

    flagged_b_by_key: Dict[Tuple[int, int, str, str], Dict[str, Any]] = {}
    for row in changes:
        if bool(row.get("pump_trade_for_mint")):
            continue
        key = tx_key(row)
        slot, tx_index, sig, mint = key
        item = flagged_b_by_key.setdefault(key, {
            "reason": "NON_PUMP_TARGET_MINT_BALANCE_CHANGE",
            "slot": slot,
            "transaction_index": tx_index,
            "signature": sig,
            "mint": mint,
            "balance_changes": [],
        })
        item["balance_changes"].append({
            "token_account": row.get("token_account"),
            "owner": row.get("owner"),
            "pre_amount_raw": row.get("pre_amount_raw"),
            "post_amount_raw": row.get("post_amount_raw"),
            "delta_raw": row.get("delta_raw"),
        })
    flagged_b = [flagged_b_by_key[k] for k in sorted(flagged_b_by_key)]

    if len(flagged_a) != EXPECTED_A:
        raise RuntimeError(f"FLAGGED_A_COUNT_CHANGED expected={EXPECTED_A} actual={len(flagged_a)}")
    if len(flagged_b) != EXPECTED_B:
        raise RuntimeError(f"FLAGGED_B_COUNT_CHANGED expected={EXPECTED_B} actual={len(flagged_b)}")

    targets = flagged_a + flagged_b
    unique_sigs = {x["signature"] for x in targets}
    if len(targets) != EXPECTED_TOTAL or len(unique_sigs) != EXPECTED_TOTAL:
        raise RuntimeError(
            f"FLAGGED_TOTAL_CHANGED rows={len(targets)} unique_signatures={len(unique_sigs)}"
        )

    url = rpc_url()
    enriched = []
    for i, target in enumerate(targets, start=1):
        fetched = rpc_get_transaction(url, target["signature"], i)
        enriched.append({**target, **fetched})
        print(f"fetched {i}/{EXPECTED_TOTAL}: {target['signature']}")

    bundle = {
        "lab": "MSEL-001",
        "artifact": "SEMANTIC_AUDIT14_RAW_TRANSACTIONS_V01",
        "outcomes_opened": False,
        "source_files": {
            "trade_events_sha256": sha256_bytes(trades_path.read_bytes()),
            "token_balance_changes_sha256": sha256_bytes(changes_path.read_bytes()),
        },
        "counts": {
            "buy_only_no_balance_change": len(flagged_a),
            "non_pump_balance_change": len(flagged_b),
            "total": len(enriched),
        },
        "transactions": enriched,
    }
    payload = (json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    out_path.write_bytes(payload)

    print("PASS: semantic audit bundle created")
    print(f"file: {out_path}")
    print(f"sha256: {sha256_bytes(payload)}")
    print("OUTCOMES REMAIN LOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        raise
