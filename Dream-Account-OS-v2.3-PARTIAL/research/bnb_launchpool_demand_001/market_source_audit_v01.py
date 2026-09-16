import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "FINAL_PRE_DISCOVERY_PROTOCOL_V0.1.json"
EVENTS = HERE / "source_validation_v02" / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_VALIDATION_V0.2.json"
OUTDIR = HERE / "market_source_v01"
RAWDIR = OUTDIR / "raw"
OUT = OUTDIR / "BNB_LAUNCHPOOL_DEMAND_001_MARKET_SOURCE_AUDIT_V0.1.json"
BASE = "https://data.binance.vision/data/spot/monthly/klines/BNBBTC/15m"
UA = {"User-Agent": "Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-MARKET-SOURCE-AUDIT/1.0"}

GUARDS = {
    "market_price_values_opened": False,
    "open_parsed": False,
    "high_parsed": False,
    "low_parsed": False,
    "close_parsed": False,
    "volume_parsed": False,
    "returns_computed": False,
    "pnl_computed": False,
    "year_2025_requested": False,
    "year_2026_requested": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
    "merge_to_main": False,
}


def get(url, attempts=4):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(0.5 * (2 ** i))
    raise last


def months(start, end):
    sy, sm = map(int, start.split("-")); ey, em = map(int, end.split("-"))
    out=[]; y=sy; m=sm
    while (y,m) <= (ey,em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1; m = 1
    return out


def parse_checksum(raw, expected_name):
    parts = raw.decode("utf-8", "replace").strip().split()
    if not parts:
        raise RuntimeError("EMPTY_CHECKSUM")
    dg = parts[0].lower()
    if len(dg) != 64 or any(c not in "0123456789abcdef" for c in dg):
        raise RuntimeError("MALFORMED_CHECKSUM")
    if len(parts) > 1 and parts[-1].lstrip("*") != expected_name:
        raise RuntimeError("CHECKSUM_FILENAME_MISMATCH")
    return dg


def parse_epoch(first):
    s = first.decode("ascii", "strict").strip()
    if not re.fullmatch(r"\d{10,18}", s):
        return None
    x = int(s)
    if x > 10**14:
        sec = x / 1_000_000.0
    elif x > 10**11:
        sec = x / 1_000.0
    else:
        sec = float(x)
    return int(round(sec))


def iso(sec):
    return datetime.fromtimestamp(sec, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def ceil_next_15m(dt):
    sec = int(dt.timestamp())
    return ((sec // 900) + 1) * 900


def build_selected(canonical_events):
    evs = []
    for e in canonical_events:
        dt = datetime.fromisoformat(e["published_timestamp_utc"].replace("Z", "+00:00")).astimezone(timezone.utc)
        evs.append({"n": int(e["n"]), "symbol": e["symbol"], "dt": dt, "published": e["published_timestamp_utc"]})
    evs.sort(key=lambda x: x["dt"])

    clusters=[]
    for e in evs:
        if not clusters or (e["dt"] - clusters[-1][-1]["dt"]).total_seconds() > 3600:
            clusters.append([e])
        else:
            clusters[-1].append(e)

    candidates=[]
    for c in clusters:
        signal=c[0]["dt"]
        entry=ceil_next_15m(signal)
        exit_ts=entry + 24*3600
        candidates.append({
            "project_numbers": [x["n"] for x in c],
            "symbols": [x["symbol"] for x in c],
            "signal_time_utc": c[0]["published"],
            "entry_time_utc": iso(entry),
            "exit_time_utc": iso(exit_ts),
            "entry_epoch": entry,
            "exit_epoch": exit_ts,
        })

    selected=[]; suppressed=[]; active_exit=None
    for c in candidates:
        if active_exit is not None and c["entry_epoch"] < active_exit:
            suppressed.append(c)
            continue
        selected.append(c)
        active_exit=c["exit_epoch"]
    return clusters, candidates, selected, suppressed


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    RAWDIR.mkdir(parents=True, exist_ok=True)
    p=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    e=json.loads(EVENTS.read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_PRE_MARKET_OUTCOME"
    assert e["classification"] == "SOURCE_DATA_PASS"
    assert e["canonical_event_manifest_sha256"] == p["source_gate"]["canonical_event_manifest_sha256"]
    assert p["market_data_contract"]["price_fields_allowed_only_after_source_audit_pass"] == ["open"]
    assert p["market_data_contract"]["high_low_close_volume_forbidden"] is True

    mths=months(p["market_data_contract"]["monthly_archive_start"], p["market_data_contract"]["monthly_archive_end"])
    assert len(mths) == 27
    if any(x.startswith("2025-") for x in mths): GUARDS["year_2025_requested"] = True
    if any(x.startswith("2026-") for x in mths): GUARDS["year_2026_requested"] = True
    assert not GUARDS["year_2025_requested"] and not GUARDS["year_2026_requested"]

    manifest=[]; all_ts=[]; technical=[]
    for ym in mths:
        name=f"BNBBTC-15m-{ym}.zip"
        url=f"{BASE}/{name}"
        try:
            cb=get(url+".CHECKSUM")
            official=parse_checksum(cb,name)
            zb=get(url)
            calc=hashlib.sha256(zb).hexdigest().lower()
            if calc != official:
                raise RuntimeError("SHA256_MISMATCH")
            zpath=RAWDIR/name
            zpath.write_bytes(zb)
            (RAWDIR/(name+".CHECKSUM")).write_bytes(cb)
            with zipfile.ZipFile(io.BytesIO(zb)) as z:
                bad=z.testzip()
                if bad is not None:
                    raise RuntimeError(f"ZIP_CRC_FAILURE:{bad}")
                members=[n for n in z.namelist() if not n.endswith("/")]
                if len(members) != 1:
                    raise RuntimeError("ZIP_MEMBER_COUNT_NOT_ONE")
                ts=[]
                with z.open(members[0]) as f:
                    for line in f:
                        if not line.strip():
                            continue
                        first=line.split(b",",1)[0]
                        sec=parse_epoch(first)
                        if sec is None:
                            # header line only; no other column is parsed.
                            continue
                        ts.append(sec)
                if not ts:
                    raise RuntimeError("NO_TIMESTAMPS")
                if len(ts) != len(set(ts)):
                    raise RuntimeError("DUPLICATE_TIMESTAMP_WITHIN_MONTH")
                all_ts.extend(ts)
                manifest.append({
                    "month": ym,
                    "archive": name,
                    "sha256": calc,
                    "timestamp_rows": len(ts),
                    "first_timestamp_utc": iso(min(ts)),
                    "last_timestamp_utc": iso(max(ts)),
                })
        except Exception as ex:
            technical.append({"month":ym,"error":f"{type(ex).__name__}:{ex}"})

    clusters,candidates,selected,suppressed=build_selected(e["canonical_events"])
    all_ts_set=set(all_ts)
    duplicates_global=len(all_ts) - len(all_ts_set)
    path_failures=[]
    for s in selected:
        req=list(range(s["entry_epoch"], s["exit_epoch"]+1, 900))
        missing=[x for x in req if x not in all_ts_set]
        if missing:
            path_failures.append({
                "project_numbers": s["project_numbers"],
                "entry_time_utc": s["entry_time_utc"],
                "exit_time_utc": s["exit_time_utc"],
                "missing_count": len(missing),
                "first_missing_utc": iso(missing[0]),
            })

    archive_checks_pass = (len(manifest)==27 and not technical)
    selection_checks_pass = (len(clusters)==32 and len(selected)==31 and len(suppressed)==1 and suppressed[0]["project_numbers"]==[59])
    path_checks_pass = (duplicates_global==0 and not path_failures)
    classification = "MARKET_SOURCE_DATA_PASS" if archive_checks_pass and selection_checks_pass and path_checks_pass else "SOURCE_OR_EXECUTION_FAILURE"

    manifest_basis="\n".join(f"{x['month']}|{x['sha256']}|{x['timestamp_rows']}|{x['first_timestamp_utc']}|{x['last_timestamp_utc']}" for x in manifest).encode()
    receipt={
        "lab_id":p["lab_id"],
        "mve_id":p["mve_id"],
        "classification":classification,
        "archive_count":len(manifest),
        "expected_archive_count":27,
        "archive_manifest_sha256":hashlib.sha256(manifest_basis).hexdigest(),
        "archive_manifest":manifest,
        "technical_failures":technical,
        "global_duplicate_timestamp_count":duplicates_global,
        "event_clusters":len(clusters),
        "candidate_clusters":len(candidates),
        "selected_trade_paths":len(selected),
        "suppressed_trade_paths":len(suppressed),
        "suppressed": [{k:v for k,v in s.items() if not k.endswith('_epoch')} for s in suppressed],
        "selected": [{k:v for k,v in s.items() if not k.endswith('_epoch')} for s in selected],
        "execution_path_failures":path_failures,
        "guards":GUARDS,
        "market_outcomes_opened":False,
        "promotion_to_discovery_execution_authorized":classification=="MARKET_SOURCE_DATA_PASS",
    }
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "classification":classification,
        "archive_count":len(manifest),
        "event_clusters":len(clusters),
        "selected_trade_paths":len(selected),
        "suppressed_trade_paths":len(suppressed),
        "execution_path_failures":len(path_failures),
        "archive_manifest_sha256":receipt["archive_manifest_sha256"],
    },indent=2))

if __name__ == "__main__":
    main()
