#!/usr/bin/env python3
from __future__ import annotations

"""CIGL-VWAP-01 fail-closed action orchestrator.

Downloads only frozen H180 source months required by the current phase, verifies
current Binance CHECKSUMs, then verifies the ordered raw hashes against the
historical H180 Run03 audit fingerprint for that phase before computing any
market outcome. 2025+ is structurally unreachable.
"""

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

import zstandard as zstd

import classic_indicators_gap_v01 as lab

BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
SYMBOLS = lab.SYMBOLS
FIELDS = [
    "open_time","open","high","low","close","volume","close_time",
    "quote_asset_volume","number_of_trades","taker_buy_base_volume",
    "taker_buy_quote_volume","ignore_provider_field","symbol","interval",
    "source_archive","source_csv","provider_sha256","source_local_sha256",
]
DISCOVERY_YMS = [f"{y}-{m:02d}" for y in (2022, 2023) for m in range(1, 13)]
VALIDATION_YMS = [f"2024-{m:02d}" for m in range(1, 13)]

# SHA256 of ordered lines '<symbol>/1m/<file>\t<historical_raw_sha256>\n'.
# Derived from the immutable H180 Run03 per-symbol audit material.
EXPECTED_PHASE_RAW_FP = {
    "DISCOVERY_2022_2023": {
        "BTCUSDT": "bdd944c4dd1da8d889a3f13961bdda687ccc9afd91be29a9d9cfcafb98a4cbfa",
        "ETHUSDT": "d22c1997541fbfba8ddb3436c45e80ef98b3d35006f67e1ca692942543adbafe",
        "SOLUSDT": "def9502c70da1dee58b1ca061ff5da2d2755ec0a6a9be9a18b04c155579b9aa4",
        "BNBUSDT": "4f76a7a0592e12ff3be547723ce97e628a84061610f91c7433e3d42fa0efa5e5",
        "XRPUSDT": "e88ac51a27f78b750401116bbbff36ff339f1a73587885354b2bf4966700a1b7",
        "DOGEUSDT": "950d47f2f1f7118e0a1ccead7a402d5ac919708cfa1910b3b3eebee722e691ce",
    },
    "VALIDATION_2024": {
        "BTCUSDT": "58b16d48f55af32d9596b3b27a298a8b749c76ea7e8395c9efab4e5eabc416e2",
        "ETHUSDT": "78cacf1ebd56cc314e8ff3abdfd817ceaa79c2724bd880c0596fe418c9d70590",
        "SOLUSDT": "795283535ec8f63f5960802b3a78537e94258f1461f0cf59deefb87cc26ee3f1",
        "BNBUSDT": "a8c90d0d4dc6c63691fbb27b97e9d7276ca7a1d1cb41fbfae02910582eef0cc1",
        "XRPUSDT": "e0f6ee46f5d846b2ee8843ddff0ba9149a925369942d6bbd1e982febaba811f7",
        "DOGEUSDT": "3a0da3b5c86a56ff1f6ff17a3b197cd1abb210d1aef2e162aa3bbf402a192b23",
    },
}


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str) -> bytes:
    if not url.startswith(BASE + "/"):
        raise PermissionError("network destination outside frozen Binance USD-M monthly kline path")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"CIGL-VWAP-01/0.1"}), timeout=90) as r:
        return r.read()


def provider_hash(text: str, filename: str) -> str:
    m = re.fullmatch(r"\s*([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*", text)
    if not m or m.group(2) != filename:
        raise RuntimeError(f"invalid provider CHECKSUM for {filename}")
    return m.group(1).lower()


def normalize_member(symbol: str, ym: str, archive: bytes, digest: str) -> tuple[str, bytes, int, str]:
    filename = f"{symbol}-1m-{ym}.zip"
    source_archive = f"{symbol}/1m/{filename}"
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        csvs = [n for n in z.namelist() if n.endswith(".csv")]
        if len(csvs) != 1:
            raise RuntimeError(f"unexpected CSV cardinality {source_archive}")
        source_csv = csvs[0]
        out = io.BytesIO()
        uh = hashlib.sha256()
        rows = 0
        zc = zstd.ZstdCompressor(level=6, threads=0, write_checksum=True, write_content_size=False)
        with zc.stream_writer(out, closefd=False) as zw, z.open(source_csv) as f:
            header = (",".join(FIELDS) + "\n").encode()
            zw.write(header); uh.update(header)
            for raw in f:
                line = raw.decode("utf-8-sig").rstrip("\r\n")
                if not line or line.startswith("open_time,"):
                    continue
                x = line.split(",")
                if len(x) != 12:
                    raise RuntimeError(f"schema drift {source_archive}")
                ts = int(x[0])
                # This action branch can never ingest 2025+.
                if ts >= 1735689600000:
                    raise PermissionError("2025+ timestamp blocked")
                ob = (",".join(x + [symbol,"1m",source_archive,source_csv,digest,digest]) + "\n").encode()
                zw.write(ob); uh.update(ob); rows += 1
        return f"{symbol}/1m/{symbol}-1m-{ym}.normalized.csv.zst", out.getvalue(), rows, uh.hexdigest()


def acquire_phase(normalized_dir: Path, phase: str, months: list[str], append: bool) -> dict:
    if phase not in EXPECTED_PHASE_RAW_FP:
        raise PermissionError("unknown phase")
    if any(not (ym.startswith("2022-") or ym.startswith("2023-") or (phase == "VALIDATION_2024" and ym.startswith("2024-"))) for ym in months):
        raise PermissionError("phase requests forbidden year")
    normalized_dir.mkdir(parents=True, exist_ok=True)
    phase_rows = []
    symbol_fps = {}
    for symbol in SYMBOLS:
        material = []
        package = normalized_dir / f"H180-0001_NORMALIZED_{symbol}.zip"
        mode = "a" if append and package.exists() else "w"
        with zipfile.ZipFile(package, mode, compression=zipfile.ZIP_STORED, allowZip64=True) as outzip:
            existing = set(outzip.namelist())
            for ym in months:
                if ym >= "2025-01":
                    raise PermissionError("2025+ month blocked")
                filename = f"{symbol}-1m-{ym}.zip"
                url = f"{BASE}/{symbol}/1m/{filename}"
                ck = fetch(url + ".CHECKSUM").decode("utf-8-sig")
                archive = fetch(url)
                digest = h(archive)
                if digest != provider_hash(ck, filename):
                    raise RuntimeError(f"provider checksum mismatch {symbol} {ym}")
                material.append(f"{symbol}/1m/{filename}\t{digest}\n")
                member, zbytes, rows, uhash = normalize_member(symbol, ym, archive, digest)
                if member in existing:
                    raise RuntimeError(f"duplicate normalized member {member}")
                zi = zipfile.ZipInfo(member, (1980,1,1,0,0,0)); zi.compress_type = zipfile.ZIP_STORED; zi.external_attr = 0o100444 << 16
                outzip.writestr(zi, zbytes)
                phase_rows.append({"symbol":symbol,"month":ym,"source_sha256":digest,"normalized_member":member,"rows":rows,"normalized_uncompressed_sha256":uhash})
        fp = hashlib.sha256("".join(material).encode()).hexdigest()
        expected = EXPECTED_PHASE_RAW_FP[phase][symbol]
        if fp != expected:
            raise RuntimeError(f"historical H180 raw fingerprint mismatch {phase} {symbol}: {fp} != {expected}")
        symbol_fps[symbol] = fp
        print(f"{phase} {symbol}: historical raw fingerprint MATCH", flush=True)
    return {"phase":phase,"months":[months[0],months[-1]],"symbol_raw_fingerprints":symbol_fps,"rows":phase_rows}


def save(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> None:
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); args=ap.parse_args()
    work=args.work; norm=work/"normalized"; out=work/"outputs"; out.mkdir(parents=True, exist_ok=True)

    # Synthetic-only guard first.
    lab.self_test()

    disc_source = acquire_phase(norm, "DISCOVERY_2022_2023", DISCOVERY_YMS, append=False)
    save(out/"CIGL-VWAP-01_DISCOVERY_SOURCE_AUDIT.json", disc_source)
    disc_all, disc_load = lab.run_phase(norm, lab.DISCOVERY_MONTHS, lab.VALIDATION_START, "DISCOVERY")
    disc = lab.split_trades(disc_all, lab.DISCOVERY_START, lab.DISCOVERY_END)
    disc_metrics = lab.summarize(disc); dgate = lab.discovery_gate(disc_metrics)
    disc.to_csv(out/"CIGL-VWAP-01_DISCOVERY_TRADES.csv", index=False)
    save(out/"CIGL-VWAP-01_DISCOVERY_GATE.json", {"metrics":disc_metrics,"gate":dgate,"load_audits":disc_load})

    if not dgate["pass"]:
        receipt={"lab":lab.LAB,"experiment":lab.EXPERIMENT,"status":"DISCOVERY_FAIL_NO_VALIDATION_ACCESS","discovery":{"metrics":disc_metrics,"gate":dgate},"validation_2024_opened":False,"protected":{"2025":"UNOPENED","2026":"LOCKED_UNOPENED"},"source_authority":{"historical_h180_fingerprint":lab.SOURCE_CANONICAL_FP,"discovery_raw_match":True}}
        save(out/"CIGL-VWAP-01_ACTION_RECEIPT.json", receipt)
        print(json.dumps({"status":receipt["status"],"discovery_gate":dgate},indent=2),flush=True)
        return

    # Only now may 2024 bytes be requested.
    val_source = acquire_phase(norm, "VALIDATION_2024", VALIDATION_YMS, append=True)
    save(out/"CIGL-VWAP-01_VALIDATION_2024_SOURCE_AUDIT.json", val_source)
    val_all, val_load = lab.run_phase(norm, lab.VALIDATION_MONTHS, lab.FORBIDDEN_START, "VALIDATION_2024")
    val = lab.split_trades(val_all, lab.VALIDATION_START, lab.VALIDATION_END)
    val_metrics = lab.summarize(val); vgate = lab.validation_gate(val_metrics)
    val.to_csv(out/"CIGL-VWAP-01_VALIDATION_2024_TRADES.csv", index=False)
    status = "MVE_1_REPLICATION_READY" if vgate["pass"] else "VALIDATION_FAIL_NO_EDGE_STOP"
    receipt={"lab":lab.LAB,"experiment":lab.EXPERIMENT,"status":status,"discovery":{"metrics":disc_metrics,"gate":dgate},"validation_2024_opened":True,"validation_2024":{"metrics":val_metrics,"gate":vgate,"load_audits":val_load},"protected":{"2025":"UNOPENED","2026":"LOCKED_UNOPENED"},"source_authority":{"historical_h180_fingerprint":lab.SOURCE_CANONICAL_FP,"discovery_raw_match":True,"validation_2024_raw_match":True}}
    save(out/"CIGL-VWAP-01_ACTION_RECEIPT.json", receipt)
    print(json.dumps({"status":status,"discovery_gate":dgate,"validation_gate":vgate},indent=2),flush=True)

if __name__ == "__main__":
    main()
