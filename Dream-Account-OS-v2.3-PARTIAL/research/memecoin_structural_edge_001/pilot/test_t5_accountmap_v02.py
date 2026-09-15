#!/usr/bin/env python3
"""Synthetic no-network guard for MSEL T+5 V0.2 historical account mapping."""

import struct

import collect_t5_forensics_blockscan_free as base
import collect_t5_forensics_blockscan_free_v02 as v02


def run_one(side: str) -> None:
    disc = base.BUY_DISC if side == "buy" else base.SELL_DISC
    raw = disc + struct.pack("<QQ", 123456789, 987654321)
    accounts = [
        "GLOBAL",
        "FEE_RECIPIENT",
        "MINT_X",
        "BONDING_CURVE_X",
        "ASSOCIATED_BONDING_CURVE_X",
        "ASSOCIATED_USER_X",
        "USER_X",
        "SYSTEM_PROGRAM",
        "CREATOR_VAULT",
        "TOKEN_PROGRAM",
        "EVENT_AUTHORITY",
        "PUMP_PROGRAM_ACCOUNT",
    ]

    originals = {
        "outer_and_inner_instructions": base.outer_and_inner_instructions,
        "resolve_program_id": base.resolve_program_id,
        "get_ix_data": base.get_ix_data,
        "b58decode": base.b58decode,
        "resolve_ix_accounts": base.resolve_ix_accounts,
    }
    try:
        base.outer_and_inner_instructions = lambda item: [("outer", 0, {"dummy": True})]
        base.resolve_program_id = lambda ix, keys: base.PUMP_PROGRAM
        base.get_ix_data = lambda ix: "synthetic"
        base.b58decode = lambda data: raw
        base.resolve_ix_accounts = lambda ix, keys: accounts

        rows = list(v02.iter_trade_instructions_v02({}, [], {"MINT_X"}))
        assert len(rows) == 1
        row = rows[0]
        assert row["side"] == side
        assert row["mint"] == "MINT_X"
        assert row["bonding_curve"] == "BONDING_CURVE_X"
        assert row["associated_bonding_curve"] == "ASSOCIATED_BONDING_CURVE_X"
        assert row["associated_user"] == "ASSOCIATED_USER_X"
        assert row["user"] == "USER_X"
        assert row["amount_tokens_raw"] == 123456789
        limit_key = "max_sol_cost_raw" if side == "buy" else "min_sol_output_raw"
        assert row[limit_key] == 987654321
    finally:
        for name, fn in originals.items():
            setattr(base, name, fn)


def main() -> int:
    run_one("buy")
    run_one("sell")
    print("PASS: historical Pump BUY/SELL account map V0.2 synthetic guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
