#!/usr/bin/env python3
"""Synthetic QA for neutral L2 primitives. No market data."""
from l2r_neutral_primitives_v01 import (
    Top5State, extract_top5, first_state_at_or_after, PrimitiveFailure, FROZEN_HORIZONS_MS
)


def levels():
    bids=[{"px":str(100-i),"sz":str(i+1),"n":1} for i in range(5)]
    asks=[{"px":str(101+i),"sz":str(i+1),"n":1} for i in range(5)]
    return [bids,asks]


def main() -> int:
    s0=extract_top5(1_000_000_000,1000,levels())
    assert s0.midpoint == 100.5
    assert s0.bid_depth5 == 15.0 and s0.ask_depth5 == 15.0

    s1=extract_top5(2_050_000_000,2050,levels())
    s2=extract_top5(6_100_000_000,6100,levels())
    arr=[s0,s1,s2]
    assert first_state_at_or_after(arr,s0.envelope_ns,1000) is s1
    assert first_state_at_or_after(arr,s0.envelope_ns,5000) is s2
    assert first_state_at_or_after(arr,s0.envelope_ns,15000) is None
    assert FROZEN_HORIZONS_MS == (1000,5000,15000,60000)

    bad=levels()
    bad[0][0]["px"]="101"
    try:
        extract_top5(1,1,bad)
    except PrimitiveFailure:
        pass
    else:
        raise AssertionError("crossed book failed to stop")

    print("L2_NEUTRAL_PRIMITIVES_SYNTHETIC_PASS | NO SWEEP THRESHOLD | NO OUTCOMES | NO PNL")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
