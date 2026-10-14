"""Protocol mock tests — offline, NO real account, NO real stop ACK."""
from dataclasses import replace
from tempfile import TemporaryDirectory
import unittest

from engine.three_convex_v05.broker_protocol import (
    AccountView,PositionReceipt,StopReceipt,DurableIntent,
    BrokerGateRejected,check_account,validate_filled_stop,
)


def account():
    return AccountView(equity="100",open_position_count=0,
            open_order_count=0,position_mode="HEDGE",
            margin_mode="ISOLATED",leverage=10,auto_margin_add=False,
            authenticated=True,observed_at_ms=10_000,
            user_fee_taker_bps="8",maintenance_margin_rate=".005")


def position():
    return PositionReceipt("SOL_USDT","LONG","test:123",1,
                           "100",10_000,"AUTHENTICATED_EXCHANGE_READ")


def stop():
    return StopReceipt("SOL_USDT","LONG","test:123",1,
                       "96","MARK_PRICE","test:stop123",True,"ACTIVE_UNTRIGGERED",
                       10_002,"AUTHENTICATED_EXCHANGE_READ",10_001,10_003)


class TestAccountGate(unittest.TestCase):
    def test_structurally_correct_sample_not_real_authority(self):
        r=check_account(account(),10_004)
        self.assertTrue(r["this_does_not_authorize_trading"])

    def test_position_mode_mismatch(self):
        with self.assertRaisesRegex(BrokerGateRejected,"MISMATCHED"):
            check_account(replace(account(),position_mode="ONE_WAY"),10_004)

    def test_untrusted_provenance(self):
        with self.assertRaisesRegex(BrokerGateRejected,"NO_AUTHENTICATED"):
            check_account(replace(account(),authenticated=False),10_004)

    def test_stale_account(self):
        with self.assertRaisesRegex(BrokerGateRejected,"STALE"):
            check_account(account(),20_000)

    def test_existing_position_halts(self):
        with self.assertRaisesRegex(BrokerGateRejected,"EXISTING"):
            check_account(replace(account(),open_position_count=1),10_001)

    def test_existing_order_halts(self):
        with self.assertRaisesRegex(BrokerGateRejected,"EXISTING"):
            check_account(replace(account(),open_order_count=1),10_001)

    def test_wrong_leverage_halts(self):
        with self.assertRaisesRegex(BrokerGateRejected,"MISMATCHED"):
            check_account(replace(account(),leverage=5),10_001)

    def test_cross_mode_halts(self):
        with self.assertRaisesRegex(BrokerGateRejected,"MISMATCHED"):
            check_account(replace(account(),margin_mode="CROSS"),10_001)

    def test_auto_margin_halts(self):
        with self.assertRaisesRegex(BrokerGateRejected,"MISMATCHED"):
            check_account(replace(account(),auto_margin_add=True),10_001)

    def test_fee_unproven_halts(self):
        with self.assertRaisesRegex(BrokerGateRejected,"UNVERIFIED_FEE"):
            check_account(replace(account(),user_fee_taker_bps="-1"),10_001)


class TestStopAck(unittest.TestCase):
    def test_matching_fake_receipts_do_not_grant_live_go(self):
        r=validate_filled_stop(position(),stop(),10_004)
        self.assertEqual(r["live_authority"],"NONE")
        self.assertTrue(r["source_assumed_not_independently_authenticated"])

    def test_initial_ack_without_later_broker_readback_is_not_protection(self):
        with self.assertRaisesRegex(BrokerGateRejected,"MISSING_INDEPENDENT"):
            validate_filled_stop(position(),replace(stop(),readback_at_ms=10_001),10_004)

    def test_wrong_position_identity(self):
        with self.assertRaisesRegex(BrokerGateRejected,"DOES_NOT_MATCH"):
            validate_filled_stop(position(),replace(stop(),position_id="other"),10_004)

    def test_wrong_symbol(self):
        with self.assertRaisesRegex(BrokerGateRejected,"DOES_NOT_MATCH"):
            validate_filled_stop(position(),replace(stop(),symbol="BNB_USDT"),10_004)

    def test_protected_quantity_short(self):
        pos=replace(position(),volume_contracts=2)
        with self.assertRaisesRegex(BrokerGateRejected,"COVER"):
            validate_filled_stop(pos,stop(),10_004)

    def test_stop_missing_reduce_only(self):
        with self.assertRaisesRegex(BrokerGateRejected,"NOT_ACCEPTED"):
            validate_filled_stop(position(),replace(stop(),reduce_only=False),10_004)

    def test_stop_ack_rejected(self):
        with self.assertRaisesRegex(BrokerGateRejected,"NOT_ACCEPTED"):
            validate_filled_stop(position(),replace(stop(),status="PENDING"),10_004)

    def test_stop_trigger_type_wrong(self):
        with self.assertRaisesRegex(BrokerGateRejected,"NOT_ACCEPTED"):
            validate_filled_stop(position(),replace(stop(),trigger_type="LAST_PRICE"),10_004)

    def test_stale_stop(self):
        with self.assertRaisesRegex(BrokerGateRejected,"STALE"):
            validate_filled_stop(position(),stop(),17_100)

    def test_source_not_independently_authenticated(self):
        with self.assertRaisesRegex(BrokerGateRejected,"UNVERIFIED_BROKER"):
            validate_filled_stop(position(),replace(stop(),source="SYNTHETIC"),10_004)

    def test_both_tighter_and_looser_stop_rejected(self):
        for s in ("95","97"):
            with self.subTest(stop=s):
                with self.assertRaisesRegex(BrokerGateRejected,"FOUR_PERCENT"):
                    validate_filled_stop(position(),replace(stop(),stop_price=s),10_004)


class TestPersistence(unittest.TestCase):
    def test_reserve_once_and_unknown_restart_fails_closed(self):
        with TemporaryDirectory() as d:
            i=DurableIntent(d)
            i.reserve("SOL:1500",{"symbol":"SOL_USDT","lane":"SOL_CONVEX_NATIVE_5M","risk_usdt":"0.45"})
            with self.assertRaisesRegex(BrokerGateRejected,"ALREADY_RESERVED"):
                i.reserve("SOL:1500",{"symbol":"SOL_USDT"})
            self.assertEqual(i.recover("SOL:1500")["state"],"UNKNOWN_EXCHANGE_STATE_NO_RESEND")

    def test_cannot_use_key_in_journal(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(BrokerGateRejected,"ALLOWLISTED"):
                DurableIntent(d).reserve("SOL:123",{"MEXC_API_SECRET":"never"})

    def test_unseen_id_not_false_empty_account(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(BrokerGateRejected,"MISSING_INTENT"):
                DurableIntent(d).recover("NOT_A_REAL_POSITION")


if __name__=="__main__":
    unittest.main()
