import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "evalmod", HERE / "scl_liqpull_mechanism_eval_v02.py"
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


def test_sides():
    assert m.normalize_trade_side("B") == "BUY"
    assert m.normalize_trade_side("A") == "SELL"


def test_proved_fill_has_no_markout_keys():
    books = [
        book(0, bd=1200.0),
        book(1000, bsz=0.01, bd=800.0),
        book(1500, bsz=0.01, bd=800.0),
        book(2500, bid=100.1, ask=101.1),
        book(6500, bid=100.2, ask=101.2),
        book(16500, bid=100.3, ask=101.3),
    ]
    trades = [trade(1200, "SELL", 100.0, 0.011)]
    fills = m.build_proved_fills(books, trades)
    row = [
        x for x in fills if x["side"] == "BUY" and x["entry_time_ms"] == 1000
    ][0]
    assert not any(k.startswith("markout_") for k in row)


def test_cancellation_does_not_advance_queue():
    books = [
        book(0),
        book(1000, bsz=2.0),
        book(1500, bsz=0.001),
        book(3500),
        book(7000),
        book(17000),
    ]
    trades = [trade(1200, "SELL", 100.0, 0.5)]
    fills = m.build_proved_fills(books, trades)
    assert not [
        x for x in fills if x["side"] == "BUY" and x["entry_time_ms"] == 1000
    ]


def test_sample_gate_blocks_outcomes():
    sample = m.sample_receipt([])
    assert sample["sample_gate_pass"] is False
