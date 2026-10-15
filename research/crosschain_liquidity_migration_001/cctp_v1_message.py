"""Circle CCTP V1 raw-message parser.

Implements only the byte layout frozen from Circle's official V1 contracts.
No chain access, prices or market outcomes.
"""
from __future__ import annotations
from dataclasses import dataclass


def _u(b: bytes) -> int:
    return int.from_bytes(b, "big", signed=False)


def _hex(b: bytes) -> str:
    return "0x" + b.hex()


@dataclass(frozen=True)
class BurnMessageV1:
    version: int
    burn_token: str
    mint_recipient: str
    amount_atomic: int
    message_sender: str


@dataclass(frozen=True)
class CctpMessageV1:
    version: int
    source_domain: int
    destination_domain: int
    nonce: int
    sender: str
    recipient: str
    destination_caller: str
    burn: BurnMessageV1


def parse_burn_message_v1(body: bytes) -> BurnMessageV1:
    if len(body) != 132:
        raise ValueError(f"INVALID_BURN_MESSAGE_LENGTH:{len(body)}")
    return BurnMessageV1(
        version=_u(body[0:4]),
        burn_token=_hex(body[4:36]),
        mint_recipient=_hex(body[36:68]),
        amount_atomic=_u(body[68:100]),
        message_sender=_hex(body[100:132]),
    )


def parse_cctp_message_v1(message: bytes) -> CctpMessageV1:
    if len(message) != 248:
        raise ValueError(f"INVALID_CCTP_V1_MESSAGE_LENGTH:{len(message)}")
    burn=parse_burn_message_v1(message[116:])
    out=CctpMessageV1(
        version=_u(message[0:4]),
        source_domain=_u(message[4:8]),
        destination_domain=_u(message[8:12]),
        nonce=_u(message[12:20]),
        sender=_hex(message[20:52]),
        recipient=_hex(message[52:84]),
        destination_caller=_hex(message[84:116]),
        burn=burn,
    )
    if out.version != 0:
        raise ValueError(f"UNEXPECTED_MESSAGE_VERSION:{out.version}")
    if burn.version != 0:
        raise ValueError(f"UNEXPECTED_BURN_BODY_VERSION:{burn.version}")
    return out


def decode_single_dynamic_bytes_abi(data_hex: str) -> bytes:
    """Decode ABI data for an event with a single non-indexed bytes argument."""
    raw=bytes.fromhex(data_hex[2:] if data_hex.startswith("0x") else data_hex)
    if len(raw) < 64 or len(raw) % 32:
        raise ValueError("INVALID_ABI_DYNAMIC_BYTES_DATA")
    offset=_u(raw[0:32])
    if offset + 32 > len(raw):
        raise ValueError("INVALID_ABI_OFFSET")
    n=_u(raw[offset:offset+32])
    start=offset+32
    end=start+n
    if end > len(raw):
        raise ValueError("INVALID_ABI_LENGTH")
    return raw[start:end]
