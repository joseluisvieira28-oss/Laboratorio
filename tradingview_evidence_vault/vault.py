#!/usr/bin/env python3
"""Evidence Vault V0.1 for TV-FOOTPRINT-CALIBRATION-001.

Input: newline-delimited Render log messages or JSON log exports containing
TVFP_RECEIPT records.
Output: canonical deduplicated JSONL corpus + manifest with SHA256 and hash chain.

This tool never modifies market data, thresholds, or outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

LOG_PREFIX = "TVFP_RECEIPT "
LAB_ID = "TV-FOOTPRINT-CALIBRATION-001"
SENSOR_VERSION = "MM-V1"
SYMBOL = "BINANCE:BTCUSDT"
TIMEFRAME = "5"
FORWARD_START_MS = 1790247600000
BAR_MS = 300000


class VaultError(ValueError):
    pass


def canonical_json(obj: object) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def payload_sha(payload: dict) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def parse_receipt_text(text: str) -> dict:
    idx = text.find(LOG_PREFIX)
    if idx < 0:
        raise VaultError("TVFP_RECEIPT prefix missing")
    raw = text[idx + len(LOG_PREFIX):].strip()
    try:
        rec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VaultError(f"invalid receipt JSON: {exc}") from exc
    return rec


def validate_receipt(rec: dict) -> dict:
    if rec.get("record_type") != "TVFP_RECEIPT":
        raise VaultError("record_type mismatch")
    if rec.get("trading_authority") != "NONE":
        raise VaultError("trading_authority mismatch")

    p = rec.get("payload")
    if not isinstance(p, dict):
        raise VaultError("payload missing")

    expected = {
        "lab_id": LAB_ID,
        "sensor_version": SENSOR_VERSION,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
    }
    for k, v in expected.items():
        if p.get(k) != v:
            raise VaultError(f"{k} mismatch")

    bo = p.get("bar_open_ms")
    bc = p.get("bar_close_ms")
    if not isinstance(bo, int) or not isinstance(bc, int):
        raise VaultError("bar timestamps must be integer")
    if bo % BAR_MS != 0 or bc - bo != BAR_MS:
        raise VaultError("invalid 5-minute alignment")
    if bc < FORWARD_START_MS:
        raise VaultError("pre-boundary receipt")

    expected_key = f"{LAB_ID}|{SENSOR_VERSION}|{SYMBOL}|{TIMEFRAME}|{bc}"
    if rec.get("evidence_key") != expected_key:
        raise VaultError("evidence_key mismatch")

    actual_sha = payload_sha(p)
    if rec.get("payload_sha256") != actual_sha:
        raise VaultError("payload_sha256 mismatch")

    return rec


def load_input(paths: Iterable[Path]) -> list[dict]:
    out = []
    for path in paths:
        with path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue

                # Accept either raw receipt lines or Render API JSON objects.
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    obj = None

                texts = []
                if isinstance(obj, dict):
                    if isinstance(obj.get("message"), str):
                        texts.append(obj["message"])
                    elif obj.get("record_type") == "TVFP_RECEIPT":
                        out.append(validate_receipt(obj))
                        continue
                else:
                    texts.append(line)

                for text in texts:
                    if LOG_PREFIX not in text:
                        continue
                    try:
                        out.append(validate_receipt(parse_receipt_text(text)))
                    except VaultError as exc:
                        raise VaultError(f"{path}:{line_no}: {exc}") from exc
    return out


def deduplicate(receipts: list[dict]) -> tuple[list[dict], dict]:
    by_key: dict[str, dict] = {}
    exact_dupes = 0
    conflicts = []

    for rec in receipts:
        key = rec["evidence_key"]
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = rec
            continue

        if prev["payload_sha256"] == rec["payload_sha256"]:
            exact_dupes += 1
        else:
            conflicts.append(
                {
                    "evidence_key": key,
                    "sha_a": prev["payload_sha256"],
                    "sha_b": rec["payload_sha256"],
                }
            )

    if conflicts:
        raise VaultError(
            "conflicting receipts for same evidence key: "
            + json.dumps(conflicts, separators=(",", ":"))
        )

    rows = sorted(by_key.values(), key=lambda r: r["payload"]["bar_close_ms"])
    return rows, {
        "input_receipts": len(receipts),
        "unique_receipts": len(rows),
        "exact_duplicates_removed": exact_dupes,
        "conflicts": 0,
    }


def continuity(rows: list[dict]) -> dict:
    if not rows:
        return {
            "first_bar_close_ms": None,
            "last_bar_close_ms": None,
            "expected_slots": 0,
            "missing_slots": 0,
            "missing_bar_close_ms": [],
        }

    closes = [r["payload"]["bar_close_ms"] for r in rows]
    expected = list(range(closes[0], closes[-1] + BAR_MS, BAR_MS))
    have = set(closes)
    missing = [x for x in expected if x not in have]
    return {
        "first_bar_close_ms": closes[0],
        "last_bar_close_ms": closes[-1],
        "expected_slots": len(expected),
        "missing_slots": len(missing),
        "missing_bar_close_ms": missing,
    }


def write_vault(rows: list[dict], outdir: Path, snapshot_id: str) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    corpus_path = outdir / f"{snapshot_id}.jsonl"
    manifest_path = outdir / f"{snapshot_id}.manifest.json"

    chain_prev = "0" * 64
    corpus_lines = []
    for rec in rows:
        normalized = {
            "evidence_key": rec["evidence_key"],
            "payload_sha256": rec["payload_sha256"],
            "received_at": rec["received_at"],
            "payload": rec["payload"],
            "trading_authority": "NONE",
        }
        line_bytes = canonical_json(normalized)
        chain = hashlib.sha256(
            bytes.fromhex(chain_prev) + line_bytes
        ).hexdigest()
        normalized["chain_sha256"] = chain
        chain_prev = chain
        corpus_lines.append(canonical_json(normalized).decode("utf-8"))

    corpus_text = "\n".join(corpus_lines) + ("\n" if corpus_lines else "")
    corpus_path.write_text(corpus_text, encoding="utf-8")
    corpus_digest = hashlib.sha256(corpus_text.encode("utf-8")).hexdigest()

    cont = continuity(rows)
    manifest = {
        "vault_version": "TV-EVIDENCE-VAULT-V0.1",
        "snapshot_id": snapshot_id,
        "lab_id": LAB_ID,
        "sensor_version": SENSOR_VERSION,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "forward_start_ms": FORWARD_START_MS,
        "unique_receipts": len(rows),
        "first_bar_close_ms": cont["first_bar_close_ms"],
        "last_bar_close_ms": cont["last_bar_close_ms"],
        "expected_slots": cont["expected_slots"],
        "missing_slots": cont["missing_slots"],
        "missing_bar_close_ms": cont["missing_bar_close_ms"],
        "corpus_file": corpus_path.name,
        "corpus_sha256": corpus_digest,
        "terminal_chain_sha256": chain_prev,
        "trading_authority": "NONE",
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--snapshot-id", required=True)
    args = ap.parse_args()

    receipts = load_input([Path(p) for p in args.inputs])
    rows, stats = deduplicate(receipts)
    manifest = write_vault(rows, Path(args.outdir), args.snapshot_id)

    print(json.dumps({**stats, **manifest}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
