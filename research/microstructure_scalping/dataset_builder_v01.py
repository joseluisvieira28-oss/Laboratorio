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
    event_time=d["cts"] if d["cts"] is not None else d["ts"]
    return {
        "event_time_ms":event_time,
        "clock_source":"cts" if d["cts"] is not None else "ts",
        "ts":d["ts"],"cts":d["cts"],
        "update_id":d["update_id"],"seq":d["seq"],
        "mid":mid,"best_bid":d["best_bid"],"best_ask":d["best_ask"],
        "spread_bps":d["spread_bps"],
        "microprice_displacement_bps":(d["microprice"]-mid)/mid*10000.0,
        "imbalance_l1":d["imbalance_l1"],
        "imbalance_l5":d["imbalance_l5"],
        "imbalance_l10":d["imbalance_l10"],
    }


def build_rows(messages: Iterable[Dict], horizons_ms=HORIZONS_MS, anchor_interval_ms=0) -> List[Dict]:
    replay=L2Replay()
    horizons=tuple(sorted(int(h) for h in horizons_ms))
    pending=deque()
    waiting={h:deque() for h in horizons}
    out=[]
    last_anchor_time=None

    for msg in messages:
        raw_now=msg.get("cts")
        if raw_now is None:
            raw_now=msg.get("ts")
        if raw_now is None:
            raise ValueError("missing_event_clock")

        anchor_due=(
            anchor_interval_ms==0 or
            last_anchor_time is None or
            raw_now-last_anchor_time >= anchor_interval_ms
        )
        st=replay.apply(msg,compute_depth_features=anchor_due)
        now=st.cts if st.cts is not None else st.ts

        # Resolve existing anchors from this current/future state.
        for h in horizons:
            q=waiting[h]
            while q and now >= q[0]["feature"]["event_time_ms"]+h:
                item=q.popleft()
                item["targets"][h]={
                    "mid":st.mid,
                    "best_bid":st.best_bid,
                    "best_ask":st.best_ask,
                    "event_time_ms":now,
                }

        while pending and all(v is not None for v in pending[0]["targets"].values()):
            item=pending.popleft()
            row=dict(item["feature"])
            base_mid=row["mid"]
            for h,t in item["targets"].items():
                row[f"label_time_{h}ms"]=t["event_time_ms"]
                row[f"fwd_mid_{h}ms"]=t["mid"]
                row[f"fwd_bid_{h}ms"]=t["best_bid"]
                row[f"fwd_ask_{h}ms"]=t["best_ask"]
                row[f"fwd_return_bps_{h}ms"]=(t["mid"]-base_mid)/base_mid*10000.0
            out.append(row)

        if not anchor_due:
            continue

        feat=contemporaneous_features(st)
        item={"feature":feat,"targets":{h:None for h in horizons}}
        pending.append(item)
        for h in horizons:
            waiting[h].append(item)
        last_anchor_time=now

    return out
