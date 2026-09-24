"""CCTP paired-flow schema for source-gate validation only."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class CctpLeg:
    side: str  # BURN or MINT
    message_hash: str
    source_chain: str
    destination_chain: str
    tx_hash: str
    block_number: int
    block_ts_ms: int
    amount_atomic: int
    protocol_version: str = "UNKNOWN"
    transfer_mode: str = "UNKNOWN"


@dataclass(frozen=True)
class CctpTransfer:
    message_hash: str
    source_chain: str
    destination_chain: str
    amount_atomic: int
    burn_tx_hash: str
    burn_block_number: int
    burn_block_ts_ms: int
    mint_tx_hash: str
    mint_block_number: int
    mint_block_ts_ms: int
    protocol_version: str
    transfer_mode: str


def pair_legs(legs: Iterable[CctpLeg]) -> tuple[list[CctpTransfer], list[str]]:
    by_hash: dict[str, dict[str, CctpLeg]] = {}
    errors: list[str] = []

    for leg in legs:
        side = leg.side.upper()
        if side not in {"BURN", "MINT"}:
            errors.append(f"INVALID_SIDE:{leg.message_hash}:{leg.side}")
            continue
        slot = by_hash.setdefault(leg.message_hash.lower(), {})
        if side in slot:
            errors.append(f"DUPLICATE_{side}:{leg.message_hash}")
            continue
        slot[side] = leg

    paired: list[CctpTransfer] = []
    for key, slot in sorted(by_hash.items()):
        if set(slot) != {"BURN", "MINT"}:
            errors.append(f"UNPAIRED:{key}")
            continue
        burn, mint = slot["BURN"], slot["MINT"]
        if burn.amount_atomic != mint.amount_atomic:
            errors.append(f"AMOUNT_MISMATCH:{key}")
            continue
        if (
            burn.source_chain != mint.source_chain
            or burn.destination_chain != mint.destination_chain
        ):
            errors.append(f"ROUTE_MISMATCH:{key}")
            continue

        versions = {burn.protocol_version, mint.protocol_version} - {"UNKNOWN"}
        modes = {burn.transfer_mode, mint.transfer_mode} - {"UNKNOWN"}
        if len(versions) > 1:
            errors.append(f"VERSION_MISMATCH:{key}")
            continue
        if len(modes) > 1:
            errors.append(f"MODE_MISMATCH:{key}")
            continue

        paired.append(
            CctpTransfer(
                message_hash=key,
                source_chain=burn.source_chain,
                destination_chain=burn.destination_chain,
                amount_atomic=burn.amount_atomic,
                burn_tx_hash=burn.tx_hash,
                burn_block_number=burn.block_number,
                burn_block_ts_ms=burn.block_ts_ms,
                mint_tx_hash=mint.tx_hash,
                mint_block_number=mint.block_number,
                mint_block_ts_ms=mint.block_ts_ms,
                protocol_version=next(iter(versions), "UNKNOWN"),
                transfer_mode=next(iter(modes), "UNKNOWN"),
            )
        )
    return paired, errors
