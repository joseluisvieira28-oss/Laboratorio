import sqlite3
import tempfile
import unittest
from pathlib import Path
from engine.three_convex_v07.coverage import Coverage
from engine.three_convex_v05.signals import Bar,MS5
from engine.three_convex_v12.watcher import Outbox
from engine.three_convex_v12 import test_v12
from engine.convex_observer_audit.read_ledger import inspect


class ReceiptTests(unittest.TestCase):
    def test_expiry_health_does_not_revoke_proved_close_or_hide_legacy_gaps(self):
        db=sqlite3.connect(':memory:');c=Coverage(db);close=1000*MS5
        bars=[Bar(i*MS5,100,101,99,100,10) for i in range(700,1000)]
        c.record('SOL5',1,bars,close+2000,close,[])
        c.record('SOL5',1,bars,close+180001,close,[])
        summary=c.summary()
        self.assertEqual(summary['lanes']['SOL5']['state'],'EXPIRED_CLOSE')
        self.assertTrue(summary['lanes']['SOL5']['latest_close_decision_proven'])
        self.assertEqual(summary['unresolved_observed_closes'],0)
        self.assertFalse(summary['complete_coverage_proven'])
        db.close()

    def test_v12_ack_survives_restart_and_failure_remains_pending(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);q.enqueue(test_v12.V12Tests().signal('BNB_CONVEX_15M_EXPERIMENTAL'))
            def fail(_):raise RuntimeError('offline')
            with self.assertRaises(RuntimeError):q.drain(fail,301000)
            self.assertEqual(q.pending(),1)
            self.assertEqual(q.drain(lambda _:923,301000),(1,0));q.close()
            q=Outbox(d)
            self.assertEqual(q.db.execute('SELECT telegram_message_id FROM notices').fetchone()[0],923)
            self.assertEqual(q.pending(),0)
            q.close()
            report=inspect(Path(d)/'V12_ONLY.sqlite3')
            self.assertEqual(report['notices']['ack_receipts'][0]['telegram_message_id'],923)

    def test_v12_schema_upgrade_does_not_invent_old_ack(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'V12_ONLY.sqlite3';db=sqlite3.connect(p)
            db.execute('CREATE TABLE notices(id TEXT PRIMARY KEY,message TEXT NOT NULL,close_ms INTEGER NOT NULL,sent_ms INTEGER,expired_ms INTEGER)')
            db.execute("INSERT INTO notices VALUES('old','private message',300000,301000,NULL)")
            db.commit();db.close()
            q=Outbox(d)
            self.assertEqual(q.db.execute('SELECT sent_ms,telegram_message_id FROM notices').fetchone(),(301000,None))
            q.close()
            self.assertNotIn('private message',str(inspect(p)))

    def test_missing_readonly_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'missing.sqlite3'
            with self.assertRaises(sqlite3.OperationalError):inspect(p)
            self.assertFalse(p.exists())
