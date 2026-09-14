import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "source_evidence_v01.json"
OUT = HERE / "SOURCE_GATE_RECEIPT_V01.json"

MIN_EVENTS = 40
MIN_TOKENS = 15
MIN_YEARS = 2

raw = json.loads(EVIDENCE.read_text(encoding="utf-8"))
assert raw["lab_id"] == "TOKEN-UNLOCK-EVENT-001"
assert raw["mve_id"] == "TUE-CLIFF-ADV30-001"
assert raw["outcomes_opened"] is False
assert raw["year_2025_opened"] is False
assert raw["year_2026_opened"] is False

sources = {x["id"]: x for x in raw["sources"]}
volume = sources["binance_public_data"]
primary = sources["primary_project_or_contract_evidence"]

volume_route_pass = all([
    volume.get("historical_2021_2024_route") is True,
    volume.get("base_asset_volume_field") is True,
    volume.get("integrity_checksum_route") is True,
])

pit_events = int(primary.get("eligible_events_with_complete_pit_receipts", 0))
pit_event_gate_pass = pit_events >= MIN_EVENTS

# Token/year dispersion cannot pass until a concrete PIT-qualified manifest exists.
distinct_tokens = 0
calendar_years = 0
dispersion_gate_pass = (
    distinct_tokens >= MIN_TOKENS and calendar_years >= MIN_YEARS
)

if not volume_route_pass:
    classification = "SOURCE_DATA_INADEQUATE"
elif not pit_event_gate_pass or not dispersion_gate_pass:
    classification = "SOURCE_PIT_PROVENANCE_INCOMPLETE"
else:
    classification = "SOURCE_DATA_FEASIBLE"

receipt = {
    "lab_id": raw["lab_id"],
    "mve_id": raw["mve_id"],
    "mode": "SOURCE_GATE_ONLY",
    "classification": classification,
    "gates": {
        "binance_pre_event_volume_route": volume_route_pass,
        "required_pit_events": MIN_EVENTS,
        "pit_events_proven": pit_events,
        "required_distinct_tokens": MIN_TOKENS,
        "distinct_tokens_proven": distinct_tokens,
        "required_calendar_years": MIN_YEARS,
        "calendar_years_proven": calendar_years,
        "pit_event_manifest_pass": pit_event_gate_pass,
        "dispersion_gate_pass": dispersion_gate_pass,
    },
    "guards": {
        "returns_computed": False,
        "pnl_computed": False,
        "profit_factor_computed": False,
        "forward_prices_opened": False,
        "year_2025_opened": False,
        "year_2026_opened": False,
        "live_trading": False,
        "exchange_mutation": False,
    },
    "reason": (
        "Historical Binance base-volume infrastructure is source-feasible, but no systematic "
        "2021-2024 event manifest currently proves, event by event, that exact unlock time and "
        "amount were publicly known at least 30 days before release. Current aggregator reconstructions "
        "and the public 2026 replication dataset are discovery aids, not sufficient PIT authority."
    ),
    "next_authorized_action": (
        "Build an outcome-blind 2021-2024 candidate event manifest from sources that can be queried "
        "without opening 2025/2026, then attach primary pre-event publication/contract evidence for "
        "each event. Re-run this gate. Discovery remains CLOSED until SOURCE_DATA_FEASIBLE."
    ),
}
OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2, sort_keys=True))
print("NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED")
