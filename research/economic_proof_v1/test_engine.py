import copy
import json
from pathlib import Path
import tempfile
import unittest
import engine as e


def signal(**changes):
    return dict(id="s1", trade_id="t1", kind="precommit", at="2026-11-05T08:00:00Z",
                information_cutoff="2026-11-05T07:59:00Z", entry_deadline="2026-11-05T08:05:00Z",
                phase="oos", decision="enter", strategy="synthetic_linear", cohort="2026-11-05",
                risk="10", currency="USDC", rules_sha256="a"*64, evidence_sha256="b"*64,
                simulation=True) | changes


def row(event, previous=e.ZERO):
    r = dict(previous=previous, event=event)
    return r | {"hash": e.digest(r)}


def fixture():
    rows = [row(signal())]
    commitment = rows[0]["hash"]
    def add(kind, **kw):
        event = dict(id=str(len(rows)), trade_id="t1", kind=kind,
                     at=f"2026-11-05T08:{len(rows):02d}:00Z", simulation=True,
                     currency="USDC", evidence_sha256="c"*64, commitment=commitment) | kw
        rows.append(row(event, rows[-1]["hash"]))
    add("entry", instrument="X", leg="long", side="buy", quantity="1", price="100", cash="-100", spread_embedded="1", slippage_embedded="0.5")
    add("exit", instrument="X", leg="long", side="sell", quantity="1", price="110", cash="110", spread_embedded="1", slippage_embedded="0.5")
    add("cost", category="fees", cash="-2")
    add("cost", category="funding", cash="0.5")
    add("close", coverage={c: "recorded" if c in {"fees", "funding"} else "not_applicable" for c in e.COSTS},
        reconciled_legs=["long"], reconciliation_evidence="synthetic flat-position receipt")
    return rows


def rehash(rows):
    result = []
    for r in rows:
        result.append(row(r["event"], result[-1]["hash"] if result else e.ZERO))
    return result


class LedgerTests(unittest.TestCase):
    def test_net_r_and_no_double_spread(self):
        report = e.report(fixture())
        self.assertEqual(report["outcomes"][0]["net"], "8.5")
        self.assertEqual(report["outcomes"][0]["r"], "0.85")
        self.assertFalse(report["live_go"])

    def test_no_precommit_and_wrong_binding(self):
        rows = fixture()
        with self.assertRaisesRegex(ValueError, "NO_PRECOMMIT"):
            e.replay(rehash(rows[1:]))
        rows[1]["event"]["commitment"] = "d"*64
        with self.assertRaisesRegex(ValueError, "PRECOMMIT_BINDING"):
            e.replay(rehash(rows))

    def test_duplicate_nonfinite_and_late_entry(self):
        for key, val, error in [("cash", "NaN", "NONFINITE"), ("at", "2026-11-05T08:06:00Z", "LATE_ENTRY"), ("id", "s1", "DUPLICATE_EVENT")]:
            rows = fixture()
            rows[1]["event"][key] = val
            with self.assertRaisesRegex(ValueError, error):
                e.replay(rehash(rows))

    def test_cost_missing_or_falsely_not_applicable(self):
        for change, error in [(lambda c: c.pop("conversion"), "COST_COVERAGE_MISSING"),
                              (lambda c: c.update(fees="not_applicable"), "COST_COVERAGE_CONFLICT")]:
            rows = fixture()
            change(rows[-1]["event"]["coverage"])
            with self.assertRaisesRegex(ValueError, error):
                e.replay(rehash(rows))

    def test_unsettled_not_zero_or_used_for_uncertainty(self):
        r = e.report(fixture()[:-1])
        self.assertEqual(r["status"], "INCOMPLETE")
        self.assertEqual(r["outcomes"], [])
        self.assertEqual(r["incomplete"], ["t1"])

    def test_anchor_detects_truncation(self):
        rows = fixture()
        with self.assertRaisesRegex(ValueError, "ANCHOR_MISMATCH"):
            e.replay(rows[:-1], rows[-1]["hash"])

    def test_append_validation_lock_and_partial_write(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"ledger.jsonl"
            head = e.append(path, signal())
            self.assertEqual(e.report(e.read(path), head)["head"], head)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "DUPLICATE_EVENT"):
                e.append(path, signal())
            self.assertEqual(before, path.read_bytes())
            lock = Path(str(path)+".lock")
            lock.write_text("")
            with self.assertRaises(FileExistsError):
                e.append(path, signal(id="s2"))
            lock.unlink()
            path.write_bytes(before[:-1])
            with self.assertRaisesRegex(ValueError, "TRUNCATED_LEDGER"):
                e.read(path)

    def test_abstention_and_phase_separation(self):
        a = signal(decision="abstain", phase="development")
        b = signal(id="s2", trade_id="t2", decision="abstain", at="2026-11-06T08:00:00Z", entry_deadline="2026-11-06T08:05:00Z")
        rows = [row(a)]
        rows.append(row(b, rows[-1]["hash"]))
        self.assertEqual(len(e.report(rows)["summaries"]), 2)

    def test_no_false_small_sample_precision(self):
        self.assertEqual(e.interval([1.0]*29)["status"], "INSUFFICIENT_COHORTS")
        a = e.interval([0., 1., -1.]*12, replicates=100)
        self.assertEqual(a, e.interval([0., 1., -1.]*12, replicates=100))
        self.assertEqual(a["status"], "EXPLORATORY_NOT_PROMOTION")

    def test_drawdown_includes_initial_loss(self):
        rows = fixture()
        rows[2]["event"]["cash"] = "90"
        r = e.report(rehash(rows))
        self.assertEqual(r["summaries"][0]["realized_cash_drawdown"], "11.5")


if __name__ == "__main__":
    unittest.main()
