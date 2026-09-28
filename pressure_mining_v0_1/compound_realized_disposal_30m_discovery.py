#!/usr/bin/env python3
"""
Protected 2025 Discovery runner for COMPOUND-REALIZED-DISPOSAL-FLOW-001.

IMPORTANT:
- Canonical authority is the 30m freeze at commit 2191bbf741ced5f801d8ae4034bd126c3b91cbc8.
- This module is intentionally fail-closed.
- Real-data execution requires BOTH:
  1) environment CRYPTO_LAB_PROTECTED_OUTCOME_AUTHORITY set to the exact frozen token below; and
  2) repository marker .github/authorities/compound-realized-disposal-flow-001-2025.authorized
- The marker is NOT created by preflight.
"""
import math, os, sys

AUTH_TOKEN="COMPOUND-REALIZED-DISPOSAL-FLOW-001::PROTECTED-2025-ECONOMIC-DISCOVERY::30M::V0.1"
AUTH_MARKER=".github/authorities/compound-realized-disposal-flow-001-2025.authorized"

ASSET_MAP={
 "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":"ETHUSDT",
 "0x514910771af9ca656af840dff83e8264ecf986ca":"LINKUSDT",
 "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984":"UNIUSDT",
 "0xc00e94cb662c3520282e6f5717214004a7f26888":"COMPUSDT",
}
BENCHMARK="BTCUSDT"
HORIZON_MINUTES=30
BASE_COST_BPS=20.0
STRESS_COST_BPS=30.0
BOOTSTRAP_SEED=20260927
BOOTSTRAP_REPS=10000

def require_authority(repo_root="."):
    token=os.environ.get("CRYPTO_LAB_PROTECTED_OUTCOME_AUTHORITY","")
    marker=os.path.join(repo_root,AUTH_MARKER)
    if token!=AUTH_TOKEN or not os.path.isfile(marker):
        raise PermissionError("PROTECTED_OUTCOME_LOCKED: exact authority token and repository marker are both required")

def first_complete_minute_open_ms(block_ts_seconds):
    return ((int(block_ts_seconds)//60)+1)*60*1000

def exit_open_ms(entry_open_ms):
    return int(entry_open_ms)+HORIZON_MINUTES*60*1000

def rel_log_bps(asset_entry,asset_exit,btc_entry,btc_exit):
    if min(asset_entry,asset_exit,btc_entry,btc_exit)<=0: raise ValueError("prices must be positive")
    return 10000.0*(math.log(asset_exit/asset_entry)-math.log(btc_exit/btc_entry))

def net_short_rel_bps(rel_bps,cost_bps):
    return -float(rel_bps)-float(cost_bps)

def synthetic_self_test():
    assert set(ASSET_MAP.values())=={"ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"}
    assert BENCHMARK=="BTCUSDT" and HORIZON_MINUTES==30
    assert BASE_COST_BPS==20.0 and STRESS_COST_BPS==30.0
    # Block at hh:mm:12 => first complete minute starts next minute.
    assert first_complete_minute_open_ms(1_800_000_012)==((1_800_000_012//60)+1)*60*1000
    e=first_complete_minute_open_ms(1_800_000_012)
    assert exit_open_ms(e)-e==30*60*1000
    # Asset falls 1%, BTC flat => negative relative, positive gross short-rel.
    r=rel_log_bps(100.0,99.0,100.0,100.0)
    assert r<0 and net_short_rel_bps(r,0)>0
    assert abs((net_short_rel_bps(r,20)-net_short_rel_bps(r,30))-10.0)<1e-12
    # Lock must fail with no env+marker.
    failed=False
    try: require_authority(".")
    except PermissionError: failed=True
    assert failed
    return True

def main():
    if "--synthetic-self-test" in sys.argv:
        synthetic_self_test()
        print("SYNTHETIC_SELF_TEST_PASS")
        print("PROTECTED_OUTCOME_LOCK_PASS")
        return 0
    require_authority(".")
    raise SystemExit("AUTHORIZED_RUNNER_SCAFFOLD_ONLY: implementation must be finalized under the same canonical contract before protected execution")

if __name__=="__main__":
    raise SystemExit(main())
