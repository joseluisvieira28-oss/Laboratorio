from cctp_schema import CctpLeg, pair_legs


def leg(side, *, amount=1_000_000, route=("Ethereum", "Base"), msg="0xabc", version="V2", mode="STANDARD"):
    return CctpLeg(
        side=side,
        message_hash=msg,
        source_chain=route[0],
        destination_chain=route[1],
        tx_hash="0x" + side.lower(),
        block_number=1 if side == "BURN" else 2,
        block_ts_ms=1000 if side == "BURN" else 2000,
        amount_atomic=amount,
        protocol_version=version,
        transfer_mode=mode,
    )


def test_pair_valid_burn_and_mint():
    paired, errors = pair_legs([leg("BURN"), leg("MINT")])
    assert errors == []
    assert len(paired) == 1
    assert paired[0].amount_atomic == 1_000_000


def test_unpaired_fails_closed():
    paired, errors = pair_legs([leg("BURN")])
    assert paired == []
    assert errors == ["UNPAIRED:0xabc"]


def test_amount_mismatch_fails_closed():
    paired, errors = pair_legs([leg("BURN"), leg("MINT", amount=2_000_000)])
    assert paired == []
    assert errors == ["AMOUNT_MISMATCH:0xabc"]


def test_version_mismatch_fails_closed():
    paired, errors = pair_legs([leg("BURN", version="V1"), leg("MINT", version="V2")])
    assert paired == []
    assert errors == ["VERSION_MISMATCH:0xabc"]


def test_mode_mismatch_fails_closed():
    paired, errors = pair_legs([leg("BURN", mode="FAST"), leg("MINT", mode="STANDARD")])
    assert paired == []
    assert errors == ["MODE_MISMATCH:0xabc"]
