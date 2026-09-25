import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "evalmod", HERE / "scl_liqpull_mechanism_eval_v01.py"
)
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def book(t, bid=100.0, bsz=2.0, ask=101.0, asz=2.0, bd=None, ad=None):
    return m.Book(
        t,
        t * 1000,
        bid,
        bsz,
        ask,
        asz,
        bd if bd is not None else bid * bsz * 5,
        ad if ad is not None else ask * asz * 5,
    )


def trade(t, side, px, sz):
    return m.Trade(t, t * 1000, side, px, sz)


def test_trade_side_normalization():
    assert m.normalize_trade_side("B") == "BUY"
    assert m.normalize_trade_side("A") == "SELL"


def test_conservative_fill_and_markouts():
    books = [
        book(0, bd=1200.0, ad=1212.0),
        book(1000, bsz=0.010, bd=800.0, ad=1212.0),
        book(1500, bsz=0.010, bd=800.0, ad=1212.0),
        book(2500, bid=100.1, ask=101.1, bd=1001.0, ad=1011.0),
        book(6500, bid=100.2, ask=101.2, bd=1002.0, ad=1012.0),
        book(16500, bid=100.3, ask=101.3, bd=1003.0, ad=1013.0),
    ]
    trades = [trade(1200, "SELL", 100.0, 0.011)]
    rows = m.build_observations(books, trades)
    buys = [
        r
        for r in rows
        if r["side"] == "BUY" and r["entry_time_ms"] == 1000
    ]
    assert len(buys) == 1
    r = buys[0]
    assert r["fill_time_ms"] == 1200
    assert r["pull_score"] > 0
    assert r["markout_5000ms_bps"] > 0


def test_cancellation_after_entry_does_not_fake_fill():
    books = [
        book(0),
        book(1000, bsz=2.0),
        book(1500, bsz=0.001),
        book(3500),
        book(7000),
        book(17000),
    ]
    trades = [trade(1200, "SELL", 100.0, 0.5)]
    rows = m.build_observations(books, trades)
    assert not [
        r
        for r in rows
        if r["side"] == "BUY" and r["entry_time_ms"] == 1000
    ]


def test_insufficient_sample_fails_closed():
    r = m.adjudicate([])
    assert r["classification"] == "INSUFFICIENT_FORWARD_SAMPLE"
    assert r["pnl_computed"] is False
