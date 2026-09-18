#!/usr/bin/env python3
"""Deterministic V0.12.1 evaluator eligibility self-test."""
from __future__ import annotations
import pandas as pd
import evaluate_chain_exact_features_v0121 as rem

df=pd.DataFrame({
 "decoder_complete_w30":[True,True,False],
 "decoder_complete_w60":[True,True,False],
 "decoder_complete_w300":[True,True,False],
 "sol_volume_complete_w30":[True,False,False],
 "sol_volume_complete_w60":[True,False,False],
 "sol_volume_complete_w300":[True,False,False],
})

def ids(mask):
    return list(df.index[mask])

# Structural features retain authoritative non-SOL quote rows.
assert ids(rem.eligibility_mask_v0121(df,"buy_count_w30"))==[0,1]
assert ids(rem.eligibility_mask_v0121(df,"unique_participants_w300"))==[0,1]
assert ids(rem.eligibility_mask_v0121(df,"count_balance_w60"))==[0,1]
assert ids(rem.eligibility_mask_v0121(df,"decoded_trade_events_accel_per_sec_w30_vs_w60"))==[0,1]

# SOL-denominated features fail closed on non-SOL quote rows.
assert ids(rem.eligibility_mask_v0121(df,"buy_volume_sol_w30"))==[0]
assert ids(rem.eligibility_mask_v0121(df,"net_flow_sol_w300"))==[0]
assert ids(rem.eligibility_mask_v0121(df,"volume_balance_w60"))==[0]
assert ids(rem.eligibility_mask_v0121(df,"net_flow_sol_accel_per_min_w60_vs_w300"))==[0]

print("V0121_EVALUATOR_ELIGIBILITY_SELFTEST_PASS")
