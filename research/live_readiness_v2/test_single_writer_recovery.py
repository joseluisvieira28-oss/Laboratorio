#!/usr/bin/env python3
"""Attack SQLite single-writer/recovery rules with separate connections and crash injection."""
import concurrent.futures
import os
import subprocess
import sys
from pathlib import Path
import sqlite3
import tempfile
import unittest
from dataclasses import replace

from single_writer_recovery import GuardError, PaperFencedStore, live_enabled

NOW=2000000000000
POLICY="1"*64
STRATEGY="2"*64


class PaperFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"one_writer.sqlite"
        self.store=PaperFencedStore(self.path)
        self.addCleanup(self.store.close)
        self.ticket=self.store.claim(NOW)

    def arm(self, now=NOW+1):
        self.store.arm_paper(self.ticket,now,human_approval=True,
                             policy_sha=POLICY,strategy_sha=STRATEGY,ttl_ms=10000)

    def reject(self, text, fn):
        with self.assertRaisesRegex(GuardError,text):
            fn()

    def test_hard_no_live_adapter(self):
        self.assertIs(live_enabled(),False)

    def test_initial_disarmed_with_epoch(self):
        s=self.store.inspect()
        self.assertEqual(s["phase"],"DISARMED")
        self.assertEqual(s["epoch"],1)

    def test_claim_second_connection_denied(self):
        other=PaperFencedStore(self.path)
        try:self.reject("LEASE_HELD_BY_OTHER",lambda:other.claim(NOW+1))
        finally:other.close()

    def test_new_claim_after_expiry_requires_reconciliation(self):
        second=PaperFencedStore(self.path)
        try:
            ticket2=second.claim(NOW+30001)
            self.assertEqual(ticket2.epoch,2)
            self.assertEqual(second.inspect()["phase"],"FROZEN_RECOVERY_REQUIRED")
            self.reject("RECOVERY_OR_FREEZE_BLOCK",lambda:second.arm_paper(
                ticket2,NOW+30002,human_approval=True,
                policy_sha=POLICY,strategy_sha=STRATEGY))
        finally:second.close()

    def test_expired_ticket_cannot_renew(self):
        self.reject("LEASE_EXPIRED",lambda:self.store.renew(self.ticket,NOW+30000))

    def test_lease_renew_extends_fence(self):
        self.store.renew(self.ticket,NOW+10000)
        self.store.renew(self.ticket,NOW+35000)
        self.assertEqual(self.store.inspect()["lease_until_ms"],NOW+65000)

    def test_old_epoch_rejected_after_takeover(self):
        second=PaperFencedStore(self.path)
        try:
            second.claim(NOW+30001)
            self.reject("STALE_FENCING_TOKEN",lambda:self.store.renew(
                self.ticket,NOW+30002))
        finally:second.close()

    def test_bad_lease_duration(self):
        self.reject("LEASE_TTL_INVALID",lambda:self.store.renew(self.ticket,NOW+1,lease_ms=900))

    def test_clock_backward_latches_lock(self):
        self.reject("CLOCK_ROLLBACK_HARD_LOCK",lambda:self.store.renew(self.ticket,NOW-1))
        self.assertTrue(self.store.inspect()["hard_lock"])
        other=PaperFencedStore(self.path)
        try:self.reject("PERSISTENT_HARD_LOCK",lambda:other.claim(NOW+31000))
        finally:other.close()

    def test_no_arm_without_human(self):
        self.reject("HUMAN_PAPER_APPROVAL_REQUIRED",lambda:self.store.arm_paper(
            self.ticket,NOW+1,human_approval=False,
            policy_sha=POLICY,strategy_sha=STRATEGY))

    def test_no_arm_with_invalid_hash(self):
        self.reject("INVALID_STRATEGY_OR_POLICY_SHA",lambda:self.store.arm_paper(
            self.ticket,NOW+1,human_approval=True,policy_sha="no",strategy_sha=STRATEGY))

    def test_session_cannot_exceed_fence(self):
        self.reject("SESSION_OUTLASTS_FENCE",lambda:self.store.arm_paper(
            self.ticket,NOW+29999,human_approval=True,
            policy_sha=POLICY,strategy_sha=STRATEGY,ttl_ms=1000))

    def test_session_ttl_out_of_range(self):
        self.reject("SESSION_TTL_INVALID",lambda:self.store.arm_paper(
            self.ticket,NOW+1,human_approval=True,
            policy_sha=POLICY,strategy_sha=STRATEGY,ttl_ms=60000))

    def test_arm_once_only(self):
        self.arm()
        self.reject("RECOVERY_OR_FREEZE_BLOCK",lambda:self.arm(now=NOW+2))

    def test_reserve_only_armed(self):
        self.reject("NOT_PAPER_ARMED",lambda:self.store.reserve(
            self.ticket,NOW+1,"abc",STRATEGY))

    def test_reserve_after_expired_session_denied(self):
        self.arm()
        self.reject("NOT_PAPER_ARMED",lambda:self.store.reserve(
            self.ticket,NOW+10001,"abc",STRATEGY))

    def test_reject_wrong_strategy(self):
        self.arm()
        self.reject("WRONG_STRATEGY",lambda:self.store.reserve(
            self.ticket,NOW+2,"abc","3"*64))

    def test_one_active_paper_intent_only(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"alpha",STRATEGY)
        self.reject("ANOTHER_POSITION_OR_ORDER_PENDING",lambda:self.store.reserve(
            self.ticket,NOW+3,"beta",STRATEGY))

    def test_duplicate_reservation_forever_even_after_cancel(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"alpha",STRATEGY)
        self.store.change_mock_intent(self.ticket,NOW+3,"alpha","PENDING","CANCELLED")
        self.reject("DUPLICATE_INTENT_PERSISTENT",lambda:self.store.reserve(
            self.ticket,NOW+4,"alpha",STRATEGY))

    def test_cancel_allows_new_id(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"alpha",STRATEGY)
        self.store.change_mock_intent(self.ticket,NOW+3,"alpha","PENDING","CANCELLED")
        self.store.reserve(self.ticket,NOW+4,"beta",STRATEGY)
        self.assertEqual(len(self.store.inspect()["intents"]),2)

    def test_unknown_paper_fill_stays_pending_after_restart(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"unknown",STRATEGY)
        other=PaperFencedStore(self.path)
        try:
            self.assertEqual(other.inspect()["intents"][0]["state"],"PENDING")
            self.reject("LEASE_HELD_BY_OTHER",lambda:other.claim(NOW+3))
            ticket2=other.claim(NOW+30001)
            self.assertEqual(other.inspect()["phase"],"FROZEN_RECOVERY_REQUIRED")
            self.reject("RECOVERY_OR_FREEZE_BLOCK",lambda:other.arm_paper(
                ticket2,NOW+30002,human_approval=True,policy_sha=POLICY,
                strategy_sha=STRATEGY))
        finally:other.close()

    def test_injected_crash_before_commit_rolls_back_intent(self):
        self.arm()
        with self.assertRaisesRegex(RuntimeError,"INJECTED_POWER_LOSS_BEFORE_COMMIT"):
            self.store.reserve(self.ticket,NOW+2,"notcommitted",STRATEGY,
                               crash_before_commit=True)
        self.assertEqual(self.store.inspect()["intents"],[])
        self.store.reserve(self.ticket,NOW+3,"notcommitted",STRATEGY)
        self.assertEqual(self.store.inspect()["intents"][0]["state"],"PENDING")

    def test_committed_intent_survives_connection_close(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"persisted",STRATEGY)
        other=PaperFencedStore(self.path)
        try:self.assertEqual(other.inspect()["intents"][0]["id"],"persisted")
        finally:other.close()

    def test_fill_without_stop_ack_stays_unprotected(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.store.change_mock_intent(self.ticket,NOW+3,"position","PENDING","FILLED_UNPROTECTED")
        self.assertEqual(self.store.inspect()["intents"][0]["state"],"FILLED_UNPROTECTED")

    def test_invalid_transition_rejected(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.reject("INVALID_MOCK_TRANSITION",lambda:self.store.change_mock_intent(
            self.ticket,NOW+3,"position","PENDING","PROTECTED"))

    def test_wrong_expected_transition_rejected(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.reject("UNKNOWN_OR_INCONSISTENT_INTENT",lambda:self.store.change_mock_intent(
            self.ticket,NOW+3,"position","PROTECTED","CLOSED"))

    def test_paper_protected_flow_not_real(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.store.change_mock_intent(self.ticket,NOW+3,"position","PENDING","FILLED_UNPROTECTED")
        self.store.change_mock_intent(self.ticket,NOW+4,"position","FILLED_UNPROTECTED","PROTECTED")
        self.assertEqual(self.store.inspect()["intents"][0]["state"],"PROTECTED")
        self.assertFalse(live_enabled())

    def test_disarm_with_pending_must_freeze(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.store.disarm(self.ticket,NOW+3)
        self.assertEqual(self.store.inspect()["phase"],"FROZEN_RECOVERY_REQUIRED")
        self.reject("NOT_PAPER_ARMED",lambda:self.store.reserve(
            self.ticket,NOW+4,"next",STRATEGY))

    def test_disarm_empty_may_return_disarmed(self):
        self.arm()
        self.store.disarm(self.ticket,NOW+2)
        self.assertEqual(self.store.inspect()["phase"],"DISARMED")
        self.arm(now=NOW+3)

    def test_reconcile_without_approval_denied(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.store.disarm(self.ticket,NOW+3)
        self.reject("MOCK_RECOVERY_PROOF_REQUIRED",lambda:self.store.reconcile_flat(
            self.ticket,NOW+4,human_approval=False,mock_flat_confirmed=True))

    def test_reconcile_without_paper_flat_denied(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.store.disarm(self.ticket,NOW+3)
        self.reject("MOCK_RECOVERY_PROOF_REQUIRED",lambda:self.store.reconcile_flat(
            self.ticket,NOW+4,human_approval=True,mock_flat_confirmed=False))

    def test_reconcile_never_deletes_original_client_id(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"position",STRATEGY)
        self.store.disarm(self.ticket,NOW+3)
        self.store.reconcile_flat(self.ticket,NOW+4,human_approval=True,mock_flat_confirmed=True)
        self.arm(now=NOW+5)
        self.reject("DUPLICATE_INTENT_PERSISTENT",lambda:self.store.reserve(
            self.ticket,NOW+6,"position",STRATEGY))
        self.assertEqual(self.store.inspect()["intents"][0]["state"],"CANCELLED")

    def test_recovery_on_expired_owner_needs_human(self):
        other=PaperFencedStore(self.path)
        try:
            next_owner=other.claim(NOW+30001)
            self.reject("MOCK_RECOVERY_PROOF_REQUIRED",lambda:other.reconcile_flat(
                next_owner,NOW+30002,human_approval=True,mock_flat_confirmed=False))
            other.reconcile_flat(next_owner,NOW+30003,human_approval=True,mock_flat_confirmed=True)
            other.arm_paper(next_owner,NOW+30004,human_approval=True,
                            policy_sha=POLICY,strategy_sha=STRATEGY,ttl_ms=1000)
            self.assertEqual(other.inspect()["phase"],"PAPER_ARMED")
        finally:other.close()

    def test_persisted_audit_verification(self):
        self.arm()
        self.store.reserve(self.ticket,NOW+2,"case",STRATEGY)
        self.assertGreaterEqual(self.store.verify_audit(),3)
        other=PaperFencedStore(self.path)
        try:self.assertEqual(self.store.verify_audit(),other.verify_audit())
        finally:other.close()

    def test_audit_modified_row_detected(self):
        self.arm()
        self.store.db.execute("UPDATE audit SET digest='bad' WHERE seq=1")
        self.reject("AUDIT_DIGEST_MISMATCH",self.store.verify_audit)

    def test_audit_last_head_mismatch_detected(self):
        self.arm()
        self.store.db.execute("UPDATE owner_state SET last_digest='bad' WHERE id=1")
        self.reject("AUDIT_HEAD_MISMATCH",self.store.verify_audit)

    def test_expired_original_cannot_arm_after_fencing(self):
        other=PaperFencedStore(self.path)
        try:
            other.claim(NOW+30001)
            self.reject("STALE_FENCING_TOKEN",lambda:self.store.arm_paper(
                self.ticket,NOW+30002,human_approval=True,
                policy_sha=POLICY,strategy_sha=STRATEGY))
        finally:other.close()

    def test_cannot_reuse_expired_lease_same_token(self):
        self.reject("LEASE_EXPIRED",lambda:self.store.reserve(
            self.ticket,NOW+30001,"late",STRATEGY))

    def test_write_to_unknown_journal_dir_blocked(self):
        missing=Path(self.temp.name)/"not-exists"/"store.sqlite"
        self.reject("JOURNAL_DIRECTORY_MISSING",lambda:PaperFencedStore(missing))

    def test_in_memory_db_refused_for_durable_recovery(self):
        self.reject("PERSISTENT_FILE_REQUIRED",lambda:PaperFencedStore(":memory:"))


class MultiprocessStyleRace(unittest.TestCase):
    def test_concurrent_independent_connections_single_fence_winner(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"race.sqlite"
            setup=PaperFencedStore(p);setup.close()
            def worker(i):
                db=PaperFencedStore(p)
                try:
                    return ("WON",db.claim(NOW).epoch)
                except GuardError as e:
                    return ("REJECT",str(e))
                finally:
                    db.close()
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                outcomes=list(pool.map(worker,range(8)))
            self.assertEqual(sum(x[0]=="WON" for x in outcomes),1,outcomes)
            self.assertEqual(sum(x[0]=="REJECT" for x in outcomes),7,outcomes)

    def test_atomic_no_duplicate_intent_with_two_file_connections(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"intents.sqlite"
            first=PaperFencedStore(p)
            try:
                token=first.claim(NOW)
                first.arm_paper(token,NOW+1,human_approval=True,
                                policy_sha=POLICY,strategy_sha=STRATEGY,ttl_ms=10000)
                def insert(idx):
                    db=PaperFencedStore(p)
                    try:
                        db.reserve(token,NOW+2,f"parallel-{idx}",STRATEGY)
                        return "RESERVED"
                    except GuardError as e:
                        return str(e)
                    finally:
                        db.close()
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    outcomes=list(pool.map(insert,range(2)))
                self.assertEqual(outcomes.count("RESERVED"),1,outcomes)
                self.assertEqual(sum(o=="ANOTHER_POSITION_OR_ORDER_PENDING" for o in outcomes),1,outcomes)
                self.assertEqual(len(first.inspect()["intents"]),1)
            finally:
                first.close()



class RealSubprocessCrashTests(unittest.TestCase):
    """Actual OS processes, not just independent SQLite threads."""

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file=Path(self.tmp.name)/"worker.sqlite"
        db=PaperFencedStore(self.file)
        db.close()
        self.env=dict(os.environ)
        src_dir=str(Path(__file__).resolve().parent)
        self.env["PYTHONPATH"]=src_dir+os.pathsep+self.env.get("PYTHONPATH","")

    def command(self, script):
        return [sys.executable,"-c",script,str(self.file)]

    def test_six_real_processes_only_one_can_claim(self):
        code="""import sys
from single_writer_recovery import PaperFencedStore,GuardError
db=PaperFencedStore(sys.argv[1])
try:
  db.claim(2000000000000)
  print('WON',flush=True)
except GuardError as e:
  print('REJECT:'+str(e),flush=True)
finally:
  db.close()
"""
        workers=[subprocess.Popen(self.command(code),env=self.env,
                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                 for _ in range(6)]
        results=[p.communicate(timeout=15) for p in workers]
        self.assertTrue(all(p.returncode==0 for p in workers),results)
        lines=[a.strip() for a,b in results]
        self.assertEqual(lines.count("WON"),1,lines)
        self.assertEqual(lines.count("REJECT:LEASE_HELD_BY_OTHER"),5,lines)

    def test_real_process_exit_after_commit_keeps_pending_and_forces_reconcile(self):
        code="""import os,sys
from single_writer_recovery import PaperFencedStore
db=PaperFencedStore(sys.argv[1])
t=db.claim(2000000000000)
db.arm_paper(t,2000000000001,human_approval=True,
             policy_sha='1'*64,strategy_sha='2'*64,ttl_ms=10000)
db.reserve(t,2000000000002,'crashed_pending','2'*64)
os._exit(17)
"""
        child=subprocess.run(self.command(code),env=self.env,
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             text=True,timeout=15)
        self.assertEqual(child.returncode,17,child.stderr)
        store=PaperFencedStore(self.file)
        try:
            self.assertEqual(store.inspect()["intents"][0]["state"],"PENDING")
            new=store.claim(NOW+30001)
            self.assertEqual(store.inspect()["phase"],"FROZEN_RECOVERY_REQUIRED")
            with self.assertRaisesRegex(GuardError,"RECOVERY_OR_FREEZE_BLOCK"):
                store.arm_paper(new,NOW+30002,human_approval=True,
                     policy_sha=POLICY,strategy_sha=STRATEGY)
            store.reconcile_flat(new,NOW+30003,human_approval=True,
                                 mock_flat_confirmed=True)
            store.arm_paper(new,NOW+30004,human_approval=True,
                            policy_sha=POLICY,strategy_sha=STRATEGY,ttl_ms=1000)
            with self.assertRaisesRegex(GuardError,"DUPLICATE_INTENT_PERSISTENT"):
                store.reserve(new,NOW+30005,"crashed_pending",STRATEGY)
        finally:store.close()

    def test_real_process_exit_mid_transaction_rolls_back_uncommitted_reservation(self):
        code="""import os,sys
from single_writer_recovery import PaperFencedStore
db=PaperFencedStore(sys.argv[1])
t=db.claim(2000000000000)
db.arm_paper(t,2000000000001,human_approval=True,
             policy_sha='1'*64,strategy_sha='2'*64,ttl_ms=10000)
db.db.execute('BEGIN IMMEDIATE')
db.db.execute("INSERT INTO paper_intents(client_id,epoch,state,created_ms,updated_ms) VALUES('uncommitted',1,'PENDING',2000000000002,2000000000002)")
os._exit(19)
"""
        child=subprocess.run(self.command(code),env=self.env,
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             text=True,timeout=15)
        self.assertEqual(child.returncode,19,child.stderr)
        store=PaperFencedStore(self.file)
        try:
            self.assertEqual(store.inspect()["intents"],[])
            self.assertEqual(store.inspect()["phase"],"PAPER_ARMED")
            self.assertGreaterEqual(store.verify_audit(),2)
            new=store.claim(NOW+30001)
            self.assertEqual(store.inspect()["phase"],"FROZEN_RECOVERY_REQUIRED")
            store.reconcile_flat(new,NOW+30002,human_approval=True,mock_flat_confirmed=True)
        finally:store.close()

if __name__=="__main__":
    unittest.main(verbosity=2)
