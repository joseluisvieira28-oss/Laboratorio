import os
import tempfile
import unittest
from datetime import datetime, timezone

from radar.dh03_archive_watcher import _persist, run_once
from radar.evidence import EvidenceStore


class DH03ArchiveWatcherTests(unittest.TestCase):
    def test_waits_before_first_eligible_archive_without_network(self):
        now=datetime(2026,9,18,10,0,tzinfo=timezone.utc)
        r=run_once(now=now,persist=False)
        self.assertEqual(r["status"],"WAITING_FIRST_ELIGIBLE_ARCHIVE_DAY")
        self.assertFalse(r["used_as_forward_evidence"])
        self.assertFalse(r["orders_created"])
        self.assertFalse(r["live_capital_enabled"])

    def test_evidence_replay_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            store=EvidenceStore(os.path.join(td,"e.sqlite3"))
            signal={
                "symbol":"BTCUSDT",
                "signal_open_time":1789732800000,
                "entry_open_time":1789776000000,
                "entry":100.0,"stop":95.0,"target":115.0,
                "initial_risk_fraction":0.05,
                "fingerprint":"abc123",
            }
            final={
                "symbol":"BTCUSDT",
                "signal_open_time":1789732800000,
                "entry_time":1789776000000,
                "exit_time":1789776060000,
                "entry_price":100.0,"exit_price":115.0,
                "stop":95.0,"target":115.0,
                "initial_risk_fraction":0.05,
                "exit_reason":"TARGET",
                "price_gross_return":0.15,
                "funding_return":-0.001,
                "funding_event_count":1,
                "economic_gross_return":0.149,
                "base_net_r":2.826923076923077,
                "stress_net_r":2.7547169811320753,
                "execution_path_unresolved":False,
            }
            symbols={s:{
                "complete_12h_bars":50,"incomplete_12h_buckets":0,
                "signal_diagnostics":{},"selected_signals":0,
                "overlap_skipped":0,"rows":[]
            } for s in ("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")}
            symbols["BTCUSDT"]["selected_signals"]=1
            symbols["BTCUSDT"]["rows"]=[{
                "signal":signal,
                "price_exit_time":1789776060000,
                "price_exit_price":115.0,
                "price_exit_reason":"TARGET",
                "price_path_unresolved":False,
                "funding_reconciliation_pending":False,
                "final_resolution":final,
            }]
            receipt={
                "latest_archive_day":"2026-09-30",
                "status":"OK",
                "price_source_receipts":[],
                "funding_source_receipts":[],
                "funding_complete_through_ms":1790812800000,
                "evaluation":{
                    "symbols":symbols,
                    "totals":{
                        "signals":1,"price_exits":1,"final_resolutions":1,
                        "funding_pending":0,"unresolved_price_paths":0,
                        "overlap_skipped":0,
                    },
                },
            }
            first=_persist(store,receipt)
            self.assertEqual(first,{"signals":1,"price_exits":1,"final_resolutions":1,"snapshots":1})
            second=_persist(store,receipt)
            self.assertEqual(second,{"signals":0,"price_exits":0,"final_resolutions":0,"snapshots":0})
            ok,detail=store.verify_chain()
            self.assertTrue(ok,detail)


if __name__=="__main__":
    unittest.main()
