import csv
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from sensor_freshness_audit_v01 import BAR_MS, FreshnessError, evaluate, intake_stats, iso_to_ms

T=1790864700000
NOW=iso_to_ms("2026-10-09T10:40:00Z")

def setup(now=NOW, last=T, vault_last=1790812500000, ledger_last=T, rows=174):
    first=last-(rows-1)*BAR_MS
    trigger={
        "lab_id":"ABSORPTION-FAILED-AUCTION-001",
        "trading_authority":"NONE",
        "economic_outcomes_unlocked":False,
        "event_open_boundary_ms":1790860200000,
        "intake_rows":rows,
        "intake_first_bar_close_ms":first,
        "intake_last_bar_close_ms":last
    }
    forward={
        "lab_id":"ABSORPTION-FAILED-AUCTION-001",
        "trading_authority":"NONE",
        "economic_outcomes_unlocked":False,
        "outcome_fields_present":False,
        "processed_through_bar_close_ms":ledger_last
    }
    vault={
        "lab_id":"TV-FOOTPRINT-CALIBRATION-001",
        "sensor_version":"MM-V1",
        "symbol":"BINANCE:BTCUSDT",
        "timeframe":"5",
        "last_bar_close_ms":vault_last
    }
    return trigger,forward,vault,(rows,first,last),now

class Freshness(unittest.TestCase):
    def test_realistic_stale(self):
        t,f,v,i,now=setup()
        z=evaluate(t,f,v,i,now)
        self.assertEqual(z["state"],"SOURCE_STALE_OR_LEDGER_LAG__NO_NEW_FORWARD_EVIDENCE")
        self.assertEqual(z["reasons"],["CURRENT_INTAKE_STALE","VAULT_ARCHIVE_STALE"])
        self.assertEqual(z["trading_authority"],"NONE")
    def test_recent_and_synced(self):
        last=NOW-15*60_000
        t,f,v,i,now=setup(last=last,ledger_last=last,vault_last=last)
        t["event_open_boundary_ms"]=last-100*BAR_MS
        z=evaluate(t,f,v,i,now)
        self.assertEqual(z["state"],"SOURCE_OBSERVABILITY_OK")
    def test_recent_ingest_but_stale_vault(self):
        last=NOW-15*60_000
        t,f,v,i,now=setup(last=last,ledger_last=last)
        t["event_open_boundary_ms"]=last-100*BAR_MS
        z=evaluate(t,f,v,i,now)
        self.assertIn("VAULT_ARCHIVE_STALE",z["reasons"])
    def test_ledger_lag(self):
        last=NOW-15*60_000
        t,f,v,i,now=setup(last=last,ledger_last=last-5*BAR_MS,vault_last=last)
        t["event_open_boundary_ms"]=last-100*BAR_MS
        z=evaluate(t,f,v,i,now)
        self.assertIn("FORWARD_LEDGER_LAGS_INTAKE",z["reasons"])
    def test_forward_cannot_exceed_intake(self):
        t,f,v,i,now=setup(ledger_last=T+BAR_MS)
        with self.assertRaises(FreshnessError):evaluate(t,f,v,i,now)
    def test_wrong_sensor_identity(self):
        t,f,v,i,now=setup()
        v["sensor_version"]="FAKE-MM-V2"
        with self.assertRaises(FreshnessError):evaluate(t,f,v,i,now)
    def test_outcomes_locked(self):
        t,f,v,i,now=setup()
        f["outcome_fields_present"]=True
        with self.assertRaises(FreshnessError):evaluate(t,f,v,i,now)
    def test_trading_locked(self):
        t,f,v,i,now=setup()
        t["trading_authority"]="MICROLIVE"
        with self.assertRaises(FreshnessError):evaluate(t,f,v,i,now)
    def test_intake_binding(self):
        t,f,v,i,now=setup()
        t["intake_rows"]=173
        with self.assertRaises(FreshnessError):evaluate(t,f,v,i,now)
    def test_future_observation(self):
        t,f,v,i,now=setup(now=T-1)
        with self.assertRaises(FreshnessError):evaluate(t,f,v,i,now)
    def test_offset_required(self):
        with self.assertRaises(FreshnessError):iso_to_ms("2026-10-09T10:00:00")
    def test_intake_csv_valid(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"t.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["bar_open_ms","bar_close_ms"])
                w.writerow([T,T+BAR_MS])
                w.writerow([T+BAR_MS,T+2*BAR_MS])
            self.assertEqual(intake_stats(p),(2,T+BAR_MS,T+2*BAR_MS))
    def test_intake_csv_gap(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"t.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["bar_open_ms","bar_close_ms"])
                w.writerow([T,T+BAR_MS])
                w.writerow([T+2*BAR_MS,T+3*BAR_MS])
            with self.assertRaises(FreshnessError):intake_stats(p)
    def test_intake_csv_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"t.csv"
            with p.open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["bar_open_ms","bar_close_ms"])
                w.writerow([T,T+BAR_MS]);w.writerow([T,T+BAR_MS])
            with self.assertRaises(FreshnessError):intake_stats(p)

if __name__=="__main__":
    unittest.main()
