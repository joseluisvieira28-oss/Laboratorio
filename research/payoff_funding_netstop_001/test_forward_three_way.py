"""Synthetic forward-path tests. No 2020-25 BTC outcomes, no network."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"payoff_funding_netstop_001"))
sys.path.insert(0,str(ROOT/"payoff_failure_execution_forward"))
import forward_child_replay as child
import forward_three_way as trio
import forward_boundary_gate as gate

H=gate.H
T=gate.BOUNDARY
BEGIN=T+200*H

def bars(n=208):
    return [{"t":T+i*H,"open":100.,"high":101.,"low":99.,
             "close":100.,"volume":100.} for i in range(n)]

def mark(b):
    return {x["t"]:{"open":100.,"high":101.,"low":99.,"close":100.} for x in b}

def sig(b):
    s=[False]*len(b)
    s[200]=True
    return s

class FutureChildTests(unittest.TestCase):
    def test_zero_funding_has_one_open_and_no_fabricated_profit(self):
        b=bars()
        r=child.replay_forward_child(b,{},mark(b),.0008,.0002,BEGIN,b[-1]["t"],signal_override=sig(b))
        self.assertEqual(r["closed"],0)
        self.assertEqual(len(r["unresolved_at_cutoff"]),1)
        self.assertEqual(r["live_trading_authority"],"NONE")

    def test_funding_adjustment_deferred_to_next_hour(self):
        b=bars()
        funds={T+202*H:.05}
        r=child.replay_forward_child(b,funds,mark(b),.0008,.0002,BEGIN,b[-1]["t"],signal_override=sig(b))
        self.assertEqual(r["closed"],1)
        self.assertEqual(r["trade_ledger"][0]["reason"],"NET_STOP_GAP")
        self.assertEqual(r["trade_ledger"][0]["exit_t"],T+203*H)
        self.assertEqual(r["funding_related_stop_updates"],1)
        self.assertLess(r["trade_ledger"][0]["margin_net_return"],0)

    def test_no_funding_credit_at_entry_timestamp(self):
        b=bars()
        funding={T+201*H:.05}
        r=child.replay_forward_child(b,funding,mark(b),.0008,.0002,BEGIN,b[-1]["t"],signal_override=sig(b))
        self.assertEqual(r["funding_events"],0)

    def test_stop_fill_gap_is_worse_than_threshold(self):
        b=bars()
        b[202]["open"]=90.;b[202]["high"]=91.;b[202]["low"]=89.;b[202]["close"]=90.
        b[203]["open"]=90.;b[203]["high"]=91.;b[203]["low"]=89.;b[203]["close"]=90.
        r=child.replay_forward_child(b,{},mark(b),.0008,.0002,BEGIN,b[-1]["t"],signal_override=sig(b))
        self.assertEqual(r["closed"],1)
        self.assertEqual(r["trade_ledger"][0]["reason"],"NET_STOP_GAP")
        self.assertLess(r["trade_ledger"][0]["margin_net_return"],-.10)

    def test_target_no_fake_holdout_result(self):
        b=bars()
        b[202]["high"]=122.
        r=child.replay_forward_child(b,{},mark(b),.0008,.0002,BEGIN,b[-1]["t"],signal_override=sig(b))
        self.assertEqual(r["closed"],1)
        self.assertEqual(r["wins"],1)
        self.assertEqual(r["trade_ledger"][0]["reason"],"TARGET")

    def test_reject_historical_economic_replay(self):
        b=bars()
        with self.assertRaisesRegex(ValueError,"PRE_BOUNDARY"):
            child.replay_forward_child(b,{},mark(b),.0008,.0002,T-H,b[-1]["t"],signal_override=sig(b))

    def test_strict_threeway_rejects_unverified_source(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_PROVENANCE"):
            trio.compare({"status":"SOURCE_OK","source_mode":"UNKNOWN","trading_authority":"NONE"})

    def test_threeway_rejects_non_none_authority(self):
        with self.assertRaisesRegex(ValueError,"TRADING_AUTHORITY"):
            trio.compare({"source_mode":"CHECKSUM_VERIFIED_DAILY_ARCHIVE_PLUS_PUBLIC_FUNDING_ENDPOINT",
                          "trading_authority":"LIVE"})

    def test_no_silent_acceptance_of_missing_manifest(self):
        with self.assertRaisesRegex(ValueError,"RECEIPTS_MISSING"):
            trio.compare({"source_mode":"CHECKSUM_VERIFIED_DAILY_ARCHIVE_PLUS_PUBLIC_FUNDING_ENDPOINT",
                          "trading_authority":"NONE"})

    def test_unvalidated_parent_source_fails(self):
        b=bars()
        d={"source_mode":"CHECKSUM_VERIFIED_DAILY_ARCHIVE_PLUS_PUBLIC_FUNDING_ENDPOINT",
           "trading_authority":"NONE","manifests":[{"sha":"dummy"}],
           "funding_manifests":[{"sha":"dummy"}],
           "authority":"PUBLIC_READ_ONLY_SHADOW",
           "status":"SOURCE_OK",
           "forward_boundary_utc":"2026-10-14T00:00:00Z",
           "bars":b,
           "funding":{},
           "marks":{str(t):m for t,m in mark(b).items()},
           "funding_verified_through_ms":0,
           "verified_complete_through_ms":b[-1]["t"]+H}
        with self.assertRaisesRegex(ValueError,"FUNDING_COVERAGE"):
            trio.compare(d)

if __name__=="__main__":unittest.main()
