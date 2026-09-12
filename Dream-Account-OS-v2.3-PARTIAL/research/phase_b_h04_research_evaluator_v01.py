from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from math import isfinite
from statistics import mean, median
from typing import Mapping
from research.phase_b_h01_protect_after_tp1_v01 import simulate_h01_managed_outcome
from research.phase_b_h02_us_eu_overlap_session_gate_v01 import is_h02_signal_eligible
from research.phase_b_research_evaluator_v01 import EvaluationMetrics, FixedCohortCostMetrics, ResearchTradeRecord, day_block_bootstrap_expectancy, split_contiguous_segments
from research.phase_b_signal_formation_v01 import derive_signal_geometries, TIMEFRAME_MS
from dream_account.engines import calculate_costs

HYPOTHESIS_ID="H04_POSITIVE_TAKER_FLOW_PERSISTENCE"
@dataclass(frozen=True)
class MechanismMetrics:
    persistent_count:int
    nonpersistent_count:int
    persistent_tp1_rate:float|None
    nonpersistent_tp1_rate:float|None
    tp1_rate_difference:float|None

def _pf(v):
    g=sum(x for x in v if x>0); l=-sum(x for x in v if x<0); return None if l<=0 else g/l
def _rate(n,d): return n/d if d else None

def _required_flow(bar_maps, cache, symbol, open_time, role):
    key=(symbol,open_time)
    if key in cache: return cache[key]
    bar=bar_maps.get(symbol,{}).get(open_time)
    if bar is None: raise ValueError(f'required H04 flow bar missing symbol={symbol} role={role} open_time={open_time}')
    try: value=bar.flow_imbalance
    except ValueError as e: raise ValueError(f'required H04 flow undefined symbol={symbol} role={role} open_time={open_time}: {e}') from e
    cache[key]=value
    return value

def _flow_pair(bar_maps, cache, symbol, signal):
    breakout=_required_flow(bar_maps,cache,symbol,signal.breakout_open_time,'BREAKOUT')
    retest=_required_flow(bar_maps,cache,symbol,signal.retest_open_time,'RETEST')
    return breakout,retest

def evaluate_h04_universe(bars_by_symbol:Mapping[str,list], parameters, costs):
    selected=[]; base_for_mechanism=[]; totals=Counter(); data_times=[]; bar_maps={}; flow_cache={}
    for symbol in sorted(bars_by_symbol):
        bars=list(bars_by_symbol[symbol]); candles=[b.candle for b in bars]; bar_maps[symbol]={b.candle.open_time:b for b in bars}; data_times.extend(c.open_time for c in candles)
        segments,gaps=split_contiguous_segments(candles); totals['contiguous_segment_count']+=len(segments); totals['detected_gap_count']+=gaps
        for seg in segments:
            sigs=derive_signal_geometries(seg,parameters,costs,require_regular_spacing=True); totals['raw_geometry_count']+=len(sigs); totals['net_rr_rejected_count']+=sum(s.geometry_status=='REJECTED_NET_RR' for s in sigs)
            ready=[s for s in sigs if s.geometry_status=='GEOMETRY_READY']; sess=[s for s in ready if is_h02_signal_eligible(s)]; totals['session_rejected_ready_count'] += len(ready)-len(sess)
            active=None
            for s in sess:
                if active is not None and s.entry_open_time<=active: continue
                o=simulate_h01_managed_outcome(s,seg,costs,max_holding_bars=parameters.max_holding_bars,require_regular_spacing=True)
                r=ResearchTradeRecord(symbol=symbol,signal=s,outcome=o); base_for_mechanism.append(r); active=o.exit_open_time if o.exit_open_time is not None else seg[-1].open_time
            flow_ready=[]
            for s in sess:
                breakout_flow,retest_flow=_flow_pair(bar_maps,flow_cache,symbol,s)
                if breakout_flow>0.0 and retest_flow>0.0: flow_ready.append(s)
            active=None
            for s in flow_ready:
                if active is not None and s.entry_open_time<=active: totals['overlap_skipped_count']+=1; continue
                o=simulate_h01_managed_outcome(s,seg,costs,max_holding_bars=parameters.max_holding_bars,require_regular_spacing=True)
                r=ResearchTradeRecord(symbol=symbol,signal=s,outcome=o); selected.append(r); active=o.exit_open_time if o.exit_open_time is not None else seg[-1].open_time
    selected.sort(key=lambda r:(r.signal.entry_open_time,r.symbol,r.signal.fingerprint)); resolved=[r for r in selected if r.outcome.net_r is not None]; vals=[float(r.outcome.net_r) for r in resolved]
    if any(not isfinite(x) for x in vals): raise ValueError('non-finite R')
    span=(max(data_times)-min(data_times)+TIMEFRAME_MS)/86400000 if data_times else 0
    m=EvaluationMetrics(cost_scenario=costs.name,raw_geometry_count=totals['raw_geometry_count'],net_rr_rejected_count=totals['net_rr_rejected_count'],selected_trade_count=len(selected),overlap_skipped_count=totals['overlap_skipped_count'],unresolved_trade_count=len(selected)-len(resolved),resolved_trade_count=len(resolved),net_expectancy_r=mean(vals) if vals else None,median_net_r=median(vals) if vals else None,win_rate=_rate(sum(x>0 for x in vals),len(vals)),loss_rate=_rate(sum(x<0 for x in vals),len(vals)),profit_factor_r=_pf(vals),tp1_reach_rate=_rate(sum(r.outcome.tp1_reached for r in resolved),len(resolved)),same_bar_ambiguity_rate=_rate(sum(r.outcome.same_bar_stop_target_ambiguity for r in resolved),len(resolved)),time_exit_rate=_rate(sum(r.outcome.exit_reason=='TIME_EXIT_NEXT_OPEN' for r in resolved),len(resolved)),stop_gap_rate=_rate(sum(r.outcome.exit_reason in {'STOP_GAP','PROTECTIVE_STOP_GAP'} for r in resolved),len(resolved)),signal_frequency_per_30d=(len(selected)/span*30 if span>0 else None),symbol_distribution=dict(sorted(Counter(r.symbol for r in resolved).items())),contiguous_segment_count=totals['contiguous_segment_count'],detected_gap_count=totals['detected_gap_count'])
    p=[]; n=[]
    for r in base_for_mechanism:
        breakout_flow,retest_flow=_flow_pair(bar_maps,flow_cache,r.symbol,r.signal); persistent=breakout_flow>0 and retest_flow>0
        (p if persistent else n).append(r)
    mech=MechanismMetrics(len(p),len(n),_rate(sum(r.outcome.tp1_reached for r in p),len(p)),_rate(sum(r.outcome.tp1_reached for r in n),len(n)),None)
    if mech.persistent_tp1_rate is not None and mech.nonpersistent_tp1_rate is not None:
        mech=MechanismMetrics(mech.persistent_count,mech.nonpersistent_count,mech.persistent_tp1_rate,mech.nonpersistent_tp1_rate,mech.persistent_tp1_rate-mech.nonpersistent_tp1_rate)
    return selected,m,base_for_mechanism,mech,dict(totals)

def reprice_fixed(records, costs, min_net_rr=2.0):
    vals=[]; bad=0
    for r in records:
        s=r.signal; alt=calculate_costs(entry=s.entry,stop=s.stop,target=s.tp2,fee_pct_each_side=costs.fee_pct_each_side,spread_pct=costs.spread_pct,slippage_pct_each_side=costs.slippage_pct_each_side,funding_pct=0.0).net_rr
        bad += alt < min_net_rr
        if r.outcome.gross_return_pct is None: continue
        gross=r.outcome.gross_return_pct/100; stop=(s.entry-s.stop)/s.entry; c=costs.round_trip_cost_pct/100; vals.append((gross-c)/(stop+c))
    return FixedCohortCostMetrics(cost_scenario=costs.name,cohort_source='BASE_SELECTED_H04_TRADES',selected_trade_count=len(records),resolved_trade_count=len(vals),unresolved_trade_count=len(records)-len(vals),net_expectancy_r=mean(vals) if vals else None,median_net_r=median(vals) if vals else None,profit_factor_r=_pf(vals),net_rr_below_minimum_count=bad,net_rr_violation_rate=_rate(bad,len(records)))
