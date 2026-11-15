import json, tempfile
from pathlib import Path
import subprocess,sys

def test_calibration_has_no_outcome_fields():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"e.jsonl"
        rows=[
          {"venue":"BYBIT","symbol":"BTCUSDT","exchange_ts_ms":1000,"notional_proxy":100.0},
          {"venue":"BYBIT","symbol":"BTCUSDT","exchange_ts_ms":1400,"notional_proxy":200.0},
          {"venue":"BYBIT","symbol":"BTCUSDT","exchange_ts_ms":3000,"notional_proxy":50.0},
        ]
        p.write_text("\n".join(json.dumps(x) for x in rows))
        o=Path(d)/"r.json"
        subprocess.check_call([sys.executable,"research/liquidation_cascade/licp001_calibrate_v01.py",str(p),"--out",str(o)])
        r=json.loads(o.read_text())
        s=json.dumps(r).lower()
        for forbidden in ("forward_return","pnl","sharpe","mfe","mae","direction_accuracy"):
            assert forbidden not in s
        assert r["outcome_blind"] is True

def test_500ms_rolling_notional():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"e.jsonl"
        rows=[
          {"venue":"BYBIT","symbol":"BTCUSDT","exchange_ts_ms":1000,"notional_proxy":100.0},
          {"venue":"BYBIT","symbol":"BTCUSDT","exchange_ts_ms":1400,"notional_proxy":200.0},
        ]
        p.write_text("\n".join(json.dumps(x) for x in rows))
        o=Path(d)/"r.json"
        subprocess.check_call([sys.executable,"research/liquidation_cascade/licp001_calibrate_v01.py",str(p),"--out",str(o)])
        r=json.loads(o.read_text())
        assert r["groups"]["BYBIT:BTCUSDT"]["windows"]["500"]["observations"]==2
