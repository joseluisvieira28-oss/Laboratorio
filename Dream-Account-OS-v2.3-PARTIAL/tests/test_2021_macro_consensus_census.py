import csv
import hashlib
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).parents[1] / "research" / "news_shock_v03_macro_consensus_source_gate"


def rows(name):
    with (ROOT / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_manifest_is_exactly_frozen_2021_universe():
    data = rows("2021_EVENT_MANIFEST.csv")
    assert len(data) == 24
    assert len({r["event_id"] for r in data}) == 24
    assert sum(r["event_family"] == "CPI" for r in data) == 12
    assert sum(r["event_family"] == "EMPLOYMENT_SITUATION" for r in data) == 12
    assert all(r["release_date"].startswith("2021-") for r in data)


def test_et_utc_dst_consistency():
    for r in rows("2021_EVENT_MANIFEST.csv"):
        local = datetime.fromisoformat(r["release_date"] + "T08:30:00").replace(
            tzinfo=ZoneInfo("America/New_York"))
        assert local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z") == r["scheduled_T0_UTC"]


def test_consensus_is_strictly_pre_t0_or_null():
    for r in rows("2021_CONSENSUS_CENSUS.csv"):
        stamp = r["publication_timestamp_utc"]
        if stamp:
            assert datetime.fromisoformat(stamp.replace("Z", "+00:00")) < datetime.fromisoformat(
                r["T0_utc"].replace("Z", "+00:00"))
        else:
            assert r["consensus_value"] == ""
            assert r["provenance_status"] == "CONSENSUS_PROVENANCE_INCOMPLETE"


def test_missing_is_not_zero_and_post_release_not_accepted():
    for r in rows("2021_CONSENSUS_CENSUS.csv"):
        if r["consensus_value"] == "":
            assert r["consensus_value"] != "0"
        assert not (r["evidence_type"] == "POST_RELEASE_ARTICLE" and r["archive_status"] == "ACCEPTED")


def test_no_forbidden_market_outcomes_or_closed_years():
    forbidden = {"btc", "eth", "return", "pnl", "volume", "taker", "yield_reaction", "price"}
    headers = {h.lower() for h in rows("2021_CONSENSUS_CENSUS.csv")[0]}
    assert not headers & forbidden
    blob = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in [
        "2021_EVENT_MANIFEST.csv", "2021_CONSENSUS_CENSUS.csv", "2021_FIELD_COVERAGE_MATRIX.csv"])
    assert "2025-" not in blob and "2026-" not in blob


def test_complete_requires_consensus_hash_and_provenance():
    matrix = rows("2021_FIELD_COVERAGE_MATRIX.csv")
    census = rows("2021_CONSENSUS_CENSUS.csv")
    indexed = {(r["event_id"], r["field"]): r for r in census}
    for r in matrix:
        if r["event_class"] == "ACCEPTED_COMPLETE":
            e = indexed[(r["event_id"], r["required_field"])]
            assert e["consensus_source_url"] and e["publication_timestamp_utc"]
            assert len(e["evidence_hash_sha256"]) == 64


def test_hash_manifest_matches_bytes():
    for r in rows("receipts/2021_HASH_MANIFEST.csv"):
        target = ROOT / r["path"]
        assert hashlib.sha256(target.read_bytes()).hexdigest() == r["sha256"]


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            suite.addTest(unittest.FunctionTestCase(value, description=name))
    return suite
