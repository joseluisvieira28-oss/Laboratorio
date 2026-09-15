from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "token_unlock_event_001"
SRC = ROOT / "source_gate_evidence" / "full_static_latest" / "TUE_FULL_STATIC_IDENTITY_MANIFEST_V01.json"
OUT_DIR = HERE / "source_gate_evidence" / "evm_candidate_scan_v01"
MANIFEST_OUT = OUT_DIR / "UCF_EVM_CANDIDATE_MANIFEST_V01.json"
RECEIPT_OUT = OUT_DIR / "UCF_EVM_CANDIDATE_RECEIPT_V01.json"

EVM_RAW = re.compile(r"^(?P<chain>[^:]+):(?P<address>0x[0-9a-fA-F]{40})$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    raw = SRC.read_bytes()
    src = json.loads(raw)
    events = src["events"]

    out = []
    for e in events:
        token_raw = str(e.get("token_raw") or "")
        m = EVM_RAW.match(token_raw)
        if not m:
            continue
        dt = datetime.fromtimestamp(int(e["timestamp"]), timezone.utc)
        if dt.year not in (2023, 2024):
            raise RuntimeError(f"forbidden year escaped source firewall: {dt.year}")
        if e.get("outcome_data_accessed") is not False:
            raise RuntimeError("source row indicates outcome access")
        row = {
            "symbol": e["symbol"],
            "chain": m.group("chain"),
            "token_address": m.group("address").lower(),
            "token_raw": token_raw,
            "scheduled_at_utc": e["scheduled_at_utc"],
            "timestamp": int(e["timestamp"]),
            "scheduled_unlock_tokens": e["scheduled_unlock_tokens"],
            "sections": e.get("sections", []),
            "file": e.get("file"),
            "adapter_id": e.get("adapter_id"),
            "snapshot": e.get("snapshot"),
            "known_at_utc": e.get("known_at_utc"),
            "known_lead_days": e.get("known_lead_days"),
            "source_repo": e.get("source_repo"),
            "source_commit": e.get("source_commit"),
            "adapter_sha256": e.get("adapter_sha256"),
            "sources": e.get("sources", []),
            "wallet_provenance_status": "UNRESOLVED_PRE_OUTCOME",
            "claim_flow_accessed": False,
            "market_outcome_accessed": False,
        }
        out.append(row)

    out.sort(key=lambda x: (x["timestamp"], x["symbol"], x["token_address"]))
    by_symbol = Counter(x["symbol"] for x in out)
    by_chain = Counter(x["chain"] for x in out)
    years = sorted({datetime.fromtimestamp(x["timestamp"], timezone.utc).year for x in out})
    max_share = max(by_symbol.values()) / len(out) if out else 1.0

    identities = defaultdict(set)
    for x in out:
        identities[x["symbol"]].add((x["chain"], x["token_address"]))
    token_contracts = {}
    token_identity_conflicts = {}
    for symbol, vals in sorted(identities.items()):
        ordered = sorted(vals)
        if len(ordered) == 1:
            chain, address = ordered[0]
            token_contracts[symbol] = {"chain": chain, "address": address}
        else:
            token_identity_conflicts[symbol] = [
                {"chain": chain, "address": address} for chain, address in ordered
            ]

    preliminary_counts_met = (
        len(out) >= 40
        and len(by_symbol) >= 8
        and years == [2023, 2024]
        and max_share <= 0.25
        and not token_identity_conflicts
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha = sha256_bytes(MANIFEST_OUT.read_bytes())

    receipt = {
        "lab_id": "UNLOCK-CLAIM-FLOW-001",
        "mve_id": "UCF-VESTING-OUTFLOW-24H-001",
        "mode": "SOURCE_ONLY_EVM_IDENTITY_CANDIDATE_SCAN",
        "classification": "EVM_IDENTITY_CANDIDATE_SCAN_PASS" if preliminary_counts_met else "SOURCE_DATA_INADEQUATE_PRE_WALLET_GATE",
        "source_manifest_path": str(SRC.relative_to(HERE.parents[2])),
        "source_manifest_sha256": sha256_bytes(raw),
        "candidate_manifest_sha256": manifest_sha,
        "candidate_event_count": len(out),
        "candidate_distinct_tokens": len(by_symbol),
        "candidate_years": years,
        "candidate_chain_counts": dict(sorted(by_chain.items())),
        "candidate_token_event_counts": dict(sorted(by_symbol.items())),
        "token_contracts": token_contracts,
        "token_identity_conflicts": token_identity_conflicts,
        "largest_token_share": max_share,
        "preliminary_count_and_concentration_gates_met": preliminary_counts_met,
        "wallet_provenance_final_count": 0,
        "source_gate_pass": False,
        "next_gate": "WALLET_PROVENANCE_AND_24H_LOG_TRANSPORT",
        "guards": {
            "claim_flow_accessed": False,
            "market_prices_accessed": False,
            "returns_computed": False,
            "pnl_computed": False,
            "year_2025_opened": False,
            "year_2026_opened": False,
            "live_trading": False,
            "exchange_mutation": False,
            "post_outcome_tuning": False,
        },
    }
    RECEIPT_OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
