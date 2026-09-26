import json,tempfile,pytest
from pathlib import Path
from research.liquidation_cascade.licp001_trigger_engine_v01 import load_config

def test_fwd_xalt_requires_frozen_config():
    cfg={"status":"UNFROZEN","btc_ignition":{},"binance_confirmation":{},"alt_propagation":{}}
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"c.json";p.write_text(json.dumps(cfg))
        with pytest.raises(PermissionError):
            load_config(p)

def test_historical_candidate_constants_are_not_parameterized():
    src=Path("research/liquidation_cascade/licp_fwd_xalt_004_observer_v01.py").read_text()
    assert "ENTRY_DELAY_MS=60_000" in src
    assert "HORIZON_MS=3_600_000" in src
    assert "FEE_BPS=16.0" in src
    assert 'b.pressure=="SELL"' in src
