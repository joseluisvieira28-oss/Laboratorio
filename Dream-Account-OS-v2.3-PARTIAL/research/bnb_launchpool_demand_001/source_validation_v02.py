import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECON = HERE / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_RECON_V0.1.json"
V01 = HERE / "source_archive_v01" / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_ARCHIVE_RECEIPT_V0.1.json"
AMEND = HERE / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_VALIDATION_AMENDMENT_V0.2.json"
OUTDIR = HERE / "source_validation_v02"
OUT = OUTDIR / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_VALIDATION_V0.2.json"


def parse_iso(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)


def minute_floor_iso(s):
    dt = parse_iso(s).replace(second=0, microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    recon = json.loads(RECON.read_text(encoding="utf-8"))
    v01 = json.loads(V01.read_text(encoding="utf-8"))
    amend = json.loads(AMEND.read_text(encoding="utf-8"))

    assert amend["status"] == "FROZEN_POST_SOURCE_BYTES_PRE_MARKET_OUTCOME"
    assert amend["governance"]["no_event_addition_or_removal"] is True
    assert amend["governance"]["no_market_price_access"] is True
    assert amend["governance"]["no_2025"] is True
    assert amend["governance"]["no_2026"] is True

    expected = recon["events"]
    got = v01["events"]
    checks = {}
    checks["event_count_exactly_33"] = len(expected) == len(got) == 33
    checks["project_numbers_exactly_31_through_63_once_each"] = [e["n"] for e in expected] == list(range(31, 64)) and [e["n"] for e in got] == list(range(31, 64))
    checks["transport_failures_zero"] = int(v01.get("transport_failures", -1)) == 0
    codes = [e["article_code"] for e in got]
    checks["all_article_codes_unique"] = len(codes) == len(set(codes)) == 33
    checks["all_fixed_article_codes_present_in_official_response"] = all(bool(e.get("article_code_present")) for e in got)
    checks["all_launchpool_context_present"] = all(bool(e.get("launchpool_present")) for e in got)
    checks["all_expected_symbols_present"] = all(bool(e.get("symbol_present")) for e in got)
    checks["all_bnb_present"] = all(bool(e.get("bnb_present")) for e in got)
    checks["all_staking_or_locking_or_farming_language_present"] = all(bool(e.get("staking_or_locking_language_present")) for e in got)
    checks["all_cms_publish_dates_parseable"] = True
    try:
        [parse_iso(e["recovered_published_utc"]) for e in got]
    except Exception:
        checks["all_cms_publish_dates_parseable"] = False
    checks["all_recon_minutes_equal_floor_to_minute_cms_publish_date"] = all(
        str(exp["published"]) == minute_floor_iso(obs["recovered_published_utc"])
        for exp, obs in zip(expected, got)
    )
    checks["all_raw_response_sha256_present"] = all(
        isinstance(e.get("sha256"), str) and len(e["sha256"]) == 64
        for e in got
    )
    checks["access_2025_false"] = v01.get("access_2025") is False
    checks["access_2026_false"] = v01.get("access_2026") is False
    checks["market_outcomes_opened_false"] = v01.get("market_outcomes_opened") is False

    canonical_events = []
    for exp, obs in zip(expected, got):
        canonical_events.append({
            "n": int(obs["n"]),
            "symbol": str(obs["symbol"]),
            "article_code": str(obs["article_code"]),
            "official_support_url": str(obs["official_support_url"]),
            "published_timestamp_utc": str(obs["recovered_published_utc"]),
            "recon_minute_timestamp_utc": str(exp["published"]),
            "raw_response_sha256": str(obs["sha256"]),
            "project_number_text_present_diagnostic": bool(obs.get("project_number_present")),
        })

    basis = "\n".join(
        f"{e['n']}|{e['symbol']}|{e['article_code']}|{e['published_timestamp_utc']}|{e['raw_response_sha256']}"
        for e in canonical_events
    ).encode("utf-8")
    canonical_manifest_sha256 = hashlib.sha256(basis).hexdigest()

    classification = "SOURCE_DATA_PASS" if all(checks.values()) else "SOURCE_VALIDATION_REMEDIATION_FAIL"
    out = {
        "lab_id": "BNB-LAUNCHPOOL-DEMAND-001",
        "source_gate_id": "BLP-BNB-OFFICIAL-ANNOUNCEMENTS-001",
        "validation_amendment": "BLP-SOURCE-VALIDATION-AMENDMENT-V0.2",
        "classification": classification,
        "v01_classification_preserved": v01["classification"],
        "v01_ordered_manifest_sha256": v01["ordered_manifest_sha256"],
        "v01_artifact_id": 10461865222,
        "v01_artifact_expected_zip_sha256": "7625170ac651c073cab094a22811559b6ebf2c28ee3a4459eb58127225953dcc",
        "source_pass_checks": checks,
        "canonical_event_count": len(canonical_events),
        "canonical_event_manifest_sha256": canonical_manifest_sha256,
        "canonical_events": canonical_events,
        "diagnostics": {
            "literal_project_number_present_count": sum(1 for e in got if e.get("project_number_present")),
            "literal_project_number_missing": [int(e["n"]) for e in got if not e.get("project_number_present")],
            "max_second_offset_from_recon_minute": max(int((parse_iso(e["recovered_published_utc"]) - parse_iso(x["published"])).total_seconds()) for x, e in zip(expected, got)),
        },
        "firewalls": {
            "market_price_fields_opened": False,
            "bnb_price_opened": False,
            "btc_price_opened": False,
            "returns_computed": False,
            "pnl_computed": False,
            "access_2025": False,
            "access_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
            "orders": False,
            "merge_to_main": False,
        },
        "next_step_if_pass": "Freeze a separate event-mechanism Discovery protocol before opening any market price field.",
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": classification,
        "canonical_event_count": len(canonical_events),
        "canonical_event_manifest_sha256": canonical_manifest_sha256,
        "failed_checks": [k for k, v in checks.items() if not v],
    }, indent=2))


if __name__ == "__main__":
    main()
