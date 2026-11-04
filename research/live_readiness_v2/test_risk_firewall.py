#!/usr/bin/env python3
"""Deterministic fault-injection tests. No exchange/HTTP/credentials needed."""
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from risk_firewall import (Account, BrokerScenario, Firewall, HashJournal,
                           Intent, Policy, Quote, Rejected, live_enabled, D)

SHA = "a" * 64
OTHER = "b" * 64
NOW = 2_000_000_000_000


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "journal.ndjson"
        self.policy = Policy(strategy_sha=SHA)
        self.engine = Firewall(self.policy, HashJournal(self.path))
        self.quote = Quote(symbol="BTC_USDT", bid="99.99", ask="100", published_ms=NOW-100, received_ms=NOW-50)
        self.account = Account(equity="100", available_margin="100", open_positions=0,
                               unmatched_orders=0, verified_asof_ms=NOW-50)
        self.intent = Intent(client_id="a1",strategy_sha=SHA,symbol="BTC_USDT",side="LONG",
                             contracts="0.01",contract_multiplier="1",step="0.01",
                             minimum_contracts="0.01",tick="0.01",stop="99",
                             signal_received_ms=NOW-100)
        self.ok = BrokerScenario()
        self.engine.arm_paper(NOW, 120_000, self.policy.digest, SHA, True)

    def result(self, *, intent=None,quote=None,account=None,scenario=None,now=None):
        return self.engine.simulate(intent or self.intent,quote or self.quote,
                                    account or self.account,scenario or self.ok,
                                    NOW if now is None else now)

    def rejects(self, key, **kwargs):
        out = self.result(**kwargs)
        self.assertEqual(out, "REJECT:"+key, out)
        return out


class HappyPath(Fixture):
    def test_paper_protected_happy_path(self):
        self.assertEqual(self.result(), "PAPER_PROTECTED")
        self.assertEqual(self.engine.state,"PAPER_PROTECTED")
        self.assertEqual(len(HashJournal.verify(self.path)), 4) # arm,intent,fill,stop
    def test_disarmed_on_start(self):
        other=Firewall(self.policy,HashJournal(Path(self.tmp.name)/"empty.ndjson"))
        self.assertEqual(other.state,"DISARMED")
    def test_hard_live_disabled(self):
        self.assertFalse(live_enabled())
    def test_positions_single_physical(self):
        self.result()
        second=replace(self.intent,client_id="a2")
        self.rejects("NOT_PAPER_ARMED",intent=second)
    def test_short_eligible_with_correct_stop(self):
        intent=replace(self.intent,side="SHORT",stop="101")
        self.assertEqual(self.result(intent=intent),"PAPER_PROTECTED")
    def test_hash_journal_integrity(self):
        self.result()
        rows=HashJournal.verify(self.path)
        self.assertEqual(rows[-1]["event"],"PAPER_STOP_ACK")
        self.assertEqual(rows[1]["data"]["policy_sha"],self.policy.digest)


class AuthorizationAndInputs(Fixture):
    def test_reject_expired_session(self):
        self.rejects("SESSION_EXPIRED",now=NOW+120_000)
    def test_reject_duplicate_id_after_entry_rejection(self):
        self.assertEqual(self.result(scenario=replace(self.ok,entry="REJECTED")),"ENTRY_REJECTED")
        self.rejects("DUPLICATE_INTENT")
    def test_foreign_strategy(self):
        self.rejects("FOREIGN_STRATEGY",intent=replace(self.intent,strategy_sha=OTHER))
    def test_foreign_symbol(self):
        self.rejects("FOREIGN_SYMBOL",intent=replace(self.intent,symbol="ETH_USDT"))
    def test_invalid_side(self):
        self.rejects("INVALID_DIRECTION",intent=replace(self.intent,side="BOTH"))
    def test_signal_late(self):
        self.rejects("SIGNAL_STALE",intent=replace(self.intent,signal_received_ms=NOW-1501))
    def test_missing_lot_step(self):
        self.rejects("MIN_CONTRACT_OR_STEP",intent=replace(self.intent,contracts="0.015"))
    def test_contract_min_too_big(self):
        self.rejects("MIN_CONTRACT_OR_STEP",intent=replace(self.intent,minimum_contracts="1"))
    def test_stop_wrong_side(self):
        self.rejects("STOP_WRONG_SIDE_OR_CROSSED",intent=replace(self.intent,stop="101"))
    def test_stop_bad_tick(self):
        self.rejects("INVALID_STOP_TICK",intent=replace(self.intent,stop="99.005"))
    def test_nan_quantity(self):
        self.rejects("NONFINITE_DECIMAL",intent=replace(self.intent,contracts="NaN"))
    def test_negative_contract(self):
        self.rejects("INVALID_CONTRACT_SPEC",intent=replace(self.intent,contracts="-1"))
    def test_crossed_quote(self):
        self.rejects("CROSSED_OR_INVALID_BOOK",quote=replace(self.quote,bid="101"))
    def test_stale_exchange_quote(self):
        self.rejects("QUOTE_PUBLISHER_STALE",quote=replace(self.quote,published_ms=NOW-3000))
    def test_stale_local_receipt(self):
        self.rejects("QUOTE_RECEIPT_STALE",quote=replace(self.quote,received_ms=NOW-2000,published_ms=NOW-2100))
    def test_quote_future(self):
        self.rejects("QUOTE_PUBLISHER_STALE",quote=replace(self.quote,published_ms=NOW+1000))
    def test_unmatched_orders(self):
        self.rejects("UNRECONCILED_BROKER_ORDERS",account=replace(self.account,unmatched_orders=1))
    def test_open_positions(self):
        self.rejects("PREEXISTING_POSITION_BLOCK",account=replace(self.account,open_positions=1))
    def test_account_stale(self):
        self.rejects("ACCOUNT_SNAPSHOT_STALE",account=replace(self.account,verified_asof_ms=NOW-3000))
    def test_bad_account_balance(self):
        self.rejects("ACCOUNT_BALANCE_INVALID",account=replace(self.account,equity="0"))
    def test_nonmock_account_rejected(self):
        self.rejects("NON_MOCK_ACCOUNT_NOT_SUPPORTED",account=replace(self.account,synthetic_fixture=False))
    def test_wrong_account_mode(self):
        self.rejects("NETTING_MODE_UNCERTIFIED",account=replace(self.account,one_way_mode=False))
    def test_oversized_stop_loss_budget(self):
        self.rejects("PER_TRADE_RISK_TOO_LARGE",intent=replace(self.intent,stop="70"))
    def test_margin_insufficient_without_assumed_leverage(self):
        self.rejects("INSUFFICIENT_UNLEVERED_MARGIN",account=replace(self.account,available_margin="0.5"))
    def test_max_ttl_policy_fails(self):
        with self.assertRaisesRegex(Rejected,"UNSAFE_SESSION_TTL"):
            Policy(strategy_sha=SHA,max_session_ms=7_200_001)
    def test_unsafe_multi_position_policy_fails(self):
        with self.assertRaisesRegex(Rejected,"MULTI_POSITION_NOT_CERTIFIED"):
            Policy(strategy_sha=SHA,max_positions=3)
    def test_policy_strategys_hash_fails(self):
        with self.assertRaisesRegex(Rejected,"INVALID_STRATEGY_SHA"):
            Policy(strategy_sha="short")
    def test_policy_ratio_fails(self):
        with self.assertRaisesRegex(Rejected,"INVALID_LIMIT_ORDER"):
            Policy(strategy_sha=SHA,per_trade_fraction="0.6",aggregate_fraction="0.5")


class SessionSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.policy=Policy(strategy_sha=SHA)
        self.fw=Firewall(self.policy,HashJournal(Path(self.tmp.name)/"j.ndjson"))
    def test_arm_denied_without_human_approval(self):
        with self.assertRaisesRegex(Rejected,"HUMAN_APPROVAL_REQUIRED"):
            self.fw.arm_paper(NOW,120000,self.policy.digest,SHA,False)
        self.assertEqual(self.fw.state,"DISARMED")
    def test_wrong_policy_hash(self):
        with self.assertRaisesRegex(Rejected,"POLICY_HASH_MISMATCH"):
            self.fw.arm_paper(NOW,120000,"x"*64,SHA,True)
    def test_wrong_sha(self):
        with self.assertRaisesRegex(Rejected,"STRATEGY_HASH_MISMATCH"):
            self.fw.arm_paper(NOW,120000,self.policy.digest,OTHER,True)
    def test_overlong_arm(self):
        with self.assertRaisesRegex(Rejected,"TTL_INVALID"):
            self.fw.arm_paper(NOW,8_000_000,self.policy.digest,SHA,True)
    def test_disarm_prevents_rearm_without_fresh_context(self):
        self.fw.arm_paper(NOW,120000,self.policy.digest,SHA,True)
        self.fw.disarm("Telegram offline")
        self.assertEqual(self.fw.state,"DISARMED")
        self.assertFalse(live_enabled())
    def test_restart_freezes_even_with_valid_paper_journal(self):
        self.fw.arm_paper(NOW,120000,self.policy.digest,SHA,True)
        restarted=Firewall(self.policy,HashJournal(self.fw.journal.path))
        self.assertEqual(restarted.state,"FROZEN_RECONCILIATION_REQUIRED")
        with self.assertRaisesRegex(Rejected,"NOT_DISARMED"):
            restarted.arm_paper(NOW,120000,self.policy.digest,SHA,True)
    def test_tamper_detected(self):
        self.fw.arm_paper(NOW,120000,self.policy.digest,SHA,True)
        s=self.fw.journal.path.read_text()
        self.fw.journal.path.write_text(s.replace("PAPER_ARM","LIVE_ARM"))
        with self.assertRaisesRegex(Rejected,"JOURNAL_HASH_MISMATCH"):
            HashJournal(self.fw.journal.path)
    def test_nonexistent_folder_does_not_arm(self):
        fw=Firewall(self.policy,HashJournal(Path(self.tmp.name)/"missing"/"j.ndjson"))
        with self.assertRaisesRegex(Rejected,"JOURNAL_WRITE_FAILED"):
            fw.arm_paper(NOW,120000,self.policy.digest,SHA,True)
        self.assertEqual(fw.state,"FROZEN_JOURNAL_FAILURE")


class BrokerFailureInjection(Fixture):
    def test_entry_clean_reject_no_position(self):
        self.assertEqual(self.result(scenario=replace(self.ok,entry="REJECTED")),"ENTRY_REJECTED")
        self.assertEqual(self.engine.state,"PAPER_ARMED")
        self.assertFalse(self.engine.active)
    def test_entry_timeout_freezes(self):
        self.assertEqual(self.result(scenario=replace(self.ok,entry="TIMEOUT")),"FROZEN_ENTRY_UNKNOWN")
        self.assertEqual(self.engine.state,"FROZEN_BROKER_UNKNOWN")
    def test_entry_unknown_status_freezes(self):
        self.assertEqual(self.result(scenario=replace(self.ok,entry="DUPLICATE")),"FROZEN_ENTRY_UNKNOWN")
    def test_partial_fill_with_matching_stop_ack(self):
        self.assertEqual(self.result(scenario=replace(self.ok,entry="PARTIAL",
                                                     filled_contracts="0.005")),"PAPER_PROTECTED")
        self.assertEqual(self.engine.active["filled_contracts"],"0.005")
    def test_partial_fill_without_stop_freezes(self):
        scenario=replace(self.ok,entry="PARTIAL",filled_contracts="0.005",stop="TIMEOUT")
        self.assertEqual(self.result(scenario=scenario),"FROZEN_FLATTEN_ACK")
    def test_full_fill_wrong_quantity_freezes(self):
        self.assertEqual(self.result(scenario=replace(self.ok,filled_contracts="0.02")),
                         "FROZEN_FILL_MISMATCH")
    def test_stop_rejected_and_emergency_flatten_ack(self):
        s=replace(self.ok,stop="REJECTED",flatten="ACK")
        self.assertEqual(self.result(scenario=s),"FROZEN_FLATTEN_ACK")
        self.assertFalse(self.engine.active)
        self.assertEqual(self.engine.state,"FROZEN_AFTER_EMERGENCY_FLATTEN")
    def test_stop_timeout_and_flatten_timeout_unknown_exposure(self):
        s=replace(self.ok,stop="TIMEOUT",flatten="TIMEOUT")
        self.assertEqual(self.result(scenario=s),"FROZEN_EXPOSURE_UNKNOWN")
        self.assertIsNotNone(self.engine.active)
        self.rejects("NOT_PAPER_ARMED",intent=replace(self.intent,client_id="other"))
    def test_stop_wrong_size_freezes(self):
        self.assertEqual(self.result(scenario=replace(self.ok,stop="WRONG_QTY")),"FROZEN_FLATTEN_ACK")
    def test_stop_wrong_direction_freezes(self):
        self.assertEqual(self.result(scenario=replace(self.ok,stop="WRONG_SIDE")),"FROZEN_FLATTEN_ACK")
    def test_stop_weaker_freezes(self):
        self.assertEqual(self.result(scenario=replace(self.ok,stop="WEAKER")),"FROZEN_FLATTEN_ACK")
    def test_no_rearm_on_uncertain_exposure(self):
        self.result(scenario=replace(self.ok,stop="REJECTED",flatten="TIMEOUT"))
        with self.assertRaisesRegex(Rejected,"NOT_DISARMED"):
            self.engine.arm_paper(NOW,120000,self.policy.digest,SHA,True)
    def test_reconcile_requires_human(self):
        self.result(scenario=replace(self.ok,stop="REJECTED",flatten="TIMEOUT"))
        with self.assertRaisesRegex(Rejected,"RECONCILIATION_PROOF_MISSING"):
            self.engine.reconcile_flat(paper_broker_flat=True,human_approval=False)
        self.assertTrue(self.engine.state.startswith("FROZEN"))
    def test_reconcile_requires_flat(self):
        self.result(scenario=replace(self.ok,stop="REJECTED",flatten="TIMEOUT"))
        with self.assertRaisesRegex(Rejected,"RECONCILIATION_PROOF_MISSING"):
            self.engine.reconcile_flat(paper_broker_flat=False,human_approval=True)
    def test_reconcile_flat_requires_new_arm(self):
        self.result(scenario=replace(self.ok,stop="REJECTED",flatten="TIMEOUT"))
        self.engine.reconcile_flat(paper_broker_flat=True,human_approval=True)
        self.assertEqual(self.engine.state,"DISARMED")
        self.rejects("NOT_PAPER_ARMED",intent=replace(self.intent,client_id="other"))
    def test_daily_loss_freeze(self):
        self.engine.loss_mark("1","1",NOW,"100")
        self.assertEqual(self.engine.state,"FROZEN_LOSS_LIMIT")
        self.rejects("NOT_PAPER_ARMED")
    def test_weekly_loss_freeze(self):
        self.engine.loss_mark("0","3",NOW,"100")
        self.assertEqual(self.engine.state,"FROZEN_LOSS_LIMIT")
    def test_disarm_cannot_clear_loss_freeze(self):
        self.engine.loss_mark("1","1",NOW,"100")
        self.engine.disarm("operator attempted reset")
        self.assertEqual(self.engine.state,"FROZEN_LOSS_LIMIT")
        with self.assertRaisesRegex(Rejected,"NOT_DISARMED"):
            self.engine.arm_paper(NOW,120000,self.policy.digest,SHA,True)
    def test_disarm_cannot_clear_unknown_broker_freeze(self):
        self.result(scenario=replace(self.ok,entry="TIMEOUT"))
        self.engine.disarm("operator attempted reset")
        self.assertEqual(self.engine.state,"FROZEN_BROKER_UNKNOWN")

    def test_under_daily_limit_no_freeze(self):
        self.engine.loss_mark("0.9","1.1",NOW,"100")
        self.assertEqual(self.engine.state,"PAPER_ARMED")
    def test_disarm_after_protection_requires_reconcile(self):
        self.result()
        self.engine.disarm("operator STOP")
        self.assertEqual(self.engine.state,"FROZEN_POSITION_NEEDS_RECONCILIATION")
        self.rejects("NOT_PAPER_ARMED",intent=replace(self.intent,client_id="later"))
    def test_stop_risk_not_only_distance(self):
        self.assertEqual(self.result(),"PAPER_PROTECTED")
        records=HashJournal.verify(self.path)
        risk=D(records[1]["data"]["risk_cash"])
        self.assertGreater(risk, D("0.01"))  # includes all configured fees/slippage/funding


if __name__ == "__main__":
    unittest.main(verbosity=2)
