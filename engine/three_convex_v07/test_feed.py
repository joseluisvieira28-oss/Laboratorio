"""Tests for strict cached 5m market collection. All HTTP responses faked."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from engine.three_convex_v07.feed import (
    LOOKBACK, MS5,fetch_complete,FeedHalt,clock_ms, fresh_signals
)


def fixture(symbol,now):
    boundary=now//MS5*MS5
    final=boundary-MS5
    if now-boundary<2000:final-=MS5
    start=final-(LOOKBACK-1)*MS5
    calls=[]
    def public(path,params=None):
        calls.append(params)
        return [[i,100.0,101.0,99.0,100.0,100.0,
                 i+MS5-1] for i in range(params["startTime"],
                                          params["startTime"]+params["limit"]*MS5,MS5)]
    return public,calls


class FeedTests(TestCase):
    def test_download_exact_count_and_cached_second_call_no_http(self):
        now=2_000_000_000_000
        with TemporaryDirectory() as td:
            f,calls=fixture("SOL_USDT",now)
            bars=fetch_complete("SOL_USDT",now,td,public=f)
            self.assertEqual(len(bars),LOOKBACK)
            self.assertGreater(len(calls),5)
            def no_http(*args,**kwargs):
                raise AssertionError("HTTP UNNECESSARY")
            again=fetch_complete("SOL_USDT",now,td,public=no_http)
            self.assertEqual(bars[-1].t,again[-1].t)

    def test_next_closed_bar_only_requests_new_delta(self):
        now=2_000_000_000_000
        with TemporaryDirectory() as td:
            f,_=fixture("SOL_USDT",now)
            fetch_complete("SOL_USDT",now,td,public=f)
            g,calls=fixture("SOL_USDT",now+MS5)
            fetch_complete("SOL_USDT",now+MS5,td,public=g)
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0]["limit"],1)

    def test_missing_page_must_halt(self):
        now=2_000_000_000_000
        with TemporaryDirectory() as td:
            with self.assertRaisesRegex(FeedHalt,"MISSING_PUBLIC"):
                fetch_complete("SOL_USDT",now,td,public=lambda *a:[])

    def test_cache_tamper_must_halt(self):
        now=2_000_000_000_000
        with TemporaryDirectory() as td:
            f,_=fixture("SOL_USDT",now)
            fetch_complete("SOL_USDT",now,td,public=f)
            p=Path(td)/"SOL_USDT_binance_5m.json"
            d=json.loads(p.read_text());d["bars"][0][3]=200
            p.write_text(json.dumps(d))
            with self.assertRaisesRegex(FeedHalt,"PUBLIC_CACHE_UNTRUSTED"):
                fetch_complete("SOL_USDT",now,td,public=f)

    def test_unknown_symbol_blocked(self):
        with TemporaryDirectory() as td:
            with self.assertRaisesRegex(FeedHalt,"INVALID_SYMBOL"):
                fetch_complete("BTC_USDT",2_000_000_000_000,td)

    def test_source_clock_skew_blocked(self):
        with self.assertRaisesRegex(FeedHalt,"CLOCK_OFFSET"):
            clock_ms(public=lambda p:{"serverTime":100000},clock=lambda:200000)

    def test_close_not_replayed_before_install(self):
        from engine.three_convex_v05.signals import Bar
        with patch("engine.three_convex_v07.feed.closed_signal_decisions",
                   return_value=[{"lane":"SOL_CONVEX_NATIVE_5M",
                                  "symbol":"SOL_USDT","signal_close_ms":100000,
                                  "signal_id":"id"}]):
            self.assertEqual(fresh_signals("SOL_USDT",[],110000,109000),[])
