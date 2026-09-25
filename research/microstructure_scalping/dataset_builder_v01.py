"""Causal feature/label builder for historical L2 replay.

No strategy selection. No threshold search. No PnL optimization.
"""
from collections import deque
from dataclasses import asdict
from typing import Iterable, Dict, List
from .l2_replay import L2Replay

HORIZONS_MS=(100,500,1000,5000,15000,30000)


def contemporaneous_features(state):
    d=asdict(state)
    mid=d["mid"]
    return {
        "ts":d["ts"],
        "cts":d["cts"],
        "update_id":d["update_id"],
        "seq":d["seq"],
        "mid":mid,
        "spread_bps":d["spread_bps"],
        "microprice_displacement_bps":(d["microprice"]-mid)/mid*10000.0,
        "imbalance_l1":d["imbalance_l1"],
        "imbalance_l5":d["imbalance_l5"],
        "imbalance_l10":d["imbalance_l10"],
    }


def build_rows(messages: Iterable[Dict], horizons_ms=HORIZONS_MS) -> List[Dict]:
    """Build features at t and labels from the first state at/after t+h.

    This intentionally uses no interpolation. Rows missing any requested horizon
    at the end of a stream are omitted.
    """
    replay=L2Replay()
    pending=deque()
    out=[]
    horizons=tuple(sorted(int(h) for h in horizons_ms))

    for msg in messages:
        st=replay.apply(msg)
        now=st.ts
        current_mid=st.mid
        pending.append({
            "feature":contemporaneous_features(st),
            "targets":{h:None for h in horizons}
        })

        # Resolve labels using only current/future states.
        for item in pending:
            base_ts=item["feature"]["ts"]
            for h in horizons:
                if item["targets"][h] is None and now >= base_ts+h:
                    item["targets"][h]=current_mid

        while pending and all(v is not None for v in pending[0]["targets"].values()):
            item=pending.popleft()
            row=dict(item["feature"])
            base_mid=row["mid"]
            for h,target_mid in item["targets"].items():
                row[f"fwd_mid_{h}ms"]=target_mid
                row[f"fwd_return_bps_{h}ms"]=(target_mid-base_mid)/base_mid*10000.0
            out.append(row)
    return out
