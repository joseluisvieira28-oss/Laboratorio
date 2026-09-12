from types import SimpleNamespace
import pytest

from research.phase_b_h04_research_evaluator_v01 import _flow_pair, _required_flow


class FakeBar:
    def __init__(self, open_time, value=None, error=None):
        self.candle = SimpleNamespace(open_time=open_time)
        self._value = value
        self._error = error

    @property
    def flow_imbalance(self):
        if self._error is not None:
            raise ValueError(self._error)
        return self._value


def test_irrelevant_zero_volume_bar_is_not_evaluated():
    bars = {
        "BTCUSDT": {
            1000: FakeBar(1000, value=0.25),
            2000: FakeBar(2000, error="zero volume"),
        }
    }
    cache = {}
    assert _required_flow(bars, cache, "BTCUSDT", 1000, "BREAKOUT") == 0.25
    assert ("BTCUSDT", 2000) not in cache


def test_required_zero_volume_bar_fails_closed_with_context():
    bars = {"BTCUSDT": {1000: FakeBar(1000, error="zero volume")}}
    with pytest.raises(ValueError, match=r"required H04 flow undefined symbol=BTCUSDT role=BREAKOUT open_time=1000: zero volume"):
        _required_flow(bars, {}, "BTCUSDT", 1000, "BREAKOUT")


def test_flow_pair_evaluates_both_frozen_signal_bars():
    bars = {
        "ETHUSDT": {
            1000: FakeBar(1000, value=0.1),
            2000: FakeBar(2000, value=-0.2),
        }
    }
    signal = SimpleNamespace(breakout_open_time=1000, retest_open_time=2000)
    assert _flow_pair(bars, {}, "ETHUSDT", signal) == (0.1, -0.2)
