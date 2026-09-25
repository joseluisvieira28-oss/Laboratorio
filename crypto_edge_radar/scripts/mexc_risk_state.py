from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _parse_utc(value: Any) -> datetime:
    dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware UTC required")
    return dt.astimezone(timezone.utc)


def _reconciliations(root: Path):
    for path in root.rglob("POST_TRADE_RECONCILIATION.json"):
        try:
            yield path,_load(path)
        except Exception:
            continue


def build_state(*,preflight_path:Path,receipt_root:Path,now:datetime|None=None)->dict[str,Any]:
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    p=_load(preflight_path)
    checks=p.get("checks") or {}
    equity=float((checks.get("account") or {}).get("equity_usdt"))
    if equity<=0:
        raise ValueError("positive equity required")
    open_positions=int((checks.get("positions") or {}).get("open_position_count",999))

    day_start=now.replace(hour=0,minute=0,second=0,microsecond=0)
    rolling_7d_start=now-timedelta(days=7)
    daily_loss_usdt=0.0
    rolling_7d_loss_usdt=0.0
    counted=[]
    for path,row in _reconciliations(receipt_root):
        try:
            closed=_parse_utc(row["closed_at_utc"])
            pnl=float(row["realized_net_pnl_usdt"])
        except Exception:
            continue
        loss=max(0.0,-pnl)
        if closed>=week_start:
            weekly_loss_usdt+=loss
        if closed>=day_start:
            daily_loss_usdt+=loss
        counted.append(str(path))

    active=[]
    planned_fraction=0.0
    for path in receipt_root.rglob("ACTIVE_TRADE_STATE.json"):
        try:
            row=_load(path)
        except Exception:
            continue
        if row.get("state") not in ("FILLED","EXIT_PENDING"):
            continue
        if (path.parent/"POST_TRADE_RECONCILIATION.json").exists():
            continue
        frac=float(row.get("planned_risk_fraction_equity",0))
        if frac<0:
            raise ValueError("negative planned risk fraction")
        planned_fraction+=frac
        active.append(str(path))

    # Exchange truth dominates local receipt count if they disagree.
    open_micro_live_positions=max(open_positions,len(active))
    status="PASS"
    blockers=[]
    if p.get("pass") is not True:
        blockers.append("AUTHENTICATED_PREFLIGHT_NOT_PASS")
    if open_positions!=0 and not active:
        blockers.append("UNRECONCILED_EXCHANGE_POSITION_PRESENT")
    if blockers:
        status="FAIL_CLOSED"

    return {
        "risk_state_id":"MEXC_ACCOUNT_RISK_STATE_V0.1",
        "status":status,
        "blockers":blockers,
        "as_of_utc":now.isoformat().replace("+00:00","Z"),
        "equity_usdt":equity,
        "daily_realized_loss_usdt":daily_loss_usdt,
        "weekly_realized_loss_usdt":rolling_7d_loss_usdt,
        "daily_realized_loss_fraction_equity":daily_loss_usdt/equity,
        "weekly_realized_loss_fraction_equity":rolling_7d_loss_usdt/equity,
        "concurrent_planned_risk_fraction_equity":planned_fraction,
        "open_micro_live_positions":open_micro_live_positions,
        "local_active_trade_receipts":active,
        "reconciliations_scanned":counted,
        "policy":{
            "planned_validation_margin_fraction_equity":0.001,
            "max_simultaneous_planned_risk_fraction_equity":0.003,
            "daily_stop_fraction_equity":0.003,
            "weekly_stop_fraction_equity":0.0075
        }
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--preflight",required=True)
    ap.add_argument("--receipt-root",default="live_receipts")
    ap.add_argument("--out",default="mexc_account_risk_state.json")
    args=ap.parse_args()
    state=build_state(
        preflight_path=Path(args.preflight),
        receipt_root=Path(args.receipt_root),
    )
    Path(args.out).write_text(json.dumps(state,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":state["status"],"out":str(Path(args.out).resolve()),"blockers":state["blockers"]},indent=2))
    return 0 if state["status"]=="PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())
