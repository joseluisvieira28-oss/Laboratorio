#!/usr/bin/env python3
"""MSEL-002 V0.5 canonical aggregate for official Solana sharded source/prevalence acquisition."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path

import collect_onchain_identity_prevalence_v01 as v1

COUNT = 16
QUAL_RUN = 35438540272
EXPECTED_COUNT = 9564
EXPECTED_SHA256 = "8506bd8a5fb41bdbd866c237ce11f2015bc2813b0f2fc4fe31c3c466e6cb55a1"


def digest_sig(rows):
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: (int(x["slot"]), str(x["signature"]))):
        h.update((str(r["slot"]) + "|" + str(r["block_time"]) + "|" + str(r["signature"]) + "\n").encode())
    return h.hexdigest()


def dump(path, obj):
    blob = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def dump_jsonl(path, rows):
    h = hashlib.sha256()
    with path.open("wb") as f:
        for r in rows:
            b = json.dumps(r, sort_keys=True, separators=(",", ":")).encode() + b"\n"
            f.write(b)
            h.update(b)
    return h.hexdigest()


def load_upstream(root: Path):
    q = json.loads((root / "qualification_receipt.json").read_text(encoding="utf-8"))
    if q.get("classification") != "UNIBLOCK_TRANSPORT_QUALIFICATION_TECHNICAL_FAILURE":
        raise RuntimeError("unexpected qualification classification")
    if "PROVIDER_HISTORY_START_AFTER_TARGET" not in str(q.get("failure") or ""):
        raise RuntimeError("unexpected qualification failure reason")
    p = next((x for x in q.get("providers", []) if x.get("provider") == "official-mainnet-beta"), None)
    if not p:
        raise RuntimeError("official provider evidence missing")
    if int(p.get("signature_count", -1)) != EXPECTED_COUNT or p.get("signature_set_sha256") != EXPECTED_SHA256:
        raise RuntimeError("official provider identity mismatch")
    sigs = [
        json.loads(x)
        for x in (root / "official-mainnet-beta" / "signatures.jsonl").read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    sigs = sorted(sigs, key=lambda x: (int(x["slot"]), str(x["signature"])))
    if len(sigs) != EXPECTED_COUNT or digest_sig(sigs) != EXPECTED_SHA256:
        raise RuntimeError("official signature set mismatch")
    return sigs


def main():
    qroot = Path("downloaded_qualification")
    sigs = load_upstream(qroot)

    sroot = Path("downloaded_shards")
    receipts = list(sroot.rglob("shard_receipt.json"))
    if len(receipts) != COUNT:
        raise RuntimeError(f"expected {COUNT} shard receipts got {len(receipts)}")

    seen_ids = set()
    creates = []
    selected_union = []
    for p in receipts:
        r = json.loads(p.read_text(encoding="utf-8"))
        sid = int(r["shard_id"])
        if sid in seen_ids:
            raise RuntimeError("duplicate shard id")
        seen_ids.add(sid)
        if r.get("classification") != "V05_OFFICIAL_SHARD_PASS" or int(r.get("shard_count", -1)) != COUNT:
            raise RuntimeError(f"shard {sid} not pass")
        if r.get("upstream_signature_set_sha256") != EXPECTED_SHA256:
            raise RuntimeError(f"shard {sid} upstream identity mismatch")
        if int(r.get("missing_transaction_results", -1)) != 0:
            raise RuntimeError(f"shard {sid} missing tx")

        expected = [x for i, x in enumerate(sigs) if i % COUNT == sid]
        if int(r["selected_signature_count"]) != len(expected) or r["selected_signature_sha256"] != digest_sig(expected):
            raise RuntimeError(f"shard {sid} deterministic partition mismatch")

        selected_rows = [
            json.loads(x)
            for x in (p.parent / "selected_signatures.jsonl").read_text(encoding="utf-8").splitlines()
            if x.strip()
        ]
        if digest_sig(selected_rows) != digest_sig(expected):
            raise RuntimeError(f"shard {sid} selected rows mismatch")
        selected_union.extend(selected_rows)

        cp = p.parent / "decoded_creates.jsonl"
        creates.extend(json.loads(x) for x in cp.read_text(encoding="utf-8").splitlines() if x.strip())

    if seen_ids != set(range(COUNT)):
        raise RuntimeError("shard id set mismatch")
    selected_union = sorted(selected_union, key=lambda x: (int(x["slot"]), str(x["signature"])))
    if len(selected_union) != EXPECTED_COUNT or digest_sig(selected_union) != EXPECTED_SHA256:
        raise RuntimeError("aggregate signature union mismatch")
    if len({x["signature"] for x in selected_union}) != EXPECTED_COUNT:
        raise RuntimeError("aggregate signature duplicate")

    keys = [(r["signature"], r["instruction_scope"], int(r["instruction_index"]), r["mint"]) for r in creates]
    unique_ok = len(keys) == len(set(keys)) and len({r["mint"] for r in creates}) == len(creates)
    if not unique_ok:
        raise RuntimeError("CREATE_UNIQUENESS_FAILURE")

    w = v1.frozen_window()
    if [int(w["source_start"]), int(w["candidate_start"]), int(w["source_end"])] != [1757101139, 1757122739, 1757144339]:
        raise RuntimeError("frozen window drift")

    candidates, summary = v1.build_features(creates, int(w["candidate_start"]), int(w["source_end"]))
    gates = v1.source_gates(summary, 0, True, True)
    classification = gates["classification"]

    out = Path("v05_official_canonical_output")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    sig_sha = dump_jsonl(out / "authority_signatures_v05.jsonl", selected_union)
    create_sha = dump_jsonl(
        out / "decoded_creates_v05.jsonl",
        sorted(creates, key=lambda r: (r["slot"], r["signature"], r["instruction_scope"], r["instruction_index"])),
    )
    candidate_sha = dump_jsonl(out / "candidate_identity_features_v05.jsonl", candidates)
    summary_sha = dump(out / "source_prevalence_summary_v05.json", summary)
    gates_sha = dump(out / "source_prevalence_gates_v05.json", gates)

    manifest = {
        "artifact": "MSEL_002_ONCHAIN_IMMUTABLE_IDENTITY_SOURCE_PREVALENCE_V05_OFFICIAL_SHARDED",
        "classification": classification,
        "upstream_qualification_run_id": QUAL_RUN,
        "upstream_signature_count": len(sigs),
        "upstream_signature_set_sha256": EXPECTED_SHA256,
        "shard_count": COUNT,
        "decoded_create_count": len(creates),
        "missing_transaction_results": 0,
        "summary": summary,
        "gates": gates,
        "window": w,
        "hashes": {
            "authority_signatures_v05.jsonl": sig_sha,
            "decoded_creates_v05.jsonl": create_sha,
            "candidate_identity_features_v05.jsonl": candidate_sha,
            "source_prevalence_summary_v05.json": summary_sha,
            "source_prevalence_gates_v05.json": gates_sha,
        },
        "safety": {
            "economic_outcomes_opened": False,
            "future_candidate_paths_opened": False,
            "graduation_or_migration_opened": False,
            "returns_opened": False,
            "live_trading": False,
            "chain_mutation": False,
        },
    }
    man_sha = dump(out / "source_prevalence_manifest_v05.json", manifest)
    print(json.dumps({
        "classification": classification,
        **summary,
        "manifest_sha256": man_sha,
        "economic_outcomes_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
