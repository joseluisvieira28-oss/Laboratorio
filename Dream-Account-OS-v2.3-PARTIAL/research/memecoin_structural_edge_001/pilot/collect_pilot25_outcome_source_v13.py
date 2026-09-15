#!/usr/bin/env python3
"""MSEL-001 Pilot25 outcome source acquisition V13.

READ-ONLY / RESEARCH-ONLY / OUTCOME-SOURCE OPENING AUTHORIZED BY V12.

This stage acquires and seals raw future transaction bytes WITHOUT computing
returns, catastrophe labels, winner labels, slice statistics, or verdicts.

Primary route (frozen before outcome access):
- for each of the 25 frozen mint addresses, use standard Solana
  getSignaturesForAddress with the frozen CREATE signature as `until`;
- page newest->launch until the server proves the history segment exhausted;
- retain only signatures whose blockTime is in (T+5, T+5+24h];
- fetch each retained transaction with getTransaction;
- preserve exact JSON-RPC response bytes + SHA-256 receipts.

Why mint-address indexing is sufficient for source discovery:
Pump BUY/SELL and PumpSwap BUY/SELL both require the target mint as a transaction
account. Migration/create-pool transactions also require the mint. The V14
evaluator, not this collector, decides which captured transactions are valid
Pump/PumpSwap economic SELL evidence under the historical schema.

Frozen technical safety policy:
- max 250 signature pages per mint (250,000 signatures newer than CREATE);
- if any mint cannot reach the launch boundary within that cap, this script
  FAILS CLOSED with ADDRESS_HISTORY_CAP_REACHED and the predeclared fallback is
  a canonical time-bounded block/accounts scan. The cap must NOT be increased
  after seeing any outcome bytes.
- no label or return may be computed by this script.

Environment:
  HELIUS_API_KEY        required unless MSEL_RPC_URL is set
  MSEL_RPC_URL          optional archival Solana RPC URL
  MSEL_RPS_DELAY        optional delay after each RPC call, default 0.12s
  MSEL_V13_MAX_PAGES    optional, MUST equal frozen 250
  MSEL_V13_MAX_TX       optional, default 200000 safety ceiling
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Tuple

EXPECTED_COHORT_SHA = "7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
EXPECTED_V11_MANIFEST_SHA = "ceec26d445a91c3a89721cd5ef3e7b774bbff5a620659c91486202e99134bae8"
EXPECTED_PREFLIGHT_SHA = "9765330662b9003eca790a51f201b4f05c7d1f9bfa66daef83d1d3c2007c781b"
FROZEN_MAX_PAGES_PER_MINT = 250
FUTURE_SECONDS = 86400
DECISION_SECONDS = 300
VERSION = "MSEL_PILOT25_OUTCOME_SOURCE_V13"


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: pathlib.Path) -> str:
    return sha_bytes(p.read_bytes())


def load_json(p: pathlib.Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def load_jsonl(p: pathlib.Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def write_json(p: pathlib.Path, obj: Any) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha_file(p)


def write_jsonl(p: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return sha_file(p)


def rpc_url() -> str:
    explicit = os.environ.get("MSEL_RPC_URL", "").strip()
    if explicit:
        return explicit
    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing HELIUS_API_KEY (or MSEL_RPC_URL).")
    return f"https://mainnet.helius-rpc.com/?api-key={key}"


class Rpc:
    def __init__(self, url: str, delay: float):
        self.url = url
        self.delay = delay
        self.request_id = 0
        self.calls = 0

    def raw_call(self, method: str, params: list, retries: int = 7) -> Tuple[bytes, Any]:
        self.request_id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}, separators=(",", ":")).encode()
        backoff = 1.0
        last: Optional[Exception] = None
        for attempt in range(retries):
            req = urllib.request.Request(self.url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read()
                obj = json.loads(raw)
                if isinstance(obj, dict) and obj.get("error"):
                    code = (obj.get("error") or {}).get("code")
                    if code in (-32005, -32603) and attempt + 1 < retries:
                        time.sleep(backoff); backoff = min(backoff * 2, 20); continue
                    raise RuntimeError(f"RPC_ERROR method={method} error={obj['error']}")
                self.calls += 1
                if self.delay > 0:
                    time.sleep(self.delay)
                return raw, obj.get("result") if isinstance(obj, dict) else None
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last = exc
                status = getattr(exc, "code", None)
                if attempt + 1 >= retries or (status is not None and status not in (429, 500, 502, 503, 504)):
                    raise
                time.sleep(backoff); backoff = min(backoff * 2, 20)
        raise RuntimeError(f"RPC_RETRY_EXHAUSTED method={method} last={last}")


def save_raw(path: pathlib.Path, raw: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_bytes()
        if existing != raw:
            raise RuntimeError(f"RAW_REPLAY_MISMATCH {path}")
        return sha_bytes(existing)
    path.write_bytes(raw)
    return sha_bytes(raw)


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    cohort_p = here / "data" / "msel001_pilot25_blockscan" / "cohort_25.jsonl"
    v11_dir = here / "data" / "msel001_pilot25_feature_v11"
    v11_manifest_p = v11_dir / "pilot25_feature_manifest_v11.json"
    preflight_p = v11_dir / "pilot25_outcome_preflight_v12.json"
    out = here / "data" / "msel001_pilot25_outcome_source_v13"
    raw_pages = out / "raw_signature_pages"
    raw_txs = out / "raw_transactions"
    manifest_p = out / "outcome_source_manifest_v13.json"

    for p in (cohort_p, v11_manifest_p, preflight_p):
        if not p.exists():
            raise RuntimeError(f"MISSING_REQUIRED_INPUT {p}")
    if manifest_p.exists():
        raise RuntimeError("V13_MANIFEST_ALREADY_EXISTS; preserve prior run and do not overwrite")
    if sha_file(cohort_p) != EXPECTED_COHORT_SHA:
        raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha_file(v11_manifest_p) != EXPECTED_V11_MANIFEST_SHA:
        raise RuntimeError("V11_MANIFEST_HASH_MISMATCH")
    if sha_file(preflight_p) != EXPECTED_PREFLIGHT_SHA:
        raise RuntimeError("V12_PREFLIGHT_HASH_MISMATCH")
    v11 = load_json(v11_manifest_p)
    pf = load_json(preflight_p)
    if v11.get("outcomes_opened") is not False or pf.get("outcomes_opened") is not False:
        raise RuntimeError("PRE_SOURCE_OUTCOME_LOCK_FAILURE")
    if pf.get("primary_future_side") != "SELL_ONLY" or pf.get("future_windows_seconds") != [900, 3600, 21600, 86400]:
        raise RuntimeError("PREFLIGHT_POLICY_MISMATCH")

    max_pages = int(os.environ.get("MSEL_V13_MAX_PAGES", str(FROZEN_MAX_PAGES_PER_MINT)))
    if max_pages != FROZEN_MAX_PAGES_PER_MINT:
        raise RuntimeError(f"FROZEN_PAGE_CAP_MISMATCH expected={FROZEN_MAX_PAGES_PER_MINT} actual={max_pages}")
    max_tx = int(os.environ.get("MSEL_V13_MAX_TX", "200000"))
    delay = float(os.environ.get("MSEL_RPS_DELAY", "0.12"))
    if max_tx <= 0 or delay < 0:
        raise RuntimeError("INVALID_SAFETY_CONFIGURATION")

    cohort = load_jsonl(cohort_p)
    if len(cohort) != 25 or len({r["mint"] for r in cohort}) != 25:
        raise RuntimeError("COHORT_SHAPE_FAILURE")
    rpc = Rpc(rpc_url(), delay)
    raw_pages.mkdir(parents=True, exist_ok=True)
    raw_txs.mkdir(parents=True, exist_ok=True)

    receipt_rows: List[Dict[str, Any]] = []
    sig_rows_by_sig: Dict[str, Dict[str, Any]] = {}
    coverage_rows: List[Dict[str, Any]] = []

    # Phase A: exhaust each mint's address history back to frozen CREATE.
    for launch in sorted(cohort, key=lambda r: int(r["cohort_rank"])):
        mint = str(launch["mint"])
        create_sig = str(launch["signature"])
        decision = int(launch["block_time"]) + DECISION_SECONDS
        end = decision + FUTURE_SECONDS
        before: Optional[str] = None
        complete = False
        page_count = 0
        total_rows = 0
        window_rows = 0

        while page_count < max_pages:
            cfg: Dict[str, Any] = {"limit": 1000, "commitment": "finalized", "until": create_sig}
            if before:
                cfg["before"] = before
            raw, result = rpc.raw_call("getSignaturesForAddress", [mint, cfg])
            page_count += 1
            fname = f"r{int(launch['cohort_rank']):02d}_p{page_count:03d}.json"
            rh = save_raw(raw_pages / fname, raw)
            rows = result or []
            if not isinstance(rows, list):
                raise RuntimeError(f"SIGNATURE_PAGE_SHAPE_FAILURE rank={launch['cohort_rank']} page={page_count}")
            receipt_rows.append({"method": "getSignaturesForAddress", "cohort_rank": int(launch["cohort_rank"]), "mint": mint,
                                 "page": page_count, "raw_file": fname, "response_sha256": rh, "row_count": len(rows)})
            total_rows += len(rows)
            for sr in rows:
                sig = sr.get("signature")
                bt = sr.get("blockTime")
                if not sig or bt is None:
                    continue
                bt = int(bt)
                if decision < bt <= end:
                    window_rows += 1
                    prev = sig_rows_by_sig.get(sig)
                    entry = {"signature": sig, "block_time": bt, "slot": int(sr.get("slot")) if sr.get("slot") is not None else None,
                             "err": sr.get("err"), "target_mints": [mint], "cohort_ranks": [int(launch["cohort_rank"])],
                             "source": "getSignaturesForAddress"}
                    if prev is None:
                        sig_rows_by_sig[sig] = entry
                    else:
                        if mint not in prev["target_mints"]:
                            prev["target_mints"].append(mint); prev["cohort_ranks"].append(int(launch["cohort_rank"]))
                        if int(prev["block_time"]) != bt:
                            raise RuntimeError(f"SIGNATURE_BLOCKTIME_CONFLICT {sig}")
            if not rows or len(rows) < 1000:
                complete = True
                break
            last_sig = rows[-1].get("signature")
            if not last_sig or last_sig == before:
                raise RuntimeError(f"SIGNATURE_PAGINATION_STALL rank={launch['cohort_rank']} page={page_count}")
            before = str(last_sig)

        coverage_rows.append({"cohort_rank": int(launch["cohort_rank"]), "mint": mint, "decision_time": decision,
                              "end_time_24h": end, "pages": page_count, "signature_rows_newer_than_create": total_rows,
                              "signatures_in_future_window": window_rows, "launch_boundary_exhausted": complete})
        if not complete:
            # Do not inspect/print per-token outcome direction. Stop only on source completeness.
            raise RuntimeError(f"ADDRESS_HISTORY_CAP_REACHED cohort_rank={launch['cohort_rank']} pages={page_count}; BLOCKSCAN_FALLBACK_REQUIRED")

    if len(sig_rows_by_sig) > max_tx:
        raise RuntimeError(f"V13_TRANSACTION_SAFETY_CAP_REACHED count={len(sig_rows_by_sig)} cap={max_tx}")

    # Phase B: fetch exact full transactions for every signature inside any target 24h window.
    for i, sig in enumerate(sorted(sig_rows_by_sig), 1):
        raw, result = rpc.raw_call("getTransaction", [sig, {"encoding": "json", "commitment": "finalized", "maxSupportedTransactionVersion": 0}])
        fname = f"tx_{i:06d}_{sig[:12]}.json"
        rh = save_raw(raw_txs / fname, raw)
        receipt_rows.append({"method": "getTransaction", "signature": sig, "raw_file": fname, "response_sha256": rh,
                             "result_present": result is not None})
        sig_rows_by_sig[sig]["raw_transaction_file"] = fname
        sig_rows_by_sig[sig]["raw_transaction_sha256"] = rh
        sig_rows_by_sig[sig]["transaction_result_present"] = result is not None

    coverage_rows.sort(key=lambda r: r["cohort_rank"])
    sig_rows = sorted(sig_rows_by_sig.values(), key=lambda r: (int(r["block_time"]), r.get("slot") or -1, r["signature"]))
    for r in sig_rows:
        r["target_mints"] = sorted(r["target_mints"])
        r["cohort_ranks"] = sorted(r["cohort_ranks"])

    coverage_p = out / "mint_source_coverage_v13.jsonl"
    sig_index_p = out / "future_signature_index_v13.jsonl"
    receipts_p = out / "rpc_receipts_v13.jsonl"
    coverage_sha = write_jsonl(coverage_p, coverage_rows)
    sig_sha = write_jsonl(sig_index_p, sig_rows)
    receipts_sha = write_jsonl(receipts_p, receipt_rows)

    manifest = {
        "artifact": VERSION,
        "pilot_only": True,
        "full_mve_verdict_authorized": False,
        "source_cohort_sha256": EXPECTED_COHORT_SHA,
        "source_v11_manifest_sha256": EXPECTED_V11_MANIFEST_SHA,
        "source_v12_preflight_sha256": EXPECTED_PREFLIGHT_SHA,
        "discovery_route": "getSignaturesForAddress(target_mint, until=frozen_create_signature)",
        "frozen_max_signature_pages_per_mint": FROZEN_MAX_PAGES_PER_MINT,
        "decision_horizon_seconds": DECISION_SECONDS,
        "future_source_horizon_seconds": FUTURE_SECONDS,
        "all_25_mint_histories_exhausted_to_create_boundary": all(r["launch_boundary_exhausted"] for r in coverage_rows),
        "coverage_rows": 25,
        "unique_future_signatures": len(sig_rows),
        "raw_signature_page_count": sum(r["pages"] for r in coverage_rows),
        "raw_transaction_count": len(sig_rows),
        "rpc_calls": rpc.calls,
        "mint_source_coverage_sha256": coverage_sha,
        "future_signature_index_sha256": sig_sha,
        "rpc_receipts_sha256": receipts_sha,
        "outcome_source_bytes_acquired": True,
        "returns_computed": False,
        "labels_computed": False,
        "slice_statistics_computed": False,
        "verdict_computed": False,
        "live_trading": False,
        "exchange_mutation": False,
    }
    msha = write_json(manifest_p, manifest)

    print("PASS: Pilot25 future source acquisition V13 complete")
    print("mint histories complete: 25/25")
    print(f"signature pages: {manifest['raw_signature_page_count']}")
    print(f"unique future signatures sealed: {len(sig_rows)}")
    print(f"full transactions sealed: {len(sig_rows)}")
    print(f"rpc calls: {rpc.calls}")
    print(f"manifest sha256: {msha}")
    print("OUTCOME SOURCE BYTES ARE NOW OPEN/SEALED")
    print("NO RETURNS OR LABELS COMPUTED")
    print("V11 RISK ORDER REMAINS FROZEN")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED: {exc}", file=__import__("sys").stderr)
        raise
