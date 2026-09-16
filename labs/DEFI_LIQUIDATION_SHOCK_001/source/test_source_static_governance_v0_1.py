#!/usr/bin/env python3
"""Static fail-closed governance checks for DEFI-LIQUIDATION-SHOCK-001 source route.

No network calls. No prices, returns, PnL or market outcomes are read.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRY = json.loads((ROOT / "protocol_registry_v0_1.json").read_text(encoding="utf-8"))
COVERAGE_SQL = (ROOT / "BIGQUERY_PROGRAM_COVERAGE_PROBE_V0_1.sql").read_text(encoding="utf-8")
CENSUS_SQL = (ROOT / "BIGQUERY_LIQUIDATION_CANDIDATE_CENSUS_V0_1.sql").read_text(encoding="utf-8")

EXPECTED_START = "2021-01-01T00:00:00Z"
EXPECTED_END = "2024-12-31T23:59:59Z"
EXPECTED_SQL_END = "2025-01-01T00:00:00Z"
EXPECTED_PROGRAMS = {
    "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
    "MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
    "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
    "dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
}
EXPECTED_TABLE = "bigquery-public-data.crypto_solana_mainnet_us.Instructions"


def sql_without_comments(sql: str) -> str:
    return "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))


def sql_table_refs(sql: str) -> set[str]:
    # Comments can legitimately mention backticked field names such as `data`.
    # Only executable SQL is relevant to the source-table firewall.
    body = sql_without_comments(sql)
    return set(re.findall(r"`([^`]+)`", body))


def main() -> int:
    assert REGISTRY["lab_id"] == "DEFI-LIQUIDATION-SHOCK-001"
    assert REGISTRY["status"] == "REFERENCE_ONLY_UNTIL_HISTORICAL_VALIDATION"
    assert REGISTRY["source_window_utc"] == {"start": EXPECTED_START, "end": EXPECTED_END}

    protocols = REGISTRY["protocols"]
    assert len(protocols) == 4
    assert {p["program_id"] for p in protocols} == EXPECTED_PROGRAMS
    assert all(p["historical_decoder_authoritative"] is False for p in protocols)

    gov = REGISTRY["governance"]
    assert gov == {
        "outcomes_opened": False,
        "prices_queried": False,
        "returns_computed": False,
        "pnl_computed": False,
        "protocol_winner_selected": False,
    }

    for name, sql in (("coverage", COVERAGE_SQL), ("census", CENSUS_SQL)):
        body = sql_without_comments(sql)
        refs = sql_table_refs(sql)
        assert refs == {EXPECTED_TABLE}, (name, refs)
        assert "2021-01-01T00:00:00Z" in body
        assert EXPECTED_SQL_END in body
        for program_id in EXPECTED_PROGRAMS:
            assert program_id in body, (name, program_id)
        # Fail closed if future source windows are accidentally introduced.
        assert "2026-" not in body
        # Only the frozen source table may be queried; these common market/outcome
        # table names must never occur as executable identifiers.
        lowered = body.lower()
        for forbidden in ("klines", "candles", "prices", "returns", "pnl", "postgard_outcomes"):
            assert f"`{forbidden}" not in lowered

    # Census prefixes must exactly match the pre-registered reference encodings.
    registry_prefixes = {
        (p["program_id"], e["prefix_hex"].lower())
        for p in protocols for e in p["reference_liquidation_encodings"]
    }
    expected_prefixes = {prefix for _, prefix in registry_prefixes}
    literal_prefixes = set(re.findall(r"'([0-9a-f]{2}|[0-9a-f]{16})'", CENSUS_SQL.lower()))
    assert expected_prefixes <= literal_prefixes
    assert literal_prefixes - expected_prefixes == set(), literal_prefixes - expected_prefixes

    print(json.dumps({
        "lab": "DEFI-LIQUIDATION-SHOCK-001",
        "stage": "SOURCE_STATIC_GOVERNANCE_V0.1",
        "classification": "PASS",
        "protocols": len(protocols),
        "program_ids": len(EXPECTED_PROGRAMS),
        "reference_prefixes": len(registry_prefixes),
        "outcomes_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
