from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen

DEFAULT_CANARY_URL="https://crypto-edge-radar-v05-canary.onrender.com/api/state"


class CanaryWakeError(RuntimeError):
    pass


def validate_public_shadow_state(state:dict[str,Any])->dict[str,Any]:
    if state.get("health") not in {"OK","STARTING"}:
        raise CanaryWakeError(f"unhealthy canary:{state.get('health')}")
    if state.get("mode")!="PUBLIC_SHADOW_ONLY":
        raise CanaryWakeError(f"unexpected mode:{state.get('mode')}")
    forbidden={
        "authenticated_exchange_api_used":state.get("authenticated_exchange_api_used"),
        "orders_created":state.get("orders_created"),
        "exchange_mutation_performed":state.get("exchange_mutation_performed"),
        "live_capital_enabled":state.get("live_capital_enabled"),
    }
    if any(value is not False for value in forbidden.values()):
        raise CanaryWakeError(f"hard safety violation:{forbidden}")
    if "tfg" not in state or "options_v21" not in state:
        raise CanaryWakeError("forward engine state missing")
    return {
        "status":"PASS_PUBLIC_BOUNDARY_WAKE",
        "health":state.get("health"),
        "mode":state.get("mode"),
        "evidence_backend":state.get("evidence_backend"),
        "evidence_chain_ok":state.get("evidence_chain_ok"),
        "tfg_status":(state.get("tfg") or {}).get("status"),
        "options_status":(state.get("options_v21") or {}).get("status"),
        "authenticated_exchange_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
        "live_capital_enabled":False,
    }


def fetch_public_shadow_state(url:str=DEFAULT_CANARY_URL,timeout:int=180)->dict[str,Any]:
    req=Request(url,method="GET",headers={"User-Agent":"crypto-edge-radar/0.11-boundary-check"})
    try:
        with urlopen(req,timeout=timeout) as response:
            body=response.read()
            if response.status!=200 or not body:
                raise CanaryWakeError(f"canary HTTP/empty:{response.status}")
    except Exception as exc:
        if isinstance(exc,CanaryWakeError):
            raise
        raise CanaryWakeError(f"canary unavailable:{type(exc).__name__}:{exc}") from exc
    try:
        obj=json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise CanaryWakeError("canary returned non-JSON bytes") from exc
    if not isinstance(obj,dict):
        raise CanaryWakeError("canary state is not an object")
    return obj


def main()->int:
    url=os.getenv("RADAR_CANARY_URL",DEFAULT_CANARY_URL)
    receipt=validate_public_shadow_state(fetch_public_shadow_state(url))
    print(json.dumps(receipt,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
