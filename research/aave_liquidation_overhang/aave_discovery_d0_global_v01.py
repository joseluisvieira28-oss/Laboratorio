#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
PHASE = "DISCOVERY_D0_GLOBAL_SOURCE_AND_SNAPSHOT_MAPPING_V0_1"

POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"
PROVIDER = "0x2f39d218133afab8f2b819b1066c7e434ad94e9e"
INITIAL_ORACLE = "0x54586be62e3c3580375ae3723c145253060ca0c2"

FROM_BLOCK = 16_490_000
R0_TO_BLOCK = 21_525_890
START_DT = datetime(2023, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
END_DT = datetime(2023, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
EXPECTED_SNAPSHOTS = 334
MAX_TS = int(datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())

# Conservative mapping bracket entirely inside the canonical R0 envelope.
MAP_LO_BLOCK = FROM_BLOCK
MAP_HI_BLOCK = 19_100_000

PORTAL = "https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
WINDOW = 75_000
TRANSIENT_HTTP = {429, 500, 502, 503, 504, 529}
TRANSIENT_RPC_CODES = {429, -32005, -32016}
PROVIDERS = [
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]


def topic(sig: str) -> str:
    return "0x" + keccak(sig.encode()).hex()


T_USER_EMODE = topic("UserEModeSet(address,uint8)")
T_EMODE_ADDED = topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)")
T_POOL_UPDATED = topic("PoolUpdated(address,address)")
T_CONFIG_UPDATED = topic("PoolConfiguratorUpdated(address,address)")
T_ORACLE_UPDATED = topic("PriceOracleUpdated(address,address)")
T_ASSET_SOURCE = topic("AssetSourceUpdated(address,address)")
T_FALLBACK = topic("FallbackOracleUpdated(address)")
T_BASE = topic("BaseCurrencySet(address,uint256)")
T_BORROW = topic("Borrow(address,address,address,uint256,uint8,uint256,uint16)")


def as_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 16) if v.startswith("0x") else int(v)
    raise TypeError("bad integer")


def taddr(t: str) -> str:
    s = str(t).lower()
    if not s.startswith("0x") or len(s) != 66:
        raise ValueError("bad address topic")
    return "0x" + s[-40:]


def words(data: str, n: int) -> list[int]:
    s = str(data)
    h = s[2:] if s.startswith("0x") else ""
    if len(h) < 64 * n or len(h) % 64:
        raise ValueError("bad ABI data")
    return [int(h[i * 64:(i + 1) * 64], 16) for i in range(n)]


def load_one(root: str, classification: str) -> dict[str, Any]:
    xs = []
    for p in Path(root).rglob("*.json"):
        try:
            x = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if x.get("classification") == classification:
            xs.append(x)
    if len(xs) != 1:
        raise RuntimeError(f"expected exactly one {classification} under {root}, got {len(xs)}")
    return xs[0]


def _transient_rpc_error(err: Any) -> bool:
    if not isinstance(err, dict):
        return False
    code = err.get("code")
    msg = str(err.get("message", "")).lower()
    return code in TRANSIENT_RPC_CODES or any(k in msg for k in (
        "rate limit", "too many requests", "compute units", "throughput", "capacity exceeded"
    ))


def rpc_json(endpoint: str, payload: Any, stats: Counter[str]) -> Any:
    last: Exception | None = None
    for attempt in range(8):
        try:
            r = requests.post(
                endpoint, json=payload, timeout=(10, 60),
                headers={"Content-Type": "application/json", "User-Agent": f"{LAB_ID}/d0-global-v0.1"},
            )
            stats["rpc_http_attempts"] += 1
            if r.status_code in TRANSIENT_HTTP:
                stats["rpc_http_transient"] += 1
                r.close()
                if attempt < 7:
                    time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                    continue
            r.raise_for_status()
            out = r.json()
            r.close()
            return out
        except Exception as exc:
            last = exc
            stats["rpc_http_exceptions"] += 1
            if attempt < 7:
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                continue
    raise RuntimeError(f"RPC transport failed {endpoint}: {type(last).__name__}: {str(last)[:300]}")


def rpc_batch(endpoint: str, calls: list[tuple[str, list[Any]]], stats: Counter[str]) -> list[Any]:
    payload = [
        {"jsonrpc": "2.0", "id": i, "method": method, "params": params}
        for i, (method, params) in enumerate(calls)
    ]
    last_err: Any = None
    for attempt in range(8):
        out = rpc_json(endpoint, payload, stats)
        if not isinstance(out, list):
            raise RuntimeError("batch RPC non-list")
        byid = {x.get("id"): x for x in out if isinstance(x, dict)}
        vals: list[Any] = []
        transient = False
        for i in range(len(payload)):
            x = byid.get(i)
            if not x:
                raise RuntimeError(f"batch RPC item {i} missing")
            err = x.get("error")
            if err is not None:
                if _transient_rpc_error(err):
                    transient = True
                    last_err = err
                    break
                raise RuntimeError(f"batch RPC item {i} failed: {err}")
            vals.append(x.get("result"))
        if not transient:
            return vals
        stats["rpc_item_transient"] += 1
        if attempt < 7:
            stats["rpc_item_retries"] += 1
            time.sleep(min(30.0, 1.5 * (2 ** attempt)))
    raise RuntimeError(f"batch RPC transient retry budget exhausted: {last_err}")


def headers_batch(endpoint: str, blocks: list[int], stats: Counter[str]) -> dict[int, dict[str, Any]]:
    unique = sorted(set(int(x) for x in blocks))
    out: dict[int, dict[str, Any]] = {}
    for start in range(0, len(unique), 24):
        chunk = unique[start:start + 24]
        vals = rpc_batch(endpoint, [("eth_getBlockByNumber", [hex(b), False]) for b in chunk], stats)
        for b, h in zip(chunk, vals):
            if not isinstance(h, dict):
                raise RuntimeError(f"missing block header {b}")
            if int(h["number"], 16) != b:
                raise RuntimeError("header block mismatch")
            ts = int(h["timestamp"], 16)
            if ts > MAX_TS and b <= MAP_HI_BLOCK:
                # Mapping may inspect later 2024-bracketing headers only if the block
                # is outside the final mapped snapshot. Here our fixed upper bracket
                # is chosen inside 2023 and must stay protected-safe.
                raise RuntimeError("header exceeds D0 protected time ceiling")
            out[b] = h
    return out


def snapshot_targets() -> list[int]:
    vals = []
    d = START_DT
    while d <= END_DT:
        vals.append(int(d.timestamp()))
        d += timedelta(days=1)
    if len(vals) != EXPECTED_SNAPSHOTS:
        raise RuntimeError(f"snapshot target count mismatch {len(vals)}")
    return vals


def map_snapshots(stats: Counter[str]) -> list[dict[str, Any]]:
    targets = snapshot_targets()
    primary = PROVIDERS[0]

    edges = headers_batch(primary, [MAP_LO_BLOCK, MAP_HI_BLOCK], stats)
    if int(edges[MAP_LO_BLOCK]["timestamp"], 16) >= targets[0]:
        raise RuntimeError("lower mapping bracket invalid")
    if int(edges[MAP_HI_BLOCK]["timestamp"], 16) < targets[-1]:
        raise RuntimeError("upper mapping bracket invalid")

    lo = [MAP_LO_BLOCK] * len(targets)
    hi = [MAP_HI_BLOCK] * len(targets)
    rounds = 0
    while True:
        active = [i for i in range(len(targets)) if lo[i] + 1 < hi[i]]
        if not active:
            break
        mids = sorted(set((lo[i] + hi[i]) // 2 for i in active))
        hdrs = headers_batch(primary, mids, stats)
        for i in active:
            mid = (lo[i] + hi[i]) // 2
            ts = int(hdrs[mid]["timestamp"], 16)
            if ts < targets[i]:
                lo[i] = mid
            else:
                hi[i] = mid
        rounds += 1
        print(json.dumps({
            "progress": "d0_snapshot_mapping",
            "round": rounds,
            "active": len(active),
            "unique_headers": len(mids),
        }, sort_keys=True), flush=True)
        if rounds > 32:
            raise RuntimeError("snapshot mapping exceeded 32 rounds")

    final = headers_batch(primary, hi + [b - 1 for b in hi], stats)
    mapped = []
    for target, b in zip(targets, hi):
        h = final[b]
        p = final[b - 1]
        ts = int(h["timestamp"], 16)
        pts = int(p["timestamp"], 16)
        if not (pts < target <= ts):
            raise RuntimeError("first-block-at-or-after invariant failed")
        if ts > MAX_TS:
            raise RuntimeError("mapped snapshot outside 2023")
        mapped.append({
            "date": datetime.fromtimestamp(target, timezone.utc).date().isoformat(),
            "target_timestamp": target,
            "block": b,
            "timestamp": ts,
            "hash": str(h["hash"]).lower(),
        })

    # Require one entire independent provider to agree on all final + predecessor headers.
    verifier_errors = []
    verified_by = None
    for ep in PROVIDERS[1:]:
        try:
            vh = headers_batch(ep, hi + [b - 1 for b in hi], stats)
            for x in mapped:
                b = x["block"]
                h = vh[b]
                p = vh[b - 1]
                if str(h["hash"]).lower() != x["hash"]:
                    raise RuntimeError("snapshot block hash disagreement")
                if int(h["timestamp"], 16) != x["timestamp"]:
                    raise RuntimeError("snapshot timestamp disagreement")
                if not (int(p["timestamp"], 16) < x["target_timestamp"] <= int(h["timestamp"], 16)):
                    raise RuntimeError("independent first-block invariant failed")
            verified_by = ep
            break
        except Exception as exc:
            verifier_errors.append(f"{ep}: {type(exc).__name__}: {str(exc)[:250]}")
    if verified_by is None:
        raise RuntimeError(f"no independent snapshot-map verifier: {verifier_errors}")

    stats["snapshot_map_independent_verifier_pass"] += 1
    return mapped


def portal_post(body: dict[str, Any], stats: Counter[str]) -> requests.Response:
    last: Exception | None = None
    for attempt in range(8):
        try:
            r = requests.post(
                PORTAL, json=body, stream=True, timeout=(20, 180),
                headers={"Content-Type": "application/json", "Accept-Encoding": "gzip",
                         "User-Agent": f"{LAB_ID}/d0-global-v0.1"},
            )
            stats["portal_http_attempts"] += 1
            if r.status_code in TRANSIENT_HTTP:
                stats["portal_transient"] += 1
                r.close()
                if attempt < 7:
                    time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                    continue
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            stats["portal_exceptions"] += 1
            if attempt < 7:
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                continue
    raise RuntimeError(f"Portal request failed: {type(last).__name__}: {str(last)[:300]}")


def portal_stream(start: int, end: int, filters: list[dict[str, Any]], stats: Counter[str]):
    cursor = start
    while cursor <= end:
        rt = min(end, cursor + WINDOW - 1)
        body = {
            "type": "evm", "fromBlock": cursor, "toBlock": rt,
            "fields": {
                "block": {"number": True, "timestamp": True},
                "log": {"address": True, "topics": True, "data": True,
                        "transactionHash": True, "logIndex": True},
            },
            "logs": filters,
        }
        page = None
        page_last = None
        for stream_attempt in range(8):
            r = portal_post(body, stats)
            stats["portal_stream_attempts"] += 1
            local = []
            local_last = None
            try:
                for raw in r.iter_lines(decode_unicode=True):
                    if not raw:
                        continue
                    obj = json.loads(raw)
                    if isinstance(obj, dict) and obj.get("error"):
                        raise RuntimeError(f"portal semantic error {obj['error']}")
                    hdr = obj.get("header") or obj.get("block") or {}
                    bn = int(hdr["number"])
                    if not (cursor <= bn <= rt):
                        raise RuntimeError("portal row outside fixed window")
                    if local_last is not None and bn < local_last:
                        raise RuntimeError("portal page non-monotonic")
                    local_last = bn
                    local.append(obj)
            except requests.RequestException:
                stats["portal_stream_read_failures"] += 1
                r.close()
                if stream_attempt < 7:
                    stats["portal_stream_read_retries"] += 1
                    time.sleep(min(20.0, 1.5 * (2 ** stream_attempt)))
                    continue
                raise
            finally:
                try:
                    r.close()
                except Exception:
                    pass
            page = local
            page_last = local_last
            stats["portal_stream_successes"] += 1
            break

        if page is None:
            raise RuntimeError("portal stream retry budget exhausted")

        if not page or page_last is None:
            stats["portal_empty_windows"] += 1
            cursor = rt + 1
            continue

        for obj in page:
            yield obj
        stats["portal_rows"] += len(page)
        cursor = page_last + 1


def main() -> int:
    outdir = Path("aave_discovery_d0_global_output")
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / "AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_D0_GLOBAL_V0_1.json"

    stats: Counter[str] = Counter()
    receipt: dict[str, Any] = {
        "lab_id": LAB_ID,
        "phase": PHASE,
        "classification": None,
        "failure": None,
        "provider_set": PROVIDERS,
        "snapshot_quorum_required": 2,
        "safety": {
            "liquidation_outcomes_opened": False,
            "liquidation_call_values_decoded": False,
            "market_returns_opened": False,
            "pnl_opened": False,
            "accessed_2024_outcomes": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }

    try:
        preflight = load_one("downloaded_d0_preflight", "D0_PREFLIGHT_PASS")
        r0 = load_one("downloaded_r0_bootstrap", "RECONSTRUCTION_R0_BOOTSTRAP_PASS")
        if int(preflight.get("snapshot_count", -1)) != EXPECTED_SNAPSHOTS:
            raise RuntimeError("D0 preflight snapshot binding mismatch")
        if len(r0.get("reserves") or {}) != 37:
            raise RuntimeError("R0 reserve binding mismatch")

        mapped = map_snapshots(stats)
        end_block = int(mapped[-1]["block"])

        # Global eMode/provider/Borrow-mode state only. No LiquidationCall filter exists.
        filters = [
            {"address": [POOL], "topic0": [T_USER_EMODE, T_BORROW]},
            {"address": [CONFIGURATOR], "topic0": [T_EMODE_ADDED]},
            {"address": [PROVIDER], "topic0": [T_POOL_UPDATED, T_CONFIG_UPDATED, T_ORACLE_UPDATED]},
        ]

        user_mode_changes = []
        category_changes = []
        provider_transitions = []
        borrow_mode_counts: Counter[str] = Counter()
        seen: set[tuple[str, int]] = set()

        for obj in portal_stream(FROM_BLOCK, end_block, filters, stats):
            hdr = obj.get("header") or obj.get("block") or {}
            bn = int(hdr["number"])
            bts = int(hdr["timestamp"])
            if bts > MAX_TS:
                raise RuntimeError("global event exceeded D0 protected time ceiling")
            for log in sorted(obj.get("logs") or [], key=lambda x: as_int(x.get("logIndex"))):
                topics = [str(x).lower() for x in (log.get("topics") or [])]
                if not topics:
                    raise RuntimeError("global log missing topic0")
                txh = str(log.get("transactionHash", "")).lower()
                li = as_int(log.get("logIndex"))
                key = (txh, li)
                if key in seen:
                    raise RuntimeError("duplicate global canonical log")
                seen.add(key)
                t0 = topics[0]

                if t0 == T_USER_EMODE:
                    if len(topics) < 2:
                        raise RuntimeError("UserEModeSet ABI")
                    vals = words(log.get("data", ""), 1)
                    user_mode_changes.append({
                        "block": bn, "logIndex": li, "user": taddr(topics[1]), "category": vals[0]
                    })
                elif t0 == T_EMODE_ADDED:
                    if len(topics) < 2:
                        raise RuntimeError("EModeCategoryAdded ABI")
                    vals = words(log.get("data", ""), 4)
                    category_changes.append({
                        "block": bn, "logIndex": li, "category": as_int(topics[1]),
                        "ltv": vals[0], "liquidationThreshold": vals[1],
                        "liquidationBonus": vals[2],
                        "priceSource": "0x" + format(vals[3], "040x")[-40:],
                    })
                elif t0 in (T_POOL_UPDATED, T_CONFIG_UPDATED, T_ORACLE_UPDATED):
                    if len(topics) < 3:
                        raise RuntimeError("provider transition ABI")
                    name = {
                        T_POOL_UPDATED: "PoolUpdated",
                        T_CONFIG_UPDATED: "PoolConfiguratorUpdated",
                        T_ORACLE_UPDATED: "PriceOracleUpdated",
                    }[t0]
                    provider_transitions.append({
                        "block": bn, "logIndex": li, "event": name,
                        "old": taddr(topics[1]), "new": taddr(topics[2]),
                    })
                elif t0 == T_BORROW:
                    # Aave V3 Borrow data words:
                    # user (address), amount, interestRateMode, borrowRate.
                    vals = words(log.get("data", ""), 4)
                    mode = vals[2]
                    borrow_mode_counts[str(mode)] += 1
                else:
                    raise RuntimeError("unexpected global topic")

        # V3 Ethereum canonical assumption requires variable-rate borrowing only.
        non_variable = sum(v for k, v in borrow_mode_counts.items() if int(k) != 2)
        if non_variable:
            raise RuntimeError(f"non-variable Borrow interestRateMode observed: {dict(borrow_mode_counts)}")
        if not borrow_mode_counts:
            raise RuntimeError("zero Borrow events in D0 global source envelope")

        oracle_transitions = [x for x in provider_transitions if x["event"] == "PriceOracleUpdated"]
        active_oracles = {INITIAL_ORACLE}
        for x in oracle_transitions:
            active_oracles.add(x["new"])

        oracle_filters = [{
            "address": sorted(active_oracles),
            "topic0": [T_ASSET_SOURCE, T_FALLBACK, T_BASE],
        }]
        oracle_config_events = []
        oracle_seen: set[tuple[str, int]] = set()
        for obj in portal_stream(FROM_BLOCK, end_block, oracle_filters, stats):
            hdr = obj.get("header") or obj.get("block") or {}
            bn = int(hdr["number"])
            bts = int(hdr["timestamp"])
            if bts > MAX_TS:
                raise RuntimeError("oracle config exceeded D0 time ceiling")
            for log in obj.get("logs") or []:
                topics = [str(x).lower() for x in (log.get("topics") or [])]
                txh = str(log.get("transactionHash", "")).lower()
                li = as_int(log.get("logIndex"))
                key = (txh, li)
                if key in oracle_seen:
                    raise RuntimeError("duplicate oracle config log")
                oracle_seen.add(key)
                t0 = topics[0]
                row = {"block": bn, "logIndex": li, "oracle": str(log["address"]).lower()}
                if t0 == T_ASSET_SOURCE:
                    if len(topics) < 3:
                        raise RuntimeError("AssetSourceUpdated ABI")
                    row.update({"event": "AssetSourceUpdated", "asset": taddr(topics[1]), "source": taddr(topics[2])})
                elif t0 == T_FALLBACK:
                    if len(topics) < 2:
                        raise RuntimeError("FallbackOracleUpdated ABI")
                    row.update({"event": "FallbackOracleUpdated", "fallback": taddr(topics[1])})
                elif t0 == T_BASE:
                    if len(topics) < 2:
                        raise RuntimeError("BaseCurrencySet ABI")
                    row.update({"event": "BaseCurrencySet", "base": taddr(topics[1]), "unit": words(log.get("data", ""), 1)[0]})
                else:
                    raise RuntimeError("unexpected oracle config event")
                oracle_config_events.append(row)

        mapping_blob = "\n".join(
            f"{x['date']}|{x['target_timestamp']}|{x['block']}|{x['timestamp']}|{x['hash']}" for x in mapped
        )
        global_blob = json.dumps({
            "user_mode_changes": user_mode_changes,
            "category_changes": category_changes,
            "provider_transitions": provider_transitions,
            "oracle_config_events": oracle_config_events,
            "borrow_mode_counts": dict(sorted(borrow_mode_counts.items())),
        }, sort_keys=True, separators=(",", ":"))

        receipt.update({
            "classification": "D0_GLOBAL_SOURCE_PASS",
            "snapshot_count": len(mapped),
            "snapshot_mapping": mapped,
            "snapshot_mapping_sha256": hashlib.sha256(mapping_blob.encode()).hexdigest(),
            "source_end_block": end_block,
            "source_event_counts": {
                "user_emode_changes": len(user_mode_changes),
                "emode_category_changes": len(category_changes),
                "provider_transitions": len(provider_transitions),
                "oracle_config_events": len(oracle_config_events),
                "borrow_events": sum(borrow_mode_counts.values()),
            },
            "borrow_interest_rate_mode_counts": dict(sorted(borrow_mode_counts.items())),
            "user_mode_changes": user_mode_changes,
            "emode_category_changes": category_changes,
            "provider_transitions": provider_transitions,
            "oracle_config_events": oracle_config_events,
            "active_oracles": sorted(active_oracles),
            "global_state_sha256": hashlib.sha256(global_blob.encode()).hexdigest(),
            "next_authorized_phase": "D0_RESERVE_SHARDS_PREDICTOR_ONLY",
        })
    except Exception as exc:
        msg = f"{type(exc).__name__}: {str(exc)[:1800]}"
        if "non-variable Borrow" in msg or "duplicate" in msg or "ABI" in msg or "disagreement" in msg:
            cls = "D0_GLOBAL_PROVENANCE_FAILURE"
        else:
            cls = "D0_GLOBAL_TECHNICAL_FAILURE"
        receipt.update({"classification": cls, "failure": msg, "next_authorized_phase": None})

    receipt["transport_stats"] = dict(stats)
    dst.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "snapshots": receipt.get("snapshot_count"),
        "borrow_modes": receipt.get("borrow_interest_rate_mode_counts"),
        "user_mode_changes": (receipt.get("source_event_counts") or {}).get("user_emode_changes"),
        "liquidation_outcomes_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True), flush=True)
    return 0 if receipt["classification"] == "D0_GLOBAL_SOURCE_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
