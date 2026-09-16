#!/usr/bin/env python3
"""PMD-001 V0.7.2 deterministic single-row evidence-reuse runner.

Thin row-level wrapper around the frozen V0.7.1 process_artifact implementation.
No shard has scientific verdict authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_rebuild_helius_v01 import Rpc
from crossdate_evidence_reuse_v071 import process_artifact


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rpc-url", default="https://api.mainnet-beta.solana.com")
    ap.add_argument("--source-name", default="solana_public_rpc_chain_exact_crossdate_v072_reuse")
    ap.add_argument("--block-batch-size", type=int, default=4)
    args = ap.parse_args()

    artifact_dir = Path(args.artifact_dir)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    rpc = Rpc(args.rpc_url, args.source_name)
    rec = dict(process_artifact(rpc, artifact_dir, out, args.block_batch_size))
    rec["stage"] = "CHAIN_EXACT_CROSSDATE_V072_REUSE_ROW"
    rec["scientific_verdict_authority"] = False
    rec["rpc_request_counter"] = rpc.counter
    p = out / "v072_row_receipt.json"
    p.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(rec, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
