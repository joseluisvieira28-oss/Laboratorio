import json,tempfile,pytest
from pathlib import Path
from research.liquidation_cascade.licp001_trigger_engine_v01 import load_config
from research.liquidation_cascade.licp_fwd_xalt_004_state_v01 import ENTRY_DELAY_MS,HORIZON_MS,FEE_BPS

def test_fwd_xalt_requires_frozen_config():
    cfg={"status":"UNFROZEN","btc_ignition":{},"binance_confirmation":{},"alt_propagation":{}}
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"c.json";p.write_text(json.dumps(cfg))
        with pytest.raises(PermissionError):
            load_config(p)

def test_historical_candidate_constants_are_frozen():
    assert ENTRY_DELAY_MS==60_000
    assert HORIZON_MS==3_600_000
    assert FEE_BPS==16.0

def test_observer_still_sell_only():
    src=Path("research/liquidation_cascade/licp_fwd_xalt_004_observer_v01.py").read_text()
    assert 'b.pressure=="SELL"' in src
    assert 'make_record("SELL"' in src
