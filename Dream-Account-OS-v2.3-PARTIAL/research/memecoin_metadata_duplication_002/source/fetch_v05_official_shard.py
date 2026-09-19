#!/usr/bin/env python3
"""MSEL-002 V0.5 official Solana deterministic transaction-fetch shard.

SOURCE/PREVALENCE ONLY. ECONOMIC OUTCOMES LOCKED.
"""
from __future__ import annotations
import hashlib, json, os, shutil
from pathlib import Path

import collect_onchain_identity_prevalence_v01 as v1
import collect_onchain_identity_prevalence_v02 as v2  # applies frozen item-level 429 retry patch

PROVIDER = "https://api.mainnet-beta.solana.com"
COUNT = 16
QUAL_RUN = 35438540272
EXPECTED_COUNT = 9564
EXPECTED_SHA256 = "8506bd8a5fb41bdbd866c237ce11f2015bc2813b0f2fc4fe31c3c466e6cb55a1"


def digest(rows):
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: (int(x["slot"]), str(x["signature"]))):
        h.update((str(r["slot"]) + "|" + str(r["block_time"]) + "|" + str(r["signature"]) + "\n").encode())
    return h.hexdigest()


def load_upstream(root: Path):
    q = json.loads((root / "qualification_receipt.json").read_text(encoding="utf-8"))
    if q.get("classification") != "UNIBLOCK_TRANSPORT_QUALIFICATION_TECHNICAL_FAILURE":
        raise RuntimeError(f"unexpected qualification classification {q.get('classification')}")
    if "PROVIDER_HISTORY_START_AFTER_TARGET" not in str(q.get("failure") or ""):
        raise RuntimeError("qualification failure is not the frozen alternate-provider history blocker")

    p = next((x for x in q.get("providers", []) if x.get("provider") == "official-mainnet-beta"), None)
    if not p:
        raise RuntimeError("official-mainnet-beta provider evidence missing")
    if int(p.get("signature_count", -1)) != EXPECTED_COUNT:
        raise RuntimeError("official signature count drift")
    if p.get("signature_set_sha256") != EXPECTED_SHA256:
        raise RuntimeError("official signature digest drift")

    rows = [
        json.loads(x)
        for x in (root / "official-mainnet-beta" / "signatures.jsonl").read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    rows = sorted(rows, key=lambda x: (int(x["slot"]), str(x["signature"])))
    if len(rows) != EXPECTED_COUNT or digest(rows) != EXPECTED_SHA256:
        raise RuntimeError("official signature rows do not match frozen identity")
    safety = q.get("safety") or {}
    if any(bool(safety.get(k)) for k in [
        "prevalence_computed", "transaction_bodies_for_prevalence_fetched",
        "economic_outcomes_opened", "graduation_or_migration_opened",
        "returns_opened", "live_trading", "chain_mutation"
    ]):
        raise RuntimeError("upstream qualification safety firewall violated")
    return rows


def main():
    sid = int(os.environ["MSEL002_SHARD_ID"])
    if not 0 <= sid < COUNT:
        raise RuntimeError("invalid shard id")
    root = Path(os.environ.get("MSEL002_QUALIFICATION_DIR", "downloaded_qualification"))
    rows = load_upstream(root)
    selected = [r for i, r in enumerate(rows) if i % COUNT == sid]

    out = Path(f"v05_official_shard_{sid:02d}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    v1.OUT_DIR = out
    v1.RAW_DIR = out / "raw_rpc"
    rpc = v1.Rpc(PROVIDER)
    creates, missing = v1.fetch_transactions(rpc, selected)
    if missing:
        raise RuntimeError(f"missing transaction results {missing}")

    selected_sha = digest(selected)
    (out / "selected_signatures.jsonl").write_text(
        "".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in selected),
        encoding="utf-8",
    )
    (out / "decoded_creates.jsonl").write_text(
        "".join(
            json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n"
            for x in sorted(creates, key=lambda r: (r["slot"], r["signature"], r["instruction_scope"], r["instruction_index"]))
        ),
        encoding="utf-8",
    )
    (out / "rpc_receipts.json").write_text(json.dumps(rpc.receipts, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "lab_id": "MSEL-002",
        "phase": "V0.5_OFFICIAL_SOLANA_SHARDED_SOURCE_PREVALENCE_TRANSACTION_ACQUISITION",
        "classification": "V05_OFFICIAL_SHARD_PASS",
        "shard_id": sid,
        "shard_count": COUNT,
        "upstream_qualification_run_id": QUAL_RUN,
        "upstream_signature_set_sha256": EXPECTED_SHA256,
        "selected_signature_count": len(selected),
        "selected_signature_sha256": selected_sha,
        "decoded_create_count": len(creates),
        "missing_transaction_results": missing,
        "raw_rpc_file_count": len(list((out / "raw_rpc").glob("*.json"))),
        "provider": PROVIDER,
        "safety": {
            "prevalence_adjudicated": False,
            "economic_outcomes_opened": False,
            "graduation_or_migration_opened": False,
            "returns_opened": False,
            "live_trading": False,
            "chain_mutation": False,
        },
    }
    (out / "shard_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "shard": sid,
        "selected": len(selected),
        "creates": len(creates),
        "missing": missing,
        "economic_outcomes_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
