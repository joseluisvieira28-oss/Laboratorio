#!/usr/bin/env python3
"""MSEL-001 T+5 forensic collector V0.2 technical correction.

READ-ONLY / RESEARCH-ONLY / OUTCOMES LOCKED.

This wrapper preserves the V0.1 block-scan logic and changes only the historical
2025 Pump BUY/SELL account mapping to match the frozen historical IDL:

  0 global
  1 fee_recipient
  2 mint
  3 bonding_curve
  4 associated_bonding_curve
  5 associated_user
  6 user

V0.1 incorrectly treated index 4 as associated_user and index 5 as user.
No signal, feature horizon, cohort, market outcome, cost, or trading logic is
changed here.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Sequence

import collect_t5_forensics_blockscan_free as base

COLLECTOR_VERSION = "MSEL_T5_FORENSIC_BLOCKSCAN_V02_ACCOUNTMAP"


def iter_trade_instructions_v02(
    item: Dict[str, Any],
    keys: Sequence[str],
    target_mints: set[str],
) -> Iterable[Dict[str, Any]]:
    for scope, ix_idx, ix in base.outer_and_inner_instructions(item):
        if base.resolve_program_id(ix, keys) != base.PUMP_PROGRAM:
            continue
        data = base.get_ix_data(ix)
        if not data:
            continue
        try:
            raw = base.b58decode(data)
        except Exception:
            continue

        if raw.startswith(base.BUY_DISC):
            side = "buy"
        elif raw.startswith(base.SELL_DISC):
            side = "sell"
        else:
            continue

        accounts = base.resolve_ix_accounts(ix, keys)
        if len(accounts) <= 6:
            raise RuntimeError(
                f"TRADE_ACCOUNT_SHAPE_FAILURE_V02 scope={scope} ix={ix_idx} "
                f"accounts={len(accounts)}"
            )

        mint = accounts[2]
        if mint not in target_mints:
            continue

        amount, limit_value = base.parse_u64_pair(raw)
        yield {
            "side": side,
            "scope": scope,
            "instruction_index": ix_idx,
            "mint": mint,
            "bonding_curve": accounts[3],
            "associated_bonding_curve": accounts[4],
            "associated_user": accounts[5],
            "user": accounts[6],
            "amount_tokens_raw": amount,
            "max_sol_cost_raw" if side == "buy" else "min_sol_output_raw": limit_value,
            "instruction_data_sha256": base.sha256_bytes(raw),
            "historical_account_map_version": "PUMP_IDL_2025_ACCOUNT_MAP_V01",
        }


def main() -> int:
    # Technical monkey-patch only: all block scanning, cohort hash checks,
    # snapshot timing, token-balance reconstruction and outcome locks remain
    # exactly in the audited V0.1 collector.
    base.iter_trade_instructions = iter_trade_instructions_v02
    base.COLLECTOR_VERSION = COLLECTOR_VERSION
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
