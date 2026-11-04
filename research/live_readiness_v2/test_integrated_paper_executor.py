#!/usr/bin/env python3
"""Independent adverse tests for TWO durable ledgers and shared paper risk gate.

SQLite is the only 'broker' here. Child processes os._exit() to inject real
process crashes between the local and mock-broker commits. Not real fills.
"""
import concurrent.futures
from dataclasses import replace
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from risk_firewall import Account, Intent, Policy, Quote
from single_writer_recovery import GuardError
from integrated_paper_executor import PaperBroker, PaperCoordinator, live_enabled

NOW=2_000_000_000_000
SHA="a"*64


class PaperIntegratedFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.policy=Policy(strategy_sha=SHA)
        self.executor=PaperCoordinator(self.root,self.policy)
        self.addCleanup(self.executor.close)
        self.ticket=self.executor.claim(NOW)
        self.account=Account(equity="100",available_margin="100",
                   open_positions=0,unmatched_orders=0,verified_asof_ms=NOW)
        self.quote=Quote("BTC_USDT","99.99","100",NOW-100,NOW-50)
        self.intent=Intent(client_id="case-a",strategy_sha=SHA,symbol="BTC_USDT",
            side="LONG",contracts="0.01",contract_multiplier="1",
            step="0.01",minimum_contracts="0.01",tick="0.01",
            stop="99",signal_received_ms=NOW)
        self.executor.arm(NOW+1,self.account,human_approval=True,ttl_ms=8000)

    def paper_entry(self,*,intent=None,quote=None,account=None,now=NOW+2,
                    stop_result="ACK"):
        return self.executor.enter(now,intent or self.intent,
                                   quote or self.quote,account or self.account,
                                   stop_result=stop_result)

    def reject(self,code,action):
        with self.assertRaisesRegex(GuardError,code):
            action()

    def test_hard_disarmed_live(self):
        self.assertIs(live_enabled(),False)

    def test_strategy_preflight_real_old_class_used(self):
        self.assertEqual(self.executor.policy.digest,self.policy.digest)
        self.assertEqual(self.executor.firewall.state,"PAPER_ARMED")

    def test_complete_healthy_mock_entry_is_paper_protected(self):
        self.assertEqual(self.paper_entry(),"PAPER_PROTECTED_MOCK_ONLY")
        st=self.executor.status()
        self.assertEqual(st["custody"]["intents"][0]["state"],"PROTECTED")
        self.assertEqual(st["mock_broker"]["open_positions"],1)
        self.assertEqual(st["mock_broker"]["server_stops"],1)
        self.assertEqual(st["mock_broker"]["unprotected_positions"],0)

    def test_mock_human_flatten_closes_both_ledgers(self):
        self.paper_entry()
        self.executor.close_protected_paper(NOW+3,"case-a",human_approval=True)
        st=self.executor.status()
        self.assertEqual(st["custody"]["intents"][0]["state"],"CLOSED")
        self.assertTrue(st["mock_broker"]["is_flat"])

    def test_close_requires_human(self):
        self.paper_entry()
        self.reject("MOCK_FLATTEN_REQUIRES_OPERATOR",
                    lambda:self.executor.close_protected_paper(
                        NOW+3,"case-a",human_approval=False))
        self.assertEqual(self.executor.status()["mock_broker"]["open_positions"],1)

    def test_replay_id_after_closed_never_second_simulated_fill(self):
        self.paper_entry()
        self.executor.close_protected_paper(NOW+3,"case-a",human_approval=True)
        self.reject("DUPLICATE_INTENT_PERSISTENT",
                    lambda:self.paper_entry(now=NOW+4))
        self.assertEqual(self.executor.broker.snapshot()["mock_receipts"],3)

    def test_two_signals_cannot_create_two_physical_positions(self):
        self.paper_entry()
        other=replace(self.intent,client_id="case-b")
        self.reject("ANOTHER_POSITION_OR_ORDER_PENDING",
                    lambda:self.paper_entry(intent=other,now=NOW+3))
        self.assertEqual(len(self.executor.broker.snapshot()["orders"]),1)

    def test_stale_quote_rejected_before_reserve_and_broker(self):
        old=replace(self.quote,published_ms=NOW-6000)
        self.assertEqual(self.paper_entry(quote=old),"REJECT_RISK:QUOTE_PUBLISHER_STALE")
        self.assertEqual(self.executor.status()["custody"]["intents"],[])
        self.assertEqual(self.executor.broker.snapshot()["orders"],[])

    def test_stale_account_rejected_before_reserve(self):
        stale=replace(self.account,verified_asof_ms=NOW-5000)
        self.assertEqual(self.paper_entry(account=stale),"REJECT_RISK:ACCOUNT_SNAPSHOT_STALE")
        self.assertEqual(self.executor.broker.snapshot()["orders"],[])

    def test_risk_over_budget_rejected_before_reserve(self):
        bad=replace(self.intent,stop="50")
        self.assertEqual(self.paper_entry(intent=bad),"REJECT_RISK:PER_TRADE_RISK_TOO_LARGE")
        self.assertFalse(self.executor.status()["custody"]["intents"])

    def test_no_hypothetical_server_stop_ack_freezes_and_preserves_exposure(self):
        self.assertEqual(self.paper_entry(stop_result="REJECTED"),
                         "FROZEN_MOCK_UNPROTECTED")
        st=self.executor.status()
        self.assertEqual(st["custody"]["phase"],"FROZEN_RECOVERY_REQUIRED")
        self.assertEqual(st["mock_broker"]["unprotected_positions"],1)
        self.reject("NOT_PAPER_ARMED",lambda:self.paper_entry(
                     intent=replace(self.intent,client_id="extra"),now=NOW+3))

    def test_mock_broker_rejects_duplicate_id_even_if_called_directly(self):
        self.paper_entry()
        self.reject("MOCK_BROKER_DUPLICATE_CLIENT_ID",
                    lambda:self.executor.broker.accept_paper_entry(self.intent,NOW+3))

    def test_mock_broker_rejects_more_than_one_open_position(self):
        self.paper_entry()
        two=replace(self.intent,client_id="other")
        self.reject("MOCK_BROKER_EXISTING_POSITION",
                    lambda:self.executor.broker.accept_paper_entry(two,NOW+3))

    def test_mock_stop_volume_mismatch_cannot_claim_ack(self):
        self.executor.broker.accept_paper_entry(self.intent,NOW+2)
        self.reject("MOCK_STOP_QTY_OR_PRICE_MISMATCH",
                    lambda:self.executor.broker.ack_paper_stop(
                          "case-a","0.02","99",NOW+3))
        self.assertEqual(self.executor.broker.snapshot()["unprotected_positions"],1)

    def test_hard_daily_loss_persists_and_blocks_new_entries(self):
        res=self.executor.record_loss(NOW+2,self.account,"1","1")
        self.assertTrue(res["locked"])
        self.assertTrue(self.executor.status()["custody"]["hard_lock"])
        self.assertFalse(self.executor.broker.snapshot()["orders"])
        self.reject("PERSISTENT_HARD_LOCK",
                    lambda:self.executor.custody.claim(NOW+30001))

    def test_hard_weekly_loss_persists(self):
        self.assertTrue(self.executor.record_loss(NOW+2,self.account,"0.2","3")["locked"])
        self.assertEqual(self.executor.status()["custody"]["phase"],"FROZEN_PAPER_LOSS")

    def test_zero_loss_does_not_decrease_saved_highwater(self):
        first=self.executor.record_loss(NOW+2,self.account,"0.7","1.2")
        self.assertFalse(first["locked"])
        second=self.executor.record_loss(NOW+3,self.account,"0.1","0.1")
        self.assertEqual(second["daily"],"0.7")
        self.assertEqual(second["weekly"],"1.2")

    def test_equity_fall_can_trigger_lock_without_new_loss(self):
        self.executor.record_loss(NOW+2,self.account,"0.7","1")
        smaller=replace(self.account,equity="50",available_margin="50",
                        verified_asof_ms=NOW+3)
        locked=self.executor.record_loss(NOW+4,smaller,"0","0")
        self.assertTrue(locked["locked"])

    def test_mock_broker_orphan_not_in_custody_refuses_reconciliation(self):
        ghost=replace(self.intent,client_id="ghost")
        self.executor.broker.accept_paper_entry(ghost,NOW+2)
        self.executor.custody.disarm(self.ticket,NOW+3)
        # The running owner cannot claim until its lease expires.
        other=PaperCoordinator(self.root,self.policy)
        try:
            other.claim(NOW+30001)
            self.reject("MOCK_BROKER_ORPHAN_NOT_IN_CUSTODY",
                        lambda:other.reconcile_paper(NOW+30002,human_approval=True))
        finally:other.close()

    def test_audit_snapshot_after_paper_entry(self):
        self.paper_entry()
        self.assertGreaterEqual(self.executor.custody.verify_audit(),5)
        self.assertEqual(self.executor.status()["custody"]["paper_risk"]["equity"],"100")

    def test_prevent_unapproved_reconcile(self):
        self.paper_entry(stop_result="REJECTED")
        self.reject("HUMAN_APPROVAL_REQUIRED",
                    lambda:self.executor.reconcile_paper(NOW+3,human_approval=False))

    def test_broker_active_prevents_reconcile_even_with_human_true(self):
        self.paper_entry(stop_result="REJECTED")
        self.reject("MOCK_BROKER_NOT_FLAT_UNSAFE_RECONCILIATION",
                    lambda:self.executor.reconcile_paper(NOW+3,human_approval=True))


class RecoveryAndRestart(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.policy=Policy(strategy_sha=SHA)
        self.env=dict(os.environ)
        module_dir=str(Path(__file__).resolve().parent)
        self.env["PYTHONPATH"]=module_dir+os.pathsep+self.env.get("PYTHONPATH","")

    def child(self,point):
        script="""import sys
from risk_firewall import Account,Quote,Intent,Policy
from integrated_paper_executor import PaperCoordinator
now=2000000000000
co=PaperCoordinator(sys.argv[1],Policy(strategy_sha='a'*64))
co.claim(now)
acc=Account('100','100',0,0,now)
q=Quote('BTC_USDT','99.99','100',now-100,now-50)
i=Intent('crash-intent','a'*64,'BTC_USDT','LONG','0.01','1','0.01','0.01','0.01','99',now)
co.arm(now+1,acc,human_approval=True,ttl_ms=8000)
co.enter(now+2,i,q,acc,fault_at=sys.argv[2])
raise SystemExit('CRASH_INJECTION_DID_NOT_EXIT')
"""
        p=subprocess.run([sys.executable,"-c",script,str(self.root),point],
                         env=self.env,stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,text=True,timeout=30)
        return p

    def resume_frozen(self):
        co=PaperCoordinator(self.root,self.policy)
        co.claim(NOW+30001)
        self.assertEqual(co.status()["custody"]["phase"],"FROZEN_RECOVERY_REQUIRED")
        return co

    def test_crash_after_reserve_but_before_broker_side_effect(self):
        p=self.child("AFTER_RESERVATION")
        self.assertEqual(p.returncode,41,p.stderr)
        recovered=self.resume_frozen()
        try:
            self.assertEqual(recovered.status()["custody"]["intents"][0]["state"],"PENDING")
            self.assertEqual(recovered.broker.snapshot()["orders"],[])
            recovered.reconcile_paper(NOW+30002,human_approval=True)
            self.assertEqual(recovered.status()["custody"]["intents"][0]["state"],"CANCELLED")
            self.assertEqual(recovered.status()["custody"]["phase"],"DISARMED")
            # Even though this client_id was never sent, do not automatically retry.
            acc=Account('100','100',0,0,NOW+30003)
            q=Quote("BTC_USDT","99.99","100",NOW+29900,NOW+30001)
            i=Intent("crash-intent",SHA,"BTC_USDT","LONG","0.01","1",
                     "0.01","0.01","0.01","99",NOW+30001)
            recovered.arm(NOW+30003,acc,human_approval=True,ttl_ms=1000)
            with self.assertRaisesRegex(GuardError,"DUPLICATE_INTENT_PERSISTENT"):
                recovered.enter(NOW+30004,i,q,acc)
        finally:recovered.close()

    def test_crash_after_broker_fill_before_local_receipt(self):
        p=self.child("AFTER_BROKER_FILL")
        self.assertEqual(p.returncode,42,p.stderr)
        recovered=self.resume_frozen()
        try:
            st=recovered.status()
            self.assertEqual(st["custody"]["intents"][0]["state"],"PENDING")
            self.assertEqual(st["mock_broker"]["unprotected_positions"],1)
            with self.assertRaisesRegex(GuardError,"MOCK_BROKER_NOT_FLAT_UNSAFE_RECONCILIATION"):
                recovered.reconcile_paper(NOW+30002,human_approval=True)
            recovered.broker.human_mock_flatten("crash-intent",NOW+30003,human_approval=True)
            recovered.reconcile_paper(NOW+30004,human_approval=True)
            self.assertEqual(recovered.status()["custody"]["intents"][0]["state"],"CLOSED")
            self.assertEqual(recovered.broker.snapshot()["open_positions"],0)
        finally:recovered.close()

    def test_crash_after_broker_stop_ack_before_local_receipt(self):
        p=self.child("AFTER_BROKER_STOP_ACK")
        self.assertEqual(p.returncode,43,p.stderr)
        recovered=self.resume_frozen()
        try:
            st=recovered.status()
            self.assertEqual(st["custody"]["intents"][0]["state"],"FILLED_UNPROTECTED")
            self.assertEqual(st["mock_broker"]["server_stops"],1)
            with self.assertRaisesRegex(GuardError,"MOCK_BROKER_NOT_FLAT_UNSAFE_RECONCILIATION"):
                recovered.reconcile_paper(NOW+30002,human_approval=True)
            recovered.broker.human_mock_flatten("crash-intent",NOW+30003,human_approval=True)
            recovered.reconcile_paper(NOW+30004,human_approval=True)
            self.assertEqual(recovered.status()["custody"]["intents"][0]["state"],"CLOSED")
        finally:recovered.close()

    def test_hard_risk_lock_survives_worker_crash(self):
        script="""import os,sys
from risk_firewall import Account,Policy
from integrated_paper_executor import PaperCoordinator
now=2000000000000
co=PaperCoordinator(sys.argv[1],Policy(strategy_sha='a'*64))
co.claim(now)
acc=Account('100','100',0,0,now)
co.arm(now+1,acc,human_approval=True,ttl_ms=8000)
co.record_loss(now+2,acc,'1','1')
os._exit(44)
"""
        p=subprocess.run([sys.executable,"-c",script,str(self.root)],
                         env=self.env,capture_output=True,text=True,timeout=30)
        self.assertEqual(p.returncode,44,p.stderr)
        new=PaperCoordinator(self.root,self.policy)
        try:
            with self.assertRaisesRegex(GuardError,"PERSISTENT_HARD_LOCK"):
                new.claim(NOW+30001)
        finally:new.close()


if __name__=="__main__":
    unittest.main(verbosity=2)
