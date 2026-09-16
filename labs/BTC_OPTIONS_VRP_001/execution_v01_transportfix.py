#!/usr/bin/env python3
"""Transport-only launcher for OVRP-EXEC-ATM30-7D-STATICDELTA-001.

Scientific rules are unchanged. The canonical runner attempted to exhaust the
entire dense BTC-PERPETUAL 30-minute tape before applying the already-frozen
"first direction-matched trade" rule. This launcher substitutes only a
streaming first-match acquisition helper for the two perpetual fill lookups.

Authority/receipt: Drive 1d0mDSGqRXNfOF0sdLJBYLw9abofu76Fklq7xafBGA-k
"""
from pathlib import Path
import hashlib

P = Path("labs/BTC_OPTIONS_VRP_001/execution_v01.py")
src = P.read_text(encoding="utf-8")
original_sha = hashlib.sha256(src.encode("utf-8")).hexdigest()

needle = '''def norm_cdf(x):\n    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n'''
helper = '''def fetch_first_direction_instrument(instrument, direction, start_ms, end_ms, count=1000, max_pages=100):\n    # Transport-only remediation: preserve the frozen first-valid-trade rule\n    # while avoiding full exhaustion of a dense BTC-PERPETUAL window.\n    hashes = []\n    cursor = start_ms\n    seen = set()\n    for _ in range(max_pages):\n        payload, h = get_json(HISTORY, "/get_last_trades_by_instrument_and_time", {\n            "instrument_name": instrument, "start_timestamp": cursor,\n            "end_timestamp": end_ms, "count": count, "sorting": "asc", "include_old": "true"\n        })\n        hashes.append(h)\n        rows, has_more = trade_list(payload)\n        rows = sorted(rows, key=lambda x: (int(x.get("timestamp", -1)), str(x.get("trade_id", ""))))\n        last_ts = None\n        new = 0\n        for t in rows:\n            ts = int(t.get("timestamp", -1))\n            tid = str(t.get("trade_id", ""))\n            key = (ts, tid, str(t.get("price", "")), str(t.get("amount", "")))\n            if key in seen:\n                continue\n            seen.add(key); new += 1\n            if last_ts is None or ts > last_ts:\n                last_ts = ts\n            if start_ms <= ts <= end_ms and t.get("direction") == direction and is_valid_screen_trade(t):\n                if ts >= PROTECTED_MS:\n                    raise RuntimeError("Protected-period trade encountered")\n                return t, hashes\n        if not has_more or not rows:\n            return None, hashes\n        if last_ts is None or last_ts >= end_ms:\n            return None, hashes\n        next_cursor = last_ts\n        if next_cursor <= cursor and new == 0:\n            next_cursor = cursor + 1\n        cursor = next_cursor\n    raise RuntimeError(f"First-direction pagination exceeded max_pages for {instrument}")\n\n\ndef norm_cdf(x):\n    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n'''
if needle not in src:
    raise RuntimeError("Transport-fix insertion anchor not found")
src = src.replace(needle, helper, 1)

old_entry = '''            perp_rows, perp_entry_hashes = fetch_trades_instrument("BTC-PERPETUAL", hstart, hend)\n            perp_in = first_direction(perp_rows, hdir, hstart, hend)\n'''
new_entry = '''            perp_in, perp_entry_hashes = fetch_first_direction_instrument("BTC-PERPETUAL", hdir, hstart, hend)\n'''
old_exit = '''            perp_rows2, perp_exit_hashes = fetch_trades_instrument("BTC-PERPETUAL", hstart2, hend2)\n            perp_out = first_direction(perp_rows2, hdir2, hstart2, hend2)\n'''
new_exit = '''            perp_out, perp_exit_hashes = fetch_first_direction_instrument("BTC-PERPETUAL", hdir2, hstart2, hend2)\n'''
if old_entry not in src or old_exit not in src:
    raise RuntimeError("Transport-fix perpetual call anchors not found")
src = src.replace(old_entry, new_entry, 1).replace(old_exit, new_exit, 1)
patched_sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
print(f"TRANSPORT_FIX_ORIGINAL_SHA256={original_sha}")
print(f"TRANSPORT_FIX_PATCHED_RUNTIME_SHA256={patched_sha}")
print("TRANSPORT_FIX_SCOPE=BTC_PERPETUAL_FIRST_DIRECTION_ACQUISITION_ONLY")
exec(compile(src, str(P), "exec"), {"__name__": "__main__", "__file__": str(P)})
