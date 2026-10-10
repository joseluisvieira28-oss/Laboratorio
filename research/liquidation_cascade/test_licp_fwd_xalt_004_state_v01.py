import json
import pytest

from research.liquidation_cascade.licp_fwd_xalt_004_state_v01 import (
    ENTRY_DELAY_MS,HORIZON_MS,FEE_BPS,STALE_MS,
    make_record,add_episode,apply_bbo,mark_restart_gaps,
    save_records,load_records,evaluate_forward
)

def burst(start,end,total=1000.0):
    return {"source":"x","symbol":"BTCUSDT","start_ms":start,"end_ms":end,
            "pressure":"SELL","total_notional":total,"side_concentration":1.0}

def test_frozen_science_constants():
    assert ENTRY_DELAY_MS==60_000
    assert HORIZON_MS==3_600_000
    assert FEE_BPS==16.0
    assert STALE_MS==1_000

def test_episode_dedup_is_deterministic():
    a=burst(1000,6000);b=burst(2000,7000)
    r1=make_record("SELL",a,b,1_000_000)
    r2=make_record("SELL",a,b,1_000_001)
    rows=[]
    assert add_episode(rows,r1) is True
    assert add_episode(rows,r2) is False
    assert len(rows)==1

def test_entry_exit_exact_fresh_bbo_timing():
    r=make_record("SELL",burst(1,2),burst(3,4),1_000_000)
    rows=[r];mono=10_000_000_000
    before={"wall_ms":r["entry_due_wall_ms"]-1,"local_ns":mono,"bid":100.0,"ask":100.1}
    assert apply_bbo(rows,before,mono) is False
    due={"wall_ms":r["entry_due_wall_ms"],"local_ns":mono,"bid":100.0,"ask":100.1}
    assert apply_bbo(rows,due,mono) is True
    preexit={"wall_ms":r["entry"]["wall_ms"]+HORIZON_MS-1,"local_ns":mono,"bid":99.0,"ask":99.1}
    assert apply_bbo(rows,preexit,mono) is False
    exitb={"wall_ms":r["entry"]["wall_ms"]+HORIZON_MS,"local_ns":mono,"bid":98.9,"ask":99.0}
    assert apply_bbo(rows,exitb,mono) is True
    assert r["gross_bps"]==pytest.approx(100.0)
    assert r["net_taker_bps"]==pytest.approx(84.0)

def test_stale_crossed_and_restart_fail_closed():
    r=make_record("SELL",burst(1,2),burst(3,4),1_000_000)
    mono=10_000_000_000
    stale={"wall_ms":r["entry_due_wall_ms"],"local_ns":mono-(STALE_MS+1)*1_000_000,"bid":100.0,"ask":100.1}
    crossed={"wall_ms":r["entry_due_wall_ms"],"local_ns":mono,"bid":100.1,"ask":100.0}
    assert apply_bbo([r],stale,mono) is False
    assert apply_bbo([r],crossed,mono) is False
    assert mark_restart_gaps([r],r["entry_due_wall_ms"]+1) is True
    assert r["entry_missed_restart"] is True

def test_state_round_trip_duplicate_guard(tmp_path):
    p=tmp_path/"state.json"
    r=make_record("SELL",burst(1,2),burst(3,4),1_000_000)
    save_records(p,[r])
    assert load_records(p)==[r]
    j=json.loads(p.read_text());j["records"].append(dict(r));p.write_text(json.dumps(j))
    with pytest.raises(ValueError,match="DUPLICATE_EPISODE_ID"):
        load_records(p)

def completed_record(event_ms,gross=30.0):
    r=make_record("SELL",burst(event_ms,event_ms+1),burst(event_ms+2,event_ms+3),event_ms)
    r["entry"]={"wall_ms":r["entry_due_wall_ms"],"entry_bid":100.0,"bid":100.0,"ask":100.1}
    r["exit"]={"wall_ms":r["entry"]["wall_ms"]+HORIZON_MS,"exit_ask":99.7,"bid":99.6,"ask":99.7}
    r["gross_bps"]=gross;r["net_taker_bps"]=gross-FEE_BPS
    return r

def test_verdict_and_missing_rate_gates():
    day=86_400_000
    base=1_700_000_000_000
    rows=[completed_record(base+(i%3)*day+i*120_000,30.0) for i in range(20)]
    now=max(r["entry_due_wall_ms"]+HORIZON_MS for r in rows)+1
    out=evaluate_forward(rows,now)
    assert out["completed_episodes"]==20
    assert out["distinct_utc_dates"]>=3
    assert out["decision"]=="FORWARD_TRANSFER_SURVIVES"

    for r in rows[:3]:
        r["exit"]=None;r.pop("gross_bps");r.pop("net_taker_bps");r["exit_missed_restart"]=True
    out=evaluate_forward(rows,now)
    assert out["missing_rate"]>0.10
    assert out["decision"]=="FORWARD_INSUFFICIENT"
