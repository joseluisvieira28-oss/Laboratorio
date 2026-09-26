from cctp_v1_message import (
    decode_single_dynamic_bytes_abi,
    parse_cctp_message_v1,
)


def b32(x: int) -> bytes:
    return x.to_bytes(32,"big")


def make_message(amount=1234567, source=0, dest=1, nonce=42):
    sender=b32(0x1111)
    recipient=b32(0x2222)
    dest_caller=b32(0)
    body=(
        (0).to_bytes(4,"big")
        + b32(0x3333)
        + b32(0x4444)
        + b32(amount)
        + b32(0x5555)
    )
    return (
        (0).to_bytes(4,"big")
        + source.to_bytes(4,"big")
        + dest.to_bytes(4,"big")
        + nonce.to_bytes(8,"big")
        + sender + recipient + dest_caller + body
    )


def abi_bytes(payload: bytes) -> str:
    pad=(-len(payload)) % 32
    raw=b32(32)+b32(len(payload))+payload+(b"\x00"*pad)
    return "0x"+raw.hex()


def test_parse_official_layout():
    msg=parse_cctp_message_v1(make_message())
    assert msg.source_domain == 0
    assert msg.destination_domain == 1
    assert msg.nonce == 42
    assert msg.burn.amount_atomic == 1234567


def test_decode_message_sent_dynamic_bytes():
    original=make_message(amount=99)
    decoded=decode_single_dynamic_bytes_abi(abi_bytes(original))
    assert decoded == original
    assert parse_cctp_message_v1(decoded).burn.amount_atomic == 99


def test_wrong_full_message_length_fails_closed():
    try:
        parse_cctp_message_v1(make_message()[:-1])
        raise AssertionError("expected failure")
    except ValueError as e:
        assert "INVALID_CCTP_V1_MESSAGE_LENGTH" in str(e)


def test_wrong_version_fails_closed():
    x=bytearray(make_message())
    x[3]=1
    try:
        parse_cctp_message_v1(bytes(x))
        raise AssertionError("expected failure")
    except ValueError as e:
        assert "UNEXPECTED_MESSAGE_VERSION" in str(e)


def test_wrong_body_version_fails_closed():
    x=bytearray(make_message())
    x[119]=1
    try:
        parse_cctp_message_v1(bytes(x))
        raise AssertionError("expected failure")
    except ValueError as e:
        assert "UNEXPECTED_BURN_BODY_VERSION" in str(e)
