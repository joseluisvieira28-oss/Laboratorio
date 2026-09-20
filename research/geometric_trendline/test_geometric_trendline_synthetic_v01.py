#!/usr/bin/env python3
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geometric_trendline_core_v01 import (
    Bar,
    LineState,
    WARMUP_END_TS_MS,
    discover_events_in_segment,
    evaluate_event_responses,
)

HOUR = 3_600_000

def make_support_case(include_overlap_resistance=False):
    base = WARMUP_END_TS_MS
    bars = []
    for i in range(60):
        close = 110.0 + 0.05 * i
        bars.append(Bar(base + i * HOUR, close - 0.2, close + 1.0, close - 1.0, close, 1.0))
    def repl(i, low=None, high=None, close=None):
        b = bars[i]
        bars[i] = Bar(b.ts_ms,b.open,b.high if high is None else high,b.low if low is None else low,b.close if close is None else close,b.volume)
    repl(5, low=100.0)
    repl(20, low=104.0)
    repl(24, low=105.0, high=112.0, close=111.2)
    if include_overlap_resistance:
        repl(6, high=120.0)
        repl(21, high=118.0)
        repl(25, low=111.0, high=117.5, close=112.0)
        repl(32, low=111.0, high=116.6, close=112.0)
    return bars

def test_line_equation():
    line = LineState("support",5,20,100.0,104.0,23,359)
    assert abs(line.price_at(5)-100.0) < 1e-12
    assert abs(line.price_at(20)-104.0) < 1e-12
    assert abs(line.price_at(24)-105.06666666666666) < 1e-9

def test_second_pivot_not_usable_before_confirmation():
    bars=make_support_case()
    early,_=discover_events_in_segment(bars[:23])
    at_confirmation,_=discover_events_in_segment(bars[:24])
    assert early == []
    assert at_confirmation == []

def test_first_post_confirmation_touch_is_event():
    bars=make_support_case()
    events,stats=discover_events_in_segment(bars)
    assert len(events)==1
    e=events[0]
    assert e.side=="support" and e.direction==1 and e.idx==24
    assert stats["accepted_events"]==1

def test_future_mutation_cannot_change_past_event():
    bars=make_support_case()
    events_a,_=discover_events_in_segment(bars)
    mutated=deepcopy(bars)
    for i in range(30,len(mutated)):
        b=mutated[i]
        mutated[i]=Bar(b.ts_ms,b.open,b.high+1000.0,max(1.0,b.low-50.0),b.close*1.5,b.volume)
    events_b,_=discover_events_in_segment(mutated)
    key_a=[(e.side,e.idx,e.p1_idx,e.p2_idx,round(e.line_price,10)) for e in events_a if e.idx<=24]
    key_b=[(e.side,e.idx,e.p1_idx,e.p2_idx,round(e.line_price,10)) for e in events_b if e.idx<=24]
    assert key_a==key_b

def test_cooldown_first_interaction_consumes_line():
    bars=make_support_case(include_overlap_resistance=True)
    events,stats=discover_events_in_segment(bars)
    assert [(e.side,e.idx) for e in events] == [("support",24)]
    assert stats["suppressed_overlap"]==1

def test_response_is_post_event_only():
    bars=make_support_case()
    events,_=discover_events_in_segment(bars)
    rows=evaluate_event_responses(bars,events,horizons=(1,6))
    expected=10000.0*(bars[30].close/bars[24].close-1.0)
    assert abs(rows[0]["response_6h_bps"]-expected) < 1e-12

if __name__=="__main__":
    fns=[test_line_equation,test_second_pivot_not_usable_before_confirmation,test_first_post_confirmation_touch_is_event,test_future_mutation_cannot_change_past_event,test_cooldown_first_interaction_consumes_line,test_response_is_post_event_only]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"SYNTHETIC_CAUSALITY_PASS {len(fns)}/{len(fns)}")
