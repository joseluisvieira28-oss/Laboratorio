from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


class CorrectionOverlayError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict):
        raise CorrectionOverlayError(f"JSON object required: {path}")
    return payload


def _all_values(obj: Any, key: str) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for k, value in obj.items():
            if k == key and value is not None:
                out.append(str(value))
            out.extend(_all_values(value, key))
    elif isinstance(obj, list):
        for value in obj:
            out.extend(_all_values(value, key))
    return out


def _finite(value: Any, name: str) -> float:
    out=float(value)
    if not math.isfinite(out):
        raise CorrectionOverlayError(f"{name} must be finite")
    return out


def build_overlay(*,catalog_path:Path,receipt_root:Path)->dict[str,Any]:
    catalog=_load(catalog_path)
    entries=catalog.get("entries")
    if not isinstance(entries,list) or not entries:
        raise CorrectionOverlayError("catalog entries missing")
    reconciliations=[]
    for path in receipt_root.rglob("POST_TRADE_RECONCILIATION.json"):
        try:
            row=_load(path)
        except Exception as exc:
            raise CorrectionOverlayError(
                f"invalid reconciliation {path}:{type(exc).__name__}"
            ) from exc
        reconciliations.append((path,row))

    out=[]
    for expected in entries:
        if not isinstance(expected,dict):
            raise CorrectionOverlayError("catalog entry must be object")
        signal=str(expected.get("signal_identity") or "")
        matches=[(p,r) for p,r in reconciliations if str(r.get("signal_identity") or "")==signal]
        if len(matches)!=1:
            raise CorrectionOverlayError(
                f"{signal}: expected exactly one reconciliation, got {len(matches)}"
            )
        path,row=matches[0]
        stored=_finite(row.get("realized_net_pnl_usdt"),"stored realized net")
        expected_stored=_finite(expected.get("stored_net_pnl_usdt"),"catalog stored net")
        if abs(stored-expected_stored)>1e-12:
            raise CorrectionOverlayError(f"{signal}: stored net mismatch")

        session=path.parent
        fill=session/"FILL_RECEIPT.json"
        if not fill.exists():
            raise CorrectionOverlayError(f"{signal}: FILL_RECEIPT missing")
        fill_payload=_load(fill)
        entry_ids=set(_all_values(fill_payload,"orderId"))
        if str(expected.get("entry_order_id")) not in entry_ids:
            raise CorrectionOverlayError(f"{signal}: entry order identity mismatch")

        exit_ids:set[str]=set()
        for ack_path in session.glob("EXIT_EXCHANGE_ACK*.json"):
            exit_ids.update(_all_values(_load(ack_path),"orderId"))
        legacy=session/"EXIT_EXCHANGE_ACK.json"
        if legacy.exists():
            exit_ids.update(_all_values(_load(legacy),"orderId"))
        if str(expected.get("exit_order_id")) not in exit_ids:
            raise CorrectionOverlayError(f"{signal}: exit order identity mismatch")

        raw=path.read_bytes()
        out.append({
            "signal_identity":signal,
            "original_receipt_path":str(path),
            "original_receipt_sha256":hashlib.sha256(raw).hexdigest(),
            "entry_order_id":str(expected["entry_order_id"]),
            "exit_order_id":str(expected["exit_order_id"]),
            "stored_net_pnl_usdt":stored,
            "corrected_realized_net_pnl_usdt":_finite(
                expected.get("corrected_realized_net_pnl_usdt"),
                "catalog corrected net",
            ),
            "entry_fee_usdt":_finite(expected.get("entry_fee_usdt"),"entry fee"),
            "exit_fee_usdt":_finite(expected.get("exit_fee_usdt"),"exit fee"),
        })

    return {
        "overlay_id":"OPTIONS_V21_LOCAL_HASH_BOUND_PNL_CORRECTION_V0.1",
        "catalog_id":catalog.get("catalog_id"),
        "catalog_source_commit":catalog.get("source_commit"),
        "catalog_source_evidence_git_blob_sha":catalog.get("source_evidence_git_blob_sha"),
        "original_receipts_mutated":False,
        "entry_count":len(out),
        "entries":out,
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--catalog",required=True)
    ap.add_argument("--receipt-root",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    try:
        overlay=build_overlay(
            catalog_path=Path(args.catalog),
            receipt_root=Path(args.receipt_root),
        )
    except Exception as exc:
        print(json.dumps({
            "status":"FAIL_CLOSED",
            "error":f"{type(exc).__name__}:{exc}",
            "original_receipts_mutated":False,
        },indent=2))
        return 2
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(out.suffix+".tmp")
    tmp.write_text(json.dumps(overlay,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    tmp.replace(out)
    print(json.dumps({
        "status":"PASS_OVERLAY_BUILT",
        "entries":len(overlay["entries"]),
        "out":str(out.resolve()),
        "original_receipts_mutated":False,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
