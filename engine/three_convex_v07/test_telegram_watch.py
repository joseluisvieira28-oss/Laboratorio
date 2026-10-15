"""V07 Telegram operator safety tests, all offline fake transports."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import json
import time

from engine.three_convex_v07.telegram import TelegramBot,TelegramHalt,message_for
from engine.three_convex_v07.watch import DurableQueue,cycle
from engine.three_convex_v07.feed import FeedHalt

TOKEN="12345678:"+"A"*35
CHAT="1234567890"


class Reply:
    status=200
    def __init__(self,ok=True,redirect=None):
        self.ok=ok;self.redirect=redirect
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def geturl(self):return self.redirect or "https://api.telegram.org/"
    def read(self,limit=0):
        return json.dumps({"ok":self.ok,"result":{"message_id":12345}}).encode()


class FakeHTTP:
    def __init__(self,ok=True,redirect=None,fail=False):
        self.ok=ok;self.redirect=redirect;self.fail=fail;self.requests=[]
    def __call__(self,req,timeout=0):
        self.requests.append((req,timeout))
        if self.fail:raise RuntimeError("secret could be in HTTP stack")
        return Reply(self.ok,self.redirect)


class NoNetworkBot:
    def __init__(self,fail=False):self.messages=[];self.fail=fail
    def send(self,s):
        if self.fail:raise TelegramHalt("MOCK_DELIVERY_FAILED")
        self.messages.append(s)
        return len(self.messages)


class Account:
    pass


def flat():
    return {"status":"AUTHENTICATED_ACCOUNT_AND_PUBLIC_MARKET_READS_NO_LIVE_GO",
            "broker_account_flat_observed_once":True,
            "open_positions_count":0,"open_orders_count_all_pages":0,"open_stops_count":0}

def open_position():
    d=flat()
    d.update(broker_account_flat_observed_once=False,
             open_positions_count=1,open_stops_count=0)
    return d


def fake_signal(lane="SOL_CONVEX_NATIVE_5M",symbol="SOL_USDT",close=1_000_000):
    return {"lane":lane,"symbol":symbol,
            "signal_id":lane+":"+str(close),"signal_close_ms":close}


class TestTelegram(TestCase):
    def test_sent_as_post_to_allowlisted_api_only(self):
        h=FakeHTTP()
        bot=TelegramBot(TOKEN,CHAT,opener=h)
        self.assertEqual(bot.send("CONVEX SIGNAL NOT ORDER"),12345)
        req,timeout=h.requests[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(timeout,10)
        body=json.loads(req.data)
        self.assertEqual(body["chat_id"],CHAT)
        self.assertEqual(body["text"],"CONVEX SIGNAL NOT ORDER")

    def test_invalid_secret_rejected_no_web(self):
        with self.assertRaisesRegex(TelegramHalt,"INVALID_BOT_TOKEN"):
            TelegramBot("fake","1234")

    def test_secret_hidden_on_network_failure(self):
        h=FakeHTTP(fail=True)
        bot=TelegramBot(TOKEN,CHAT,opener=h)
        with self.assertRaises(TelegramHalt) as ctx:
            bot.send("failed")
        self.assertNotIn(TOKEN,str(ctx.exception))

    def test_redirect_to_other_domain_rejected(self):
        h=FakeHTTP(redirect="https://attacker.example.invalid")
        with self.assertRaisesRegex(TelegramHalt,"DELIVERY_UNVERIFIED"):
            TelegramBot(TOKEN,CHAT,opener=h).send("test")

    def test_no_untrusted_message(self):
        with self.assertRaisesRegex(TelegramHalt,"EVENT_NOT_ALLOWLISTED"):
            message_for({"kind":"UNKNOWN_TRADING_FILLED"})

    def test_signal_never_described_as_order(self):
        ev={"kind":"V5_SIGNAL_NOT_ORDER","lane":"SOL_CONVEX_1H",
            "symbol":"SOL_USDT","close_utc":"2026-10-15 08:00 UTC",
            "signal_id":"SOL_CONVEX_1H:1"}
        msg=message_for(ev)
        self.assertIn("NÃO É ORDEM",msg)
        self.assertIn("NÃO CONFIRMADA",msg)

    def test_real_broker_unsafe_account_warns(self):
        msg=message_for({"kind":"MEXC_PROTECTION_UNVERIFIED",
                         "checked_at_utc":"2026-10-15","positions":1,"orders":0,"stops":0})
        self.assertIn("PROTEÇÃO NÃO COMPROVADA",msg)


class TestDurableAlerts(TestCase):
    def test_duplicate_signal_id_outbox_deduped_after_restart(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td)
            ev={"kind":"SYSTEM_ONLINE"}
            q.enqueue("S",ev,1000)
            q.enqueue("S",ev,1100)
            self.assertEqual(q.pending_count(),1)
            bot=NoNetworkBot()
            self.assertEqual(q.drain(bot,1200),1)
            self.assertEqual(q.pending_count(),0)
            q.close()
            q2=DurableQueue(td)
            q2.enqueue("S",ev,1300)
            self.assertEqual(q2.drain(bot,1400),0)
            self.assertEqual(len(bot.messages),1)
            q2.close()

    def test_telegram_error_keeps_outbox_for_recovery(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td)
            q.enqueue("START",{"kind":"SYSTEM_ONLINE"},100)
            with self.assertRaises(TelegramHalt):
                q.drain(NoNetworkBot(fail=True),200)
            self.assertEqual(q.pending_count(),1)
            self.assertEqual(q.drain(NoNetworkBot(),300),1)
            q.close()

    def test_authenticated_flat_never_claims_entry(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td);bot=NoNetworkBot()
            with patch("engine.three_convex_v07.watch.account_inspect",return_value=flat()),\
                 patch("engine.three_convex_v07.watch.fresh_signals",return_value=[]):
                s=cycle(q,bot,account_client=Account(),
                    public_clock=lambda:1_002_000,
                    feed=lambda s,t,dir:object(),now_ms=1_002_000)
            self.assertTrue(s["account_flat_in_authenticated_snapshot"])
            self.assertTrue(s["v5_public_source_ok"])
            self.assertTrue(all("ordem executada" not in x.lower()
                                for x in bot.messages))
            self.assertFalse(s["real_order_submission_enabled"])
            q.close()

    def test_risk_alarm_only_when_authenticated_open_position_seen(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td);bot=NoNetworkBot()
            with patch("engine.three_convex_v07.watch.account_inspect",return_value=open_position()),\
                 patch("engine.three_convex_v07.watch.fresh_signals",return_value=[]):
                x=cycle(q,bot,account_client=Account(),
                        public_clock=lambda:2_000_000,
                        feed=lambda *a:[],now_ms=2_000_000)
            self.assertFalse(x["account_flat_in_authenticated_snapshot"])
            self.assertTrue(any("PROTEÇÃO NÃO COMPROVADA" in x for x in bot.messages))
            q.close()

    def test_both_sol_lanes_same_close_blocked(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td);bot=NoNetworkBot()
            sol=[fake_signal("SOL_CONVEX_NATIVE_5M"),
                 fake_signal("SOL_CONVEX_1H")]
            with patch("engine.three_convex_v07.watch.account_inspect",return_value=flat()),\
                 patch("engine.three_convex_v07.watch.fresh_signals",side_effect=[sol,[]]):
                cycle(q,bot,account_client=Account(),public_clock=lambda:1_000_000,
                      feed=lambda *a:[],now_ms=1_000_000)
            self.assertTrue(any("TWO_SOL_LONG_LANES_COLLIDE" in x for x in bot.messages))
            self.assertFalse(any("SINAL DETETADO" in x for x in bot.messages))
            q.close()

    def test_bnb_signal_is_observation_only(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td);bot=NoNetworkBot()
            sig=[fake_signal("BNB_CONVEX_4H","BNB_USDT")]
            with patch("engine.three_convex_v07.watch.account_inspect",return_value=flat()),\
                 patch("engine.three_convex_v07.watch.fresh_signals",side_effect=[[],sig]):
                cycle(q,bot,account_client=Account(),public_clock=lambda:1_000_000,
                      feed=lambda *a:[],now_ms=1_000_000)
            self.assertEqual(sum("SINAL DETETADO" in x for x in bot.messages),1)
            self.assertIn("NÃO É ORDEM",bot.messages[-1])
            q.close()

    def test_binance_source_failure_sends_warning_not_signal(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td);bot=NoNetworkBot()
            with patch("engine.three_convex_v07.watch.account_inspect",return_value=flat()):
                info=cycle(q,bot,account_client=Account(),
                    public_clock=lambda:1_000_000,
                    feed=lambda *a:(_ for _ in ()).throw(FeedHalt("NO_DATA")),
                    now_ms=1_000_000)
            self.assertFalse(info["v5_public_source_ok"])
            self.assertTrue(any("FONTE/BROKER BLOQUEADO" in x for x in bot.messages))
            q.close()

    def test_incomplete_account_read_warns_not_flat(self):
        with TemporaryDirectory() as td:
            q=DurableQueue(td);bot=NoNetworkBot()
            with patch("engine.three_convex_v07.watch.account_inspect",
                       return_value={"status":"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED"}),\
                 patch("engine.three_convex_v07.watch.fresh_signals",return_value=[]):
                info=cycle(q,bot,account_client=Account(),
                    public_clock=lambda:1_000_000,
                    feed=lambda *a:[],now_ms=1_000_000)
            self.assertFalse(info["account_flat_in_authenticated_snapshot"])
            self.assertTrue(any("ACCOUNT_OR_MARKET_READ_FAILED" in x for x in bot.messages))
            q.close()


if __name__=="__main__":
    import unittest
    unittest.main()
