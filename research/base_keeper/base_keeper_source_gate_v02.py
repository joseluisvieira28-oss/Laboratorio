"""One-shot PublicNode source-only remediation; frozen economics and sample unchanged."""
from . import base_keeper_source_gate_v01 as source

source.RPC = "https://base-rpc.publicnode.com"

if __name__ == "__main__":
    import json
    import os
    from pathlib import Path
    receipt = source.collect()
    receipt["source_revision"] = "SOURCE_REMEDIATION_V0.2_SINGLE_ATTEMPT"
    receipt["endpoint"] = source.RPC
    Path(os.environ.get("BASE_KEEPER_V02_RECEIPT_PATH", "BASE_KEEPER_001_V02_SOURCE_RECEIPT.json")).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
