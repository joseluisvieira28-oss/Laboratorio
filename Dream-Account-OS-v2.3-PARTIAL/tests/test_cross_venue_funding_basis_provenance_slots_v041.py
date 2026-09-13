from __future__ import annotations

import importlib.util
import json
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

MODULE_PATH = RESEARCH / "cross_venue_funding_basis_provenance_slots_v041.py"
SPEC = importlib.util.spec_from_file_location("cvfb_slots_v041", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_frozen_pacing_has_conservative_headroom_under_documented_weight_model():
    page_items = 500
    conservative_weight = 20 + page_items // 20
    requests_per_minute = 60.0 / mod.MIN_REQUEST_INTERVAL_SECONDS
    assert conservative_weight == 45
    assert requests_per_minute * conservative_weight < 1200
    assert mod.MIN_REQUEST_INTERVAL_SECONDS == 3.0
    assert mod.HTTP_429_COOLDOWN_SECONDS == 15.0
    assert mod.MAX_ATTEMPTS_PER_PAGE == 6


def test_pacing_waits_between_request_starts(monkeypatch):
    clock = {"t": 100.0}
    sleeps = []

    def monotonic():
        return clock["t"]

    def sleep(seconds):
        sleeps.append(seconds)
        clock["t"] += seconds

    monkeypatch.setattr(mod.time, "monotonic", monotonic)
    monkeypatch.setattr(mod.time, "sleep", sleep)
    client = mod.HyperliquidPacedClient()
    client._pace()
    clock["t"] += 0.5
    client._pace()
    assert sleeps == [pytest.approx(2.5)]


def test_429_waits_and_retries_same_request(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def read(self):
            return json.dumps([]).encode()

    calls = {"n": 0}
    sleeps = []
    clock = {"t": 0.0}

    def fake_urlopen(req, timeout=30):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", hdrs=None, fp=None)
        return FakeResponse()

    def monotonic():
        return clock["t"]

    def sleep(seconds):
        sleeps.append(seconds)
        clock["t"] += seconds

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(mod.time, "monotonic", monotonic)
    monkeypatch.setattr(mod.time, "sleep", sleep)

    req = mod.build_hyperliquid_funding_request("BTC", mod.AUDIT_START_MS, mod.AUDIT_START_MS + 1000)
    client = mod.HyperliquidPacedClient()
    assert client.request_json(req) == []
    assert calls["n"] == 2
    assert client.http_429_retry_count == 1
    assert client.request_count == 2
    assert mod.HTTP_429_COOLDOWN_SECONDS in sleeps


def test_fetch_pagination_advances_last_timestamp_plus_one(monkeypatch):
    client = mod.HyperliquidPacedClient()
    requested_starts = []
    batches = [
        [{"coin": "BTC", "time": mod.AUDIT_START_MS + 100, "fundingRate": "0.1"}],
        [],
    ]

    def fake_request_json(req):
        payload = json.loads(req.data.decode())
        requested_starts.append(payload["startTime"])
        return batches.pop(0)

    monkeypatch.setattr(client, "request_json", fake_request_json)
    rows = client.fetch_funding("BTC", mod.AUDIT_START_MS, mod.AUDIT_START_MS + 10000)
    assert len(rows) == 1
    assert requested_starts == [mod.AUDIT_START_MS, mod.AUDIT_START_MS + 101]


def test_locked_2026_still_forbidden():
    client = mod.HyperliquidPacedClient()
    with pytest.raises(mod.TransportFailure):
        client.fetch_funding("BTC", mod.AUDIT_START_MS, mod.LOCKED_2026_START_MS)


def test_no_economic_markers_are_enabled():
    assert mod.carry_computed is False
    assert mod.apr_apy_computed is False
    assert mod.pnl_computed is False
    assert mod.signals_computed is False
