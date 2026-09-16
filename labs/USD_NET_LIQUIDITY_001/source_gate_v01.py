#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import pathlib
import urllib.request
from datetime import date

LAB_ID = "USD-NET-LIQUIDITY-001"
MVE_ID = "UNL-FED-TGA-RRP-W1-001"
START = "2017-12-27"
END = "2024-12-18"
SERIES = {
    "WALCL": "millions_usd_weekly_wednesday",
    "WDTGAL": "millions_usd_weekly_wednesday",
    "RRPONTSYD": "billions_usd_daily_exact_wednesday",
}
MIN_ALIGNED = 350
MIN_DELTAS = 349
OUT = pathlib.Path(os.environ.get("UNL_OUT", "artifacts/usd_net_liquidity_source_v01"))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch_series(series_id: str) -> bytes:
    # Explicit observation cutoff is part of the scientific firewall.
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&cosd={START}&coed={END}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 USD-NET-LIQUIDITY-001 research-only"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    if not body:
        raise RuntimeError(f"EMPTY_SOURCE_BYTES:{series_id}")
    return body


def parse_series(series_id: str, body: bytes) -> dict[str, float]:
    text = body.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise RuntimeError(f"NO_ROWS:{series_id}")
    value_col = series_id
    if value_col not in rows[0]:
        candidates = [c for c in rows[0] if c != "observation_date"]
        if len(candidates) != 1:
            raise RuntimeError(f"VALUE_COLUMN_NOT_UNIQUE:{series_id}:{list(rows[0])}")
        value_col = candidates[0]
    out: dict[str, float] = {}
    for r in rows:
        ds = (r.get("observation_date") or r.get("DATE") or "").strip()
        if not ds:
            continue
        d = date.fromisoformat(ds)
        if ds < START or ds > END:
            raise RuntimeError(f"PROTECTED_DATE_RETURNED:{series_id}:{ds}")
        raw = (r.get(value_col) or "").strip()
        if raw in ("", "."):
            continue
        v = float(raw)
        if not math.isfinite(v):
            raise RuntimeError(f"NONFINITE:{series_id}:{ds}")
        if ds in out:
            raise RuntimeError(f"DUPLICATE_DATE:{series_id}:{ds}")
        out[ds] = v
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source_meta = {}
    parsed = {}
    for sid in SERIES:
        body = fetch_series(sid)
        p = OUT / f"{sid}_{START}_{END}.csv"
        p.write_bytes(body)
        source_meta[sid] = {
            "sha256": sha256_bytes(body),
            "byte_count": len(body),
            "file": p.name,
            "requested_start": START,
            "requested_end": END,
            "unit_contract": SERIES[sid],
        }
        parsed[sid] = parse_series(sid, body)

    walcl = parsed["WALCL"]
    tga = parsed["WDTGAL"]
    rrp = parsed["RRPONTSYD"]
    aligned = []
    for ds in sorted(set(walcl) & set(tga) & set(rrp)):
        d = date.fromisoformat(ds)
        if d.weekday() != 2:
            continue
        nl = walcl[ds] - tga[ds] - 1000.0 * rrp[ds]
        if not math.isfinite(nl):
            raise RuntimeError(f"NONFINITE_NET_LIQUIDITY:{ds}")
        aligned.append({
            "date": ds,
            "walcl_musd": walcl[ds],
            "wdtgal_musd": tga[ds],
            "rrp_busd": rrp[ds],
            "net_liquidity_musd": nl,
        })

    deltas = []
    for prev, cur in zip(aligned, aligned[1:]):
        dv = cur["net_liquidity_musd"] - prev["net_liquidity_musd"]
        deltas.append({
            "date": cur["date"],
            "previous_eligible_date": prev["date"],
            "delta_net_liquidity_musd": dv,
        })

    # Gate checks are source-only; no BTC data exists in this process.
    checks = {
        "aligned_wednesdays_ge_350": len(aligned) >= MIN_ALIGNED,
        "deltas_ge_349": len(deltas) >= MIN_DELTAS,
        "first_aligned_not_before_start": bool(aligned and aligned[0]["date"] >= START),
        "last_aligned_not_after_end": bool(aligned and aligned[-1]["date"] <= END),
        "all_exact_wednesdays": all(date.fromisoformat(r["date"]).weekday() == 2 for r in aligned),
        "btc_market_data_accessed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "access_2025": False,
        "access_2026": False,
    }
    passed = all(v for k, v in checks.items() if k not in {"btc_market_data_accessed", "returns_computed", "pnl_computed", "access_2025", "access_2026"})

    aligned_bytes = ("\n".join(json.dumps(r, sort_keys=True) for r in aligned) + "\n").encode()
    delta_bytes = ("\n".join(json.dumps(r, sort_keys=True) for r in deltas) + "\n").encode()
    (OUT / "aligned_net_liquidity_v01.jsonl").write_bytes(aligned_bytes)
    (OUT / "weekly_deltas_v01.jsonl").write_bytes(delta_bytes)

    manifest = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": "SOURCE_DATA_PASS" if passed else "DATA_FAILURE",
        "source_window": {"start": START, "end": END},
        "source_meta": source_meta,
        "aligned_wednesdays": len(aligned),
        "delta_rows": len(deltas),
        "first_aligned": aligned[0]["date"] if aligned else None,
        "last_aligned": aligned[-1]["date"] if aligned else None,
        "aligned_sha256": sha256_bytes(aligned_bytes),
        "deltas_sha256": sha256_bytes(delta_bytes),
        "checks": checks,
    }
    mb = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    (OUT / "source_gate_manifest_v01.json").write_bytes(mb)
    receipt = {
        **manifest,
        "manifest_sha256": sha256_bytes(mb),
        "outcome_evaluation_performed": False,
        "network_access_performed": True,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
    }
    (OUT / "source_gate_receipt_v01.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
