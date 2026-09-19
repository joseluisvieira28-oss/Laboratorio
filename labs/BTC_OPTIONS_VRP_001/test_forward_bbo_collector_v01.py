import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("forward_bbo_collector_v01.py")
spec = importlib.util.spec_from_file_location("collector", MODULE_PATH)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def test_select_instruments_is_deterministic_and_respects_envelope():
    now_ms = 1_700_000_000_000
    day = 86_400_000
    instruments = [
        {"kind":"option","is_active":True,"expiration_timestamp":now_ms+30*day,"strike":100.0,"option_type":"call","instrument_name":"C100"},
        {"kind":"option","is_active":True,"expiration_timestamp":now_ms+30*day,"strike":100.0,"option_type":"put","instrument_name":"P100"},
        {"kind":"option","is_active":True,"expiration_timestamp":now_ms+30*day,"strike":130.0,"option_type":"call","instrument_name":"TOO_FAR"},
        {"kind":"option","is_active":True,"expiration_timestamp":now_ms+10*day,"strike":100.0,"option_type":"call","instrument_name":"TOO_SHORT"},
        {"kind":"option","is_active":False,"expiration_timestamp":now_ms+30*day,"strike":100.0,"option_type":"call","instrument_name":"INACTIVE"},
    ]
    got = collector.select_instruments(instruments, 100.0, now_ms)
    assert [x["instrument_name"] for x in got] == ["C100", "P100"]


def test_first_level():
    assert collector.first_level({"bids":[[1.5, 2.0]]}, "bids") == (1.5, 2.0)
    assert collector.first_level({"asks":[]}, "asks") == (None, None)
