import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDENTITY = HERE / "FULL_STATIC_TOKEN_IDENTITY_MAP_V01.json"
OUT = HERE / "source_probe_output_v07" / "TUE_FULL_STATIC_IDENTITY_MANIFEST_V01.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main(argv):
    if len(argv) != 3:
        print("usage: build_full_static_identity_manifest_v01.py <2023-json> <2024-json>")
        return 2
    a = load(Path(argv[1]))
    b = load(Path(argv[2]))
    identity = load(IDENTITY)
    assert identity["status"] == "FROZEN_PRE_FULL_STATIC_ROUTE_CHECK"
    mapping = identity["provider_adapter_to_symbol"]
    quarantine = identity["quarantine"]

    raw = []
    exclusions = []
    for src in (a, b):
        for event in src.get("events", []):
            file = str(event.get("file", ""))
            if file in quarantine:
                exclusions.append({"file": file, "reason": "IDENTITY_QUARANTINE", "scheduled_at_utc": event.get("scheduled_at_utc")})
                continue
            symbol = mapping.get(file)
            if not symbol:
                exclusions.append({"file": file, "reason": "UNMAPPED_IDENTITY", "scheduled_at_utc": event.get("scheduled_at_utc")})
                continue
            if file == "liquity.ts" and str(event.get("snapshot", "")).startswith("2023-"):
                exclusions.append({"file": file, "reason": "LIQUITY_2023_LUSD_LQTY_IDENTITY_CONFLICT", "scheduled_at_utc": event.get("scheduled_at_utc")})
                continue
            ts = int(event["timestamp"])
            year = int(str(event["scheduled_at_utc"])[0:4])
            if year not in (2023, 2024):
                raise RuntimeError("date firewall breach")
            if float(event.get("known_lead_days", -1)) < 30:
                exclusions.append({"file": file, "reason": "KNOWN_AHEAD_LT_30D", "scheduled_at_utc": event.get("scheduled_at_utc")})
                continue
            if float(event.get("scheduled_unlock_tokens", 0)) <= 0:
                exclusions.append({"file": file, "reason": "NON_POSITIVE_UNLOCK_AMOUNT", "scheduled_at_utc": event.get("scheduled_at_utc")})
                continue
            x = dict(event)
            x["symbol"] = symbol
            x["identity_status"] = "FROZEN_PRE_ROUTE"
            raw.append(x)

    # Cross-snapshot duplicates are the same project event at the same exact timestamp.
    # Prefer the earlier immutable snapshot because it proves the longer PIT lead.
    by_key = {}
    conflicts = []
    for event in sorted(raw, key=lambda x: (x["symbol"], int(x["timestamp"]), str(x.get("known_at_utc", "")))):
        key = (event["symbol"], int(event["timestamp"]))
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = event
            continue
        a_amt = float(prev["scheduled_unlock_tokens"])
        b_amt = float(event["scheduled_unlock_tokens"])
        tol = max(1e-9, 1e-9 * max(abs(a_amt), abs(b_amt)))
        if abs(a_amt - b_amt) > tol:
            conflicts.append({
                "symbol": event["symbol"],
                "timestamp": int(event["timestamp"]),
                "amount_a": a_amt,
                "amount_b": b_amt,
                "snapshot_a": prev.get("snapshot"),
                "snapshot_b": event.get("snapshot"),
            })
            continue
        # earlier known_at is retained deterministically
        if str(event.get("known_at_utc", "")) < str(prev.get("known_at_utc", "")):
            by_key[key] = event

    if conflicts:
        classification = "BLOCKED_SOURCE_CONFLICT"
    else:
        classification = "PASS_IDENTITY_PREFREEZE"
    events = [by_key[k] for k in sorted(by_key)]
    symbols = sorted({x["symbol"] for x in events})
    years = sorted({int(str(x["scheduled_at_utc"])[0:4]) for x in events})
    receipt = {
        "lab_id": "TOKEN-UNLOCK-EVENT-001",
        "mve_id": "TUE-CLIFF-ADV30-001",
        "mode": "SOURCE_ONLY_FULL_STATIC_IDENTITY_MANIFEST_V01",
        "classification": classification,
        "raw_event_count_before_dedupe": len(raw),
        "deduplicated_event_count": len(events),
        "distinct_tokens": len(symbols),
        "tokens": symbols,
        "years": years,
        "identity_quarantine_count": sum(1 for x in exclusions if x["reason"] == "IDENTITY_QUARANTINE"),
        "excluded_event_count": len(exclusions),
        "cross_snapshot_conflict_count": len(conflicts),
        "identity_map_sha256": hashlib.sha256(IDENTITY.read_bytes()).hexdigest(),
        "manifest_fingerprint_sha256": fingerprint(events),
        "guards": {
            "binance_route_checked": False,
            "market_prices_accessed": False,
            "returns_computed": False,
            "pnl_computed": False,
            "year_2025_opened": False,
            "year_2026_opened": False,
            "live_trading": False,
            "exchange_mutation": False
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"receipt": receipt, "events": events, "exclusions": exclusions, "conflicts": conflicts}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("NO BINANCE ROUTE / NO PRICE VALUES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED")
    return 0 if not conflicts else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
