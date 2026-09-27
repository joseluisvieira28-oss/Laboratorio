# REACTIVE-SHOCK-SCALP-005 — EXECUTION RETURN ARITHMETIC CORRECTION V0.1

Date: 2026-09-26
Status: TECHNICAL CORRECTION — SIGNAL SCIENCE UNCHANGED

After the first successful MVE receipt, code review found that SHORT executable return used the future exit quote as the percentage denominator.

Incorrect SHORT expression:
- taker: (entry_bid - future_ask) / future_ask
- maker ceiling: (entry_ask - future_bid) / future_bid

Correct executable return:
- taker: (entry_bid - future_ask) / entry_bid
- maker ceiling: (entry_ask - future_bid) / entry_ask

LONG arithmetic was already correct.

The signal, events, entry timestamp, exit timestamp, flow rule, horizons, fee overlays and survival gate are unchanged.

Required action:
- rerun the same 8-event MVE with corrected arithmetic;
- treat the earlier economic numbers as superseded;
- do not launch fresh-event replication until corrected MVE classification is checked.
