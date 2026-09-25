from pathlib import Path
import json
import tempfile
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("collector", HERE / "scl_liqpull_raw_collector_v01.py")
collector = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = collector
SPEC.loader.exec_module(collector)


def test_subscriptions_public_only():
    subs = collector.subscriptions()
    assert len(subs) == 2
    assert {x["subscription"]["type"] for x in subs} == {"l2Book", "trades"}
    assert all(x["subscription"]["coin"] == "BTC" for x in subs)


def test_writer_preserves_raw_and_marks_no_outcomes():
    with tempfile.TemporaryDirectory() as td:
        w = collector.RawShardWriter(Path(td), "deadbeefcafebabe")
        payload = {"channel": "l2Book", "data": {"coin": "BTC", "time": 1, "levels": [[], []]}}
        w.write(payload, 123, 456)
        w.close()
        manifest = json.loads(w.manifest_path.read_text())
        assert manifest["line_count"] == 1
        assert manifest["outcomes_computed"] is False
        assert manifest["derived_features_computed"] is False
        assert manifest["authenticated_endpoint_used"] is False
        assert manifest["orders_sent"] is False
        assert manifest["historical_backfill"] is False
        line = json.loads(w.raw_path.read_text().strip())
        assert line["provider_payload"] == payload
        assert line["protocol_commit"] == "deadbeefcafebabe"
