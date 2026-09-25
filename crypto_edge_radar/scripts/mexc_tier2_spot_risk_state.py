from __future__ import annotations

import argparse,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Any

def _load(p:Path)->dict[str,Any]:
    out=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(out,dict): raise ValueError("JSON object required")
    return out

def _utc(v:Any)->datetime:
    dt=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("timezone aware required")
    return dt.astimezone(timezone.utc)

def build_state(*,preflight_path:Path,receipt_root:Path,now:datetime|None=None)->dict[str,Any]:
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    pf=_load(preflight_path)
    day=now.replace(hour=0,minute=0,second=0,microsecond=0); start7=now-timedelta(days=7)
    dl=0.0; wl=0.0; reconciled=[]
    for p in receipt_root.rglob("POST_TRADE_RECONCILIATION.json"):
        try:
            row=_load(p); closed=_utc(row["closed_at_utc"]); pnl=float(row["realized_net_pnl_usdt"])
        except Exception: continue
        loss=max(0.0,-pnl)
        if closed>=day: dl+=loss
        if closed>=start7: wl+=loss
        reconciled.append(str(p))
    active=[]
    for p in receipt_root.rglob("ACTIVE_TRADE_STATE.json"):
        try: row=_load(p)
        except Exception: continue
        if row.get("state") in ("FILLED","EXIT_PENDING") and not (p.parent/"POST_TRADE_RECONCILIATION.json").exists():
            active.append(str(p))
    blockers=[]
    if pf.get("pass") is not True: blockers.append("SPOT_PREFLIGHT_NOT_PASS")
    if int((((pf.get("checks") or {}).get("orders") or {}).get("open_order_count",999)))!=0: blockers.append("OPEN_SPOT_ORDER_PRESENT")
    if dl>=2.0: blockers.append("DAILY_2_USDT_KILL_ACTIVE")
    if wl>=5.0: blockers.append("ROLLING_7D_5_USDT_KILL_ACTIVE")
    if len(active)>1: blockers.append("MULTIPLE_MICRO_LIVE_POSITIONS_PRESENT")
    return {
        "risk_state_id":"MEXC_TIER2_SPOT_RISK_STATE_V0.3","status":"PASS" if not blockers else "FAIL_CLOSED",
        "blockers":blockers,"as_of_utc":now.isoformat().replace("+00:00","Z"),
        "daily_realized_loss_usdt":dl,"rolling_7d_realized_loss_usdt":wl,
        "open_micro_live_positions":len(active),"local_active_trade_receipts":active,
        "reconciliations_scanned":reconciled,
        "policy":{"max_notional_usdt":10.0,"max_concurrent_positions":1,"daily_realized_loss_kill_usdt":2.0,"rolling_7d_realized_loss_kill_usdt":5.0}
    }

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--preflight",required=True); ap.add_argument("--receipt-root",default="live_receipts"); ap.add_argument("--out",default="mexc_tier2_spot_risk_state.json")
    args=ap.parse_args(); state=build_state(preflight_path=Path(args.preflight),receipt_root=Path(args.receipt_root))
    Path(args.out).write_text(json.dumps(state,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":state["status"],"blockers":state["blockers"],"out":str(Path(args.out).resolve())},indent=2))
    return 0 if state["status"]=="PASS" else 2

if __name__=="__main__": raise SystemExit(main())
