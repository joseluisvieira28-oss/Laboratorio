#!/usr/bin/env python3
"""Production source-only event parser for BINANCE-MARGIN-BORROW-ACCESS-001.

Frozen by EVENT_PARSER_PROTOCOL_V0_1. Operates only on the 69 source-qualified
official Binance Support articles. No price/outcome/borrow-cost data is used.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import source_census_v04 as base

SHARD_COUNT = 4
START_MS = base.START_MS
END_MS = base.END_MS

STOP_SYMBOLS = {
    "A","AN","AND","AS","AT","BINANCE","MARGIN","CROSS","ISOLATED","NEW","BORROWABLE",
    "ASSET","ASSETS","HAS","ADDED","ADD","WILL","MORE","TOKEN","TOKENS","PAIR","PAIRS",
    "ON","THE","TO","FROM","WITH","PLUS","OF","IN","TRADING","SPOT","FUTURES","EARN",
    "BUY","CRYPTO","CONVERT","USD","UTC","NETWORK","FINANCE","PROTOCOL"
}

BORROW_CLAUSE_RE = re.compile(
    r"(?P<assets>.{1,320}?)\s+as\s+(?:a\s+)?new\s+borrowable\s+assets?\s+on\s+"
    r"(?P<venue>Cross\s+Margin|Cross\s+(?:and|&)\s+Isolated\s+Margin)", re.I
)
ADD_PREFIX_RE = re.compile(
    r"^(?:Binance(?:\s+Margin)?(?:\s+has)?\s+added|Binance\s+Margin\s+will\s+add)\s+", re.I
)
UTC_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})\s+(\d{2}:\d{2})(?::(\d{2}))?\s*(?:\(UTC\)|UTC)", re.I)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse_body_ast(raw: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {"node":"text","text":base.normalize_text(raw)}
    return {}


def node_text(node: Any) -> str:
    if isinstance(node, dict):
        if node.get("node") == "text" and isinstance(node.get("text"), str):
            return node["text"]
        parts = []
        for key in ("child", "children"):
            value = node.get(key)
            if isinstance(value, list):
                parts.extend(node_text(x) for x in value)
        return norm(" ".join(x for x in parts if x))
    if isinstance(node, list):
        return norm(" ".join(node_text(x) for x in node))
    return ""


def walk_tag(node: Any, wanted: set[str]):
    if isinstance(node, dict):
        tag = str(node.get("tag") or "").lower()
        if tag in wanted:
            yield node
        for key in ("child", "children"):
            value = node.get(key)
            if isinstance(value, list):
                for x in value:
                    yield from walk_tag(x, wanted)
    elif isinstance(node, list):
        for x in node:
            yield from walk_tag(x, wanted)


def scientific_blocks(ast: Any) -> list[str]:
    blocks: list[str] = []
    for n in walk_tag(ast, {"p", "li"}):
        t = norm(node_text(n))
        if t:
            blocks.append(t)
    if not blocks:
        t = norm(node_text(ast))
        if t:
            blocks.append(t)
    return blocks


def table_rows(ast: Any) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in walk_tag(ast, {"tr"}):
        cells = []
        children = tr.get("child") or tr.get("children") or []
        for ch in children:
            if isinstance(ch, dict) and str(ch.get("tag") or "").lower() in {"td","th"}:
                t = norm(node_text(ch))
                if t:
                    cells.append(t)
        if cells:
            rows.append(cells)
    return rows


def strip_disclaimer(text: str) -> str:
    markers = ["Risk Warning", "Digital asset prices can be volatile", "General Disclaimer"]
    cuts = [text.lower().find(m.lower()) for m in markers if text.lower().find(m.lower()) >= 0]
    return text[:min(cuts)] if cuts else text


def symbols_from_expression(expr: str) -> list[str]:
    expr = ADD_PREFIX_RE.sub("", norm(expr)).strip(" :-–—,")
    paren = re.findall(r"\(([A-Z0-9][A-Z0-9._-]{0,19})\)", expr)
    if paren:
        vals = paren
    else:
        vals = re.findall(r"(?<![A-Za-z0-9])([A-Z0-9][A-Z0-9._-]{0,19})(?![A-Za-z0-9])", expr)
    out: list[str] = []
    for v in vals:
        v = v.strip("._-")
        if not v or v in STOP_SYMBOLS or re.fullmatch(r"20\d{2}", v):
            continue
        if v not in out:
            out.append(v)
    return out


def extract_clause_assets(blocks: list[str]) -> tuple[list[str], str | None]:
    for block in blocks:
        low = block.lower()
        if "borrowable asset" not in low or "cross" not in low or "margin" not in low:
            continue
        if re.search(r"\b(delist|remove|removal)\b", block, re.I):
            continue
        m = BORROW_CLAUSE_RE.search(block)
        if not m:
            continue
        syms = symbols_from_expression(m.group("assets"))
        if syms:
            return syms, block[max(0,m.start()-80):min(len(block),m.end()+120)]
    return [], None


def extract_table_assets(ast: Any) -> tuple[list[str], str | None]:
    rows = table_rows(ast)
    # Frozen schema route: only accept rows/cells explicitly tied to New Borrowable Assets + Cross Margin.
    context = False
    evidence: list[str] = []
    for row in rows:
        joined = " | ".join(row)
        if re.search(r"\bNew Borrowable Assets\b", joined, re.I):
            context = True
            evidence.append(joined)
            # Sometimes header and values are in the same row.
            if re.search(r"\bCross Margin\b", joined, re.I):
                parts = re.split(r"Cross Margin", joined, flags=re.I)
                if len(parts) > 1:
                    syms = symbols_from_expression(parts[-1])
                    if syms:
                        return syms, " || ".join(evidence[-3:])
            continue
        if context:
            evidence.append(joined)
            # Reject table scan after a new section is encountered.
            if re.search(r"\bNew (?:Cross|Isolated).*Pairs?\b", joined, re.I):
                break
            if any(re.fullmatch(r"Cross Margin", c, re.I) for c in row):
                others = [c for c in row if not re.fullmatch(r"Cross Margin", c, re.I)]
                syms = symbols_from_expression(" ".join(others))
                if syms:
                    return syms, " || ".join(evidence[-3:])
            if re.search(r"\bCross Margin\b", joined, re.I):
                after = re.split(r"Cross Margin", joined, flags=re.I)[-1]
                syms = symbols_from_expression(after)
                if syms:
                    return syms, " || ".join(evidence[-3:])
    return [], None


def explicit_times(text: str, publish_ms: int) -> list[int]:
    vals: list[int] = []
    for m in UTC_RE.finditer(text):
        sec = m.group(3) or "00"
        dt = datetime.strptime(f"{m.group(1)} {m.group(2)}:{sec}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        ts = int(dt.timestamp()*1000)
        if ts >= publish_ms and ts <= END_MS + 31*24*3600*1000:
            vals.append(ts)
    return sorted(set(vals))


def parse_one(code: str) -> dict[str, Any]:
    obj, status, raw_sha, retries = base.detail_request(code)
    data = obj.get("data", obj)
    if not isinstance(data, dict):
        raise RuntimeError(f"canonical article data is not an object: {code}")
    payload_code = str(data.get("code") or "").lower()
    if payload_code and payload_code != code.lower():
        raise RuntimeError(f"article identity mismatch {code}!={payload_code}")
    title = norm(str(data.get("title") or ""))
    publish_ms = base.parse_timestamp_value(data.get("publishDate"))
    if not title or publish_ms is None or not (START_MS <= publish_ms <= END_MS):
        raise RuntimeError(f"missing/invalid canonical title or publishDate for {code}")
    ast = parse_body_ast(data.get("body"))
    blocks = scientific_blocks(ast)
    full_text = norm(node_text(ast))
    main_text = norm(strip_disclaimer(full_text))
    body_sha = hashlib.sha256(str(data.get("body") or "").encode()).hexdigest()

    if re.search(r"\b(delist|remove|removal)\b", title, re.I) and re.search(r"borrowable assets?", title, re.I):
        direction = "REMOVE"
        assets: list[str] = []
        route = "TITLE_REMOVE"
        evidence = title
        ambiguous = False
    elif re.search(r"Introduces Collateral Haircuts", title, re.I):
        direction = "OTHER"
        assets = []
        route = "TITLE_OTHER"
        evidence = title
        ambiguous = False
    else:
        assets, evidence = extract_clause_assets(blocks)
        route = "CLAUSE" if assets else ""
        if not assets:
            assets, evidence = extract_table_assets(ast)
            route = "TABLE" if assets else ""
        has_cross_borrow = bool(
            re.search(r"borrowable assets?.{0,80}(?:on|from)\s+Cross(?:\s+Margin|\s+(?:and|&)\s+Isolated\s+Margin)", main_text, re.I)
            or re.search(r"Cross(?:\s+and\s+Isolated)?\s+Margin.{0,80}borrowable assets?", main_text, re.I)
        )
        if assets and has_cross_borrow:
            direction = "ADD"
            ambiguous = False
        elif has_cross_borrow:
            direction = "ADD"
            ambiguous = True
            route = "ASSET_PARSE_AMBIGUOUS"
            evidence = evidence or title
        else:
            direction = "OTHER"
            assets = []
            ambiguous = False
            route = "NO_EXPLICIT_CROSS_BORROW_ADD"
            evidence = title

    title_body = norm(title + " " + main_text)
    confounds = {
        "new_cross_margin_pair": bool(re.search(r"\bnew\s+(?:cross\s+margin|margin|trading)\s+pairs?\b|new trading pairs? on Cross Margin", title_body, re.I)),
        "isolated_margin": bool(re.search(r"\bIsolated Margin\b", title_body, re.I)),
        "spot_listing_or_start": bool(re.search(r"\bBinance will list\b|\bSpot trading (?:will )?(?:open|start|commence)\b|\blisted on Binance Spot\b|\binitial Spot trading\b", title_body, re.I)),
        "convert": bool(re.search(r"\bConvert\b", title_body, re.I)),
        "earn": bool(re.search(r"\bEarn\b", title_body, re.I)),
        "buy_crypto": bool(re.search(r"\bBuy Crypto\b", title_body, re.I)),
        "futures_or_perpetual": bool(re.search(r"\bFutures?\b|\bPerpetual\b", title_body, re.I)),
    }
    times = explicit_times(main_text, publish_ms)
    effective_ms = times[0] if times else None
    snippet = norm(evidence or "")[:1200]
    return {
        "code": code.lower(),
        "http_status": status,
        "request_retries": retries,
        "response_sha256": raw_sha,
        "official_title": title,
        "official_publish_ms": publish_ms,
        "event_information_ms": publish_ms,
        "effective_ms": effective_ms,
        "explicit_utc_times": times[:12],
        "direction": direction,
        "cross_margin_borrowable_assets": assets,
        "asset_parse_ambiguous": ambiguous,
        "parser_route": route,
        "confounds": confounds,
        "body_sha256": body_sha,
        "evidence_snippet": snippet,
    }


def cmd_shard(input_path: Path, shard: int, out_dir: Path) -> int:
    source = json.loads(input_path.read_text())
    codes = source.get("codes", [])
    if source.get("structural_articles") != 69 or len(codes) != 69 or len(set(codes)) != 69:
        raise SystemExit("frozen 69-code input invariant failed")
    assigned = [c for i,c in enumerate(codes) if i % SHARD_COUNT == shard]
    records = []
    failure = None
    classification = "EVENT_PARSE_SHARD_PASS"
    try:
        for code in assigned:
            records.append(parse_one(code))
            time.sleep(2.5)
    except Exception as exc:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
    out = {
        "lab_id": base.LAB_ID,
        "phase": "EVENT_PARSE_V0_1_SHARD",
        "classification": classification,
        "shard": shard,
        "shard_count": SHARD_COUNT,
        "assigned_codes": len(assigned),
        "resolved_codes": len(records),
        "records": records,
        "failure": failure,
        "safety": base.SAFETY,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir/f"event_parse_shard_{shard}.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"shard":shard,"assigned":len(assigned),"resolved":len(records),"failure":failure}))
    return 0 if classification == "EVENT_PARSE_SHARD_PASS" else 2


def cmd_aggregate(input_path: Path, shards_dir: Path, out_dir: Path) -> int:
    source = json.loads(input_path.read_text())
    expected = set(source["codes"])
    records: list[dict[str, Any]] = []
    shard_receipts = []
    for p in sorted(glob.glob(str(shards_dir/"**/event_parse_shard_*.json"), recursive=True)):
        d = json.loads(Path(p).read_text())
        shard_receipts.append({"shard":d.get("shard"),"classification":d.get("classification"),"assigned_codes":d.get("assigned_codes"),"resolved_codes":d.get("resolved_codes"),"failure":d.get("failure")})
        if d.get("classification") != "EVENT_PARSE_SHARD_PASS":
            raise SystemExit("non-pass parse shard encountered")
        records.extend(d.get("records", []))
    codes = [r.get("code") for r in records]
    missing = sorted(expected - set(codes))
    dupes = sorted({c for c in codes if codes.count(c)>1})
    ambiguous = [r for r in records if r.get("direction")=="ADD" and r.get("asset_parse_ambiguous")]
    invalid_add = [r for r in records if r.get("direction")=="ADD" and not r.get("cross_margin_borrowable_assets")]
    if len(shard_receipts) != SHARD_COUNT or len(records)!=69 or missing or dupes:
        classification = "PROVENANCE_FAILURE"
        failure = f"coverage invariant failed: shards={len(shard_receipts)} records={len(records)} missing={len(missing)} dupes={len(dupes)}"
    elif ambiguous or invalid_add:
        classification = "EVENT_PARSE_AMBIGUOUS"
        failure = f"ambiguous_add={len(ambiguous)} invalid_add={len(invalid_add)}"
    else:
        classification = "EVENT_PARSE_PASS"
        failure = None
    directions = {k:sum(1 for r in records if r.get("direction")==k) for k in ("ADD","REMOVE","OTHER")}
    clean_assets = sum(len(r.get("cross_margin_borrowable_assets",[])) for r in records if r.get("direction")=="ADD")
    out = {
        "lab_id": base.LAB_ID,
        "phase": "EVENT_PARSE_V0_1_CANONICAL",
        "classification": classification,
        "failure": failure,
        "frozen_input_articles": 69,
        "resolved_articles": len(records),
        "directions": directions,
        "add_asset_mentions": clean_assets,
        "ambiguous_add_articles": [r.get("code") for r in ambiguous],
        "records": sorted(records, key=lambda r:(r.get("official_publish_ms") or 0,r.get("code"))),
        "shards": sorted(shard_receipts,key=lambda x:x["shard"]),
        "safety": base.SAFETY,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir/"BINANCE_MARGIN_BORROW_ACCESS_001_EVENT_PARSE_RECEIPT_V0_1.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"directions":directions,"add_asset_mentions":clean_assets,"ambiguous":len(ambiguous),"failure":failure}))
    return 0 if classification == "EVENT_PARSE_PASS" else 2


def main() -> int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("shard"); s.add_argument("--input",type=Path,required=True); s.add_argument("--shard",type=int,required=True); s.add_argument("--out",type=Path,required=True)
    a=sub.add_parser("aggregate"); a.add_argument("--input",type=Path,required=True); a.add_argument("--shards",type=Path,required=True); a.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=="shard": return cmd_shard(args.input,args.shard,args.out)
    return cmd_aggregate(args.input,args.shards,args.out)

if __name__=="__main__":
    sys.exit(main())
