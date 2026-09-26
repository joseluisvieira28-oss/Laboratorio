import json, subprocess, sys
from pathlib import Path

def write_shard(root,name,start_ms,seconds,bybit_events=0,btc_events=0,uptime=1.0):
    d=root/name;d.mkdir()
    events=[]
    for i in range(bybit_events):
        sym="BTCUSDT" if i<btc_events else "ETHUSDT"
        events.append({"venue":"BYBIT","symbol":sym,"exchange_ts_ms":start_ms+i*1000,
                       "liquidated_side":"Buy","notional_proxy":1000+i,"qty":1,"price":1000+i,
                       "recv_ts_ms":start_ms+i*1000,"recv_mono_ns":i+1})
    (d/"liquidations.jsonl").write_text("\n".join(json.dumps(x) for x in events))
    from datetime import datetime,timezone
    end=datetime.fromtimestamp((start_ms+seconds*1000)/1000,tz=timezone.utc).isoformat()
    h={"outcome_blind":True,"started_wall_ms":start_ms,"ended_at":end,"scheduled_seconds":seconds,
       "event_log_sha256":"0"*64,"health":{
         v:{"connected_seconds":seconds*uptime,"clock_regressions":0} for v in ("bybit","binance","mexc")}}
    (d/"health.json").write_text(json.dumps(h))

def test_aggregate_refuses_to_be_ready_before_seven_days(tmp_path):
    write_shard(tmp_path,"a",0,3600,250,50)
    out=tmp_path/"out.json"
    subprocess.check_call([sys.executable,"-m","research.liquidation_cascade.licp001_aggregate_calibration_v01",str(tmp_path),"--out",str(out)])
    r=json.loads(out.read_text())
    assert r["eligible_for_freeze"] is False
    assert r["eligibility"]["bybit_events"]==250

def test_aggregate_ready_only_when_all_floors_pass(tmp_path):
    write_shard(tmp_path,"a",0,3600,125,25)
    write_shard(tmp_path,"b",7*86400000,3600,125,25)
    out=tmp_path/"out.json"
    subprocess.check_call([sys.executable,"-m","research.liquidation_cascade.licp001_aggregate_calibration_v01",str(tmp_path),"--out",str(out)])
    r=json.loads(out.read_text())
    assert r["eligible_for_freeze"] is True
    assert r["eligibility"]["span_days"]>=7
    assert r["eligibility"]["clock_regressions"]==0
    assert len(r["eligibility"]["raw_event_log_sha256"])==64
