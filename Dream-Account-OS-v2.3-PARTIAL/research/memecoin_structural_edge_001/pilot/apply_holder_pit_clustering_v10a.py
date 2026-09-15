#!/usr/bin/env python3
"""MSEL-001 V10A technical reconciliation wrapper.

PRE-OUTCOME / LOCAL-ONLY / FAIL-CLOSED.

This wrapper preserves V10 scientific logic and changes only V09 final-edge
reconciliation as frozen in V10A_EDGE_RECONCILIATION_CORRECTION_V01.md.

V05 behavior is untouched. For V09 final statuses, multiple instruction-level
matches are accepted only when they are economically equivalent on the frozen
funding tuple; otherwise execution fails closed.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import apply_holder_pit_clustering_v10 as v10

ORIGINAL_MATCH_PRIMARY_EDGE = v10.match_primary_edge
EQUIVALENT_DUPLICATE_GROUPS_CANONICALIZED = 0


def _sort_key(edge: Dict[str, Any]) -> Tuple[str, str]:
    return (str(edge.get("scope") or ""), str(edge.get("instruction_index") or ""))


def match_primary_edge_v10a(
    status: Dict[str, Any],
    edges_by_wallet: Dict[str, List[Dict[str, Any]]],
    final: bool,
) -> Optional[Dict[str, Any]]:
    """Preserve V05 matching; canonicalize only economically-equivalent V09 ties."""
    global EQUIVALENT_DUPLICATE_GROUPS_CANONICALIZED

    if not final:
        return ORIGINAL_MATCH_PRIMARY_EDGE(status, edges_by_wallet, final=False)

    wallet = str(status["wallet"])
    if status.get("final_funding_status") != "DIRECT_FUNDING_EVIDENCE_FOUND_STANDARD_TRANSFER":
        return None

    sig = status.get("final_primary_funding_signature")
    funder = status.get("final_primary_funder")
    lamports = status.get("final_primary_funding_lamports")
    if sig is None or funder is None or lamports is None:
        return None

    matches = [
        e for e in edges_by_wallet.get(wallet, [])
        if e.get("funding_signature") == sig
        and e.get("funder") == funder
        and int(e.get("lamports", -1)) == int(lamports)
        and e.get("instruction_class") == "SYSTEM_TRANSFER"
    ]

    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    econ_keys = {
        (
            str(e.get("wallet")),
            str(e.get("funder")),
            int(e.get("lamports", -1)),
            str(e.get("funding_signature")),
            int(e["funding_block_time"]) if e.get("funding_block_time") is not None else None,
            int(e["funding_slot"]) if e.get("funding_slot") is not None else None,
            str(e.get("instruction_class")),
        )
        for e in matches
    }
    if len(econ_keys) != 1:
        raise RuntimeError(
            f"V10A_V09_DUPLICATE_EDGE_ECONOMIC_CONFLICT wallet={wallet} matches={len(matches)}"
        )

    EQUIVALENT_DUPLICATE_GROUPS_CANONICALIZED += 1
    return sorted(matches, key=_sort_key)[0]


def main() -> int:
    v10.match_primary_edge = match_primary_edge_v10a
    v10.VERSION = "MSEL_HOLDER_PIT_CLUSTERING_V10A"
    rc = v10.main()
    print(f"V10A economically-equivalent duplicate edge groups canonicalized: {EQUIVALENT_DUPLICATE_GROUPS_CANONICALIZED}")
    print("V10A TECHNICAL RECONCILIATION APPLIED; SCIENTIFIC THRESHOLDS UNCHANGED")
    print("OUTCOMES REMAIN LOCKED")
    return rc


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL-CLOSED V10A: {exc}", file=__import__("sys").stderr)
        raise
