"""Offline closeout integrity validator; never computes strategy performance."""
import hashlib
import itertools
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "labs/BTC_OPTIONS_VRP_001"
EVIDENCE = ROOT / "receipts/btc_options_vrp_final_20261001"

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def require(value, message):
    if not value:
        raise ValueError(message)

def main():
    manifest = read(EVIDENCE / "evidence_manifest.json")
    for item in manifest["files"]:
        path = (ROOT / item["path"]).resolve()
        require(path.is_relative_to(ROOT), "manifest path escapes repository")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], "hash mismatch: " + item["path"])
    x = read(EVIDENCE / "optionsdx_census_complete.json")
    log = (EVIDENCE / "optionsdx_census_complete.log").read_text(encoding="utf-8-sig")
    echoed = [json.loads(line[line.index("{"):]) for line in log.splitlines()
              if '"resolved_variations":' in line and '"probe_id":' in line]
    require(len(echoed) == 1 and echoed[0] == x, "JSON differs from canonical log object")
    rows = x["resolved_variations"]
    period = sorted({r["attributes"]["attribute_period"] for r in rows})
    freq = {r["attributes"]["attribute_quote-frequency"] for r in rows}
    require(len(period) == 40 and period[0] == "2021-06" and period[-1] == "2024-09", "period catalogue drift")
    expected_freq = {"End of Day", "30 Minutes", "15 Minutes", "5 Minutes", "Minutely"}
    require(freq == expected_freq, "frequency catalogue drift")
    keys = [(r["attributes"]["attribute_period"], r["attributes"]["attribute_quote-frequency"]) for r in rows]
    require(len(keys) == len(set(keys)) == 200 and set(keys) == set(itertools.product(period, freq)), "incomplete/duplicate census")
    require(len({r["variation_id"] for r in rows}) == 200, "duplicate variation ids")
    for row in rows:
        require(isinstance(row["display_price"], (int, float)) and row["display_price"] >= 0, "invalid price metadata")
        require(all(k in row for k in ["display_regular_price", "variation_is_active", "is_in_stock", "is_purchasable"]), "missing authority field")
    zeros = [r for r in rows if r["display_price"] == 0]
    free_intraday = [r for r in zeros if r["attributes"]["attribute_quote-frequency"] != "End of Day"]
    require(len(zeros) == 40 and not free_intraday, "free route requires a new adjudication")
    require(x["zero_price_variations"] == zeros and x["zero_price_intraday_variations"] == free_intraday, "wrong zero subsets")
    require(x["classification"] == "OPTIONSDX_ZERO_PRICE_EOD_ONLY", "wrong classification")
    require(x["resolved_price_count"] == x["lookup_count"] == 200 and x["error_count"] == x["unresolved_lookup_count"] == 0, "census unresolved")
    require(x["cash_spend_usd"] == 0, "cash spend")
    for k in ["cart_used", "checkout_used", "account_created", "order_created", "market_payload_opened", "outcomes_opened"]:
        require(x[k] is False, "census firewall: " + k)
    health = read(EVIDENCE / "forward_health_receipt.json")
    require(health["classification"] == "PUBLIC_FORWARD_BBO_SOURCE_CAPTURE_PASS", "collector health did not pass")
    require(health["captured_instrument_count"] == health["selected_instrument_count"] == 112 and health["failure_count"] == 0, "health counts")
    require(len(health["artifact_sha256"]) == 64, "health hash")
    for k in ["authenticated", "orders", "pnl_computed", "returns_computed", "market_prices_emitted_in_receipt"]:
        require(health[k] is False, "health firewall: " + k)
    # This calendar inference is independent of price payload and gate code.
    anchors = [date(2021,4,1) + timedelta(days=7*i) for i in range(192)]
    require(anchors[-1] == date(2024,11,28) and all(d.weekday() == 3 for d in anchors), "frozen calendar drift")
    days = set(anchors) | {d + timedelta(days=7) for d in anchors}
    require(len(days) == 193 and max(days) == date(2024,12,5), "BOM calendar union")
    free_paired = sum(d.day == 1 and (d + timedelta(days=7)).day == 1 for d in anchors)
    require(free_paired == 0, "free-monthly calendar argument invalid")
    parent = read(LAB / "SOURCE_EXECUTION_VERDICT_V0.3.json")
    require(parent["discovery"]["classification"] == "DISCOVERY_PASS_VRP_EXISTS" and parent["discovery"]["n"] == 192, "parent discovery changed")
    require(parent["discovery"]["hac_95_ci"][0] > 0 and parent["discovery"]["bootstrap_95_ci"][0] > 0, "parent positive receipt changed")
    require(parent["old_execution"]["executable_n"] == 19 and parent["old_execution"]["performance"] is None and parent["old_execution"]["closed"], "old MVE reopened")
    v = read(LAB / "SOURCE_EXECUTION_VERDICT_V0.4.json")
    require(v["canonical_classification"] == "SOURCE_ACCESS_BLOCKED / EXECUTION_NOT_ADJUDICATED", "noncanonical verdict")
    require(v["parent_discovery_classification"] == parent["discovery"]["classification"] and v["vrp_phenomenon_survives"] and not v["source_access_blocked_is_no_edge"], "phenomenon not preserved")
    require(v["execution_mve_id"] == parent["bbo_execution"]["mve_id"] and v["minimum_executable_n"] == 120 and v["bbo_staleness_seconds_max"] == 30, "frozen gate drift")
    require(v["source_gate"]["status"] == "NOT_RUN_NO_ADMISSIBLE_CORPUS" and not v["source_gate"]["pass"] and v["source_gate"]["performance"] is None and v["execution"]["performance"] is None, "fabricated source/performance result")
    require(not v["forward_health"]["historical_coverage_claim"], "health promoted to history")
    safe = v["safety"]
    require(safe["cash_spend_usd"] == 0 and safe["forward_current_capture_source_only"] is True, "safety scope")
    require(all(value is False for key,value in safe.items() if key not in {"cash_spend_usd", "forward_current_capture_source_only"}), "closeout firewall")
    matrix = read(EVIDENCE / "route_matrix.json")
    expected = {"optionsDX", "Cryptarbitrage", "BRC", "CoinAPI", "Laevitas", "Tardis", "Volar", "crypto-data.io", "UWA", "CandleFeed", "ByKaranteli", "official_Deribit", "public_GitHub_witnesses"}
    require({r["route_id"] for r in matrix["routes"]} == expected and len(matrix["routes"]) == len(expected), "missing/duplicate route")
    require(all(not r["source_gate_pass"] and not r["outcomes_opened"] and not r["new_market_payload_opened"] and r["urls"] and r["evidence"] for r in matrix["routes"]), "matrix nonclaim/evidence error")
    m = read(EVIDENCE / "public_metadata_receipt.json")
    require(m["cash_spend_usd"] == 0 and not m["market_payload_requested"] and not m["outcomes_opened"] and not m["account_created"], "metadata firewall")
    wr = read(EVIDENCE / "workflow_receipts.json")
    require(wr["corrected_manual_rerun"]["run_id"] == v["census"]["workflow_run"] and wr["corrected_manual_rerun"]["conclusion"] == "success", "census lineage")
    require(wr["forward_manual_rerun"]["conclusion"] == "success" and not wr["forward_manual_rerun"]["protected_payload_locally_opened"], "forward lineage")
    require(wr["canonical_parent_sha"] == v["canonical_parent"]["commit"], "parent lineage mismatch")
    result = {"classification": "CLOSEOUT_INTEGRITY_PASS", "source_gate_pass": False,
              "verdict": v["canonical_classification"], "parent": v["parent_discovery_classification"],
              "checked_evidence_files": len(manifest["files"]), "retained_census_rows": len(rows),
              "free_intraday": len(free_intraday), "tardis_free_complete_anchor_pairs": free_paired,
              "commercial_calendar_days": len(days), "route_count": len(expected), "outcomes_computed": False}
    (EVIDENCE / "validator_receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
