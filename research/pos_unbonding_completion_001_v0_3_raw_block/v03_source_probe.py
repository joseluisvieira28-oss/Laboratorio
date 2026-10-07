#!/usr/bin/env python3
import base64, hashlib, json, os, urllib.parse, urllib.request
from datetime import datetime, timezone

OUT = "research/pos_unbonding_completion_001_v0_3_raw_block/SOURCE_PROBE_RECEIPT_V03.json"
UA = "CryptoLab-Unbonding-V03-SourceProbe/1.1"

PROBES = [
    {
        "chain": "dydx",
        "height": 15000000,
        "sources": {
            "kingnodes": "https://dydx-ops-archive-rpc.kingnodes.com",
            "polkachu": "https://dydx-dao-archive-rpc.polkachu.com",
        },
        "event_probe_range": [14950000, 15050000],
        "raw_scan": {"primary": "kingnodes", "secondary": "polkachu", "center": 15000000, "radius": 250},
    },
    {
        "chain": "celestia",
        "height": 2500000,
        "sources": {
            "dteam": "https://rpc.archive.celestia.mainnet.dteam.tech",
            "validatus": "https://rpc.archive.celestia.validatus.com",
            "itrocket": "https://celestia-mainnet-rpc.itrocket.net",
            "kj_archive_1": "http://157.180.10.38:40657",
            "kj_archive_2": "http://136.243.94.113:26667",
        },
        "event_probe_range": [2450000, 2550000],
    },
]

def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        status = getattr(r, "status", 200)
    return status, raw

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def parse_json(raw):
    return json.loads(raw.decode("utf-8"))

def read_varint(buf, i):
    shift = out = 0
    while True:
        if i >= len(buf):
            raise ValueError("truncated varint")
        b = buf[i]; i += 1
        out |= (b & 0x7F) << shift
        if not (b & 0x80):
            return out, i
        shift += 7
        if shift > 70:
            raise ValueError("varint overflow")

def fields(buf):
    i = 0
    while i < len(buf):
        key, i = read_varint(buf, i)
        num, wire = key >> 3, key & 7
        if wire == 0:
            val, i = read_varint(buf, i)
            yield num, wire, val
        elif wire == 1:
            val = buf[i:i+8]; i += 8
            yield num, wire, val
        elif wire == 2:
            n, i = read_varint(buf, i)
            val = buf[i:i+n]; i += n
            yield num, wire, val
        elif wire == 5:
            val = buf[i:i+4]; i += 4
            yield num, wire, val
        else:
            raise ValueError(f"unsupported wire={wire}")

def first_len(buf, n):
    for fn,w,v in fields(buf):
        if fn == n and w == 2:
            return v
    return None

def all_len(buf, n):
    return [v for fn,w,v in fields(buf) if fn == n and w == 2]

def first_varint(buf, n):
    for fn,w,v in fields(buf):
        if fn == n and w == 0:
            return v
    return None

def text_field(buf, n):
    v = first_len(buf, n)
    return v.decode("utf-8", "replace") if v is not None else None

def decode_coin(buf):
    if not buf:
        return None
    return {"denom": text_field(buf,1), "amount": text_field(buf,2)}

def decode_any(anybuf):
    type_url = text_field(anybuf,1)
    value = first_len(anybuf,2) or b""
    out = {"type_url": type_url}
    if type_url == "/cosmos.staking.v1beta1.MsgUndelegate":
        out.update({
            "delegator": text_field(value,1),
            "validator": text_field(value,2),
            "amount": decode_coin(first_len(value,3)),
        })
    elif type_url == "/cosmos.staking.v1beta1.MsgCancelUnbondingDelegation":
        out.update({
            "delegator": text_field(value,1),
            "validator": text_field(value,2),
            "amount": decode_coin(first_len(value,3)),
            "creation_height": first_varint(value,4),
        })
    return out

def decode_txraw(b64):
    raw = base64.b64decode(b64)
    body = first_len(raw,1)
    if body is None:
        return []
    return [decode_any(x) for x in all_len(body,1)]

def block_obj(raw):
    j = parse_json(raw)
    r = j.get("result",{})
    b = r.get("block",{})
    h = b.get("header",{})
    return r, b, h

def block_summary(raw):
    r,b,h = block_obj(raw)
    txs = ((b.get("data") or {}).get("txs") or [])
    return {
        "height": h.get("height"),
        "time": h.get("time"),
        "chain_id": h.get("chain_id"),
        "block_hash": ((r.get("block_id") or {}).get("hash")),
        "app_hash": h.get("app_hash"),
        "tx_count": len(txs),
        "txs": txs,
    }

def results_summary(raw):
    j = parse_json(raw)
    r = j.get("result",{})
    phases = {}
    for key in ("begin_block_events","end_block_events","finalize_block_events"):
        phases[key] = []
        for e in (r.get(key) or []):
            if e.get("type") == "complete_unbonding":
                phases[key].append({
                    "type": e.get("type"),
                    "attributes": [
                        {"key": a.get("key"), "value": a.get("value"), "index": a.get("index")}
                        for a in (e.get("attributes") or [])
                    ],
                })
    return {
        "height": r.get("height"),
        "complete_unbonding": phases,
        "tx_codes": [x.get("code",0) for x in (r.get("txs_results") or [])],
    }

def block_search(base, query):
    url = base + "/block_search?" + urllib.parse.urlencode({
        "query": query, "page": "1", "per_page": "10", "order_by": "asc"
    })
    try:
        status, raw = get(url, timeout=45)
        result = parse_json(raw).get("result",{})
        return {
            "status": status,
            "sha256": sha256(raw),
            "query": query,
            "total_count": result.get("total_count"),
            "returned_blocks": [
                {
                    "height": ((x.get("block") or {}).get("header") or {}).get("height"),
                    "time": ((x.get("block") or {}).get("header") or {}).get("time"),
                    "block_hash": ((x.get("block_id") or {}).get("hash")),
                }
                for x in (result.get("blocks") or [])
            ],
        }
    except Exception as e:
        return {"error": type(e).__name__ + ": " + str(e), "query": query}

def scan_raw_for_staking(base, secondary, center, radius):
    order = [center]
    for d in range(1, radius+1):
        order.extend([center-d, center+d])
    attempted = 0
    errors = 0
    for h in order:
        attempted += 1
        try:
            _, raw = get(f"{base}/block?height={h}", timeout=20)
            b = block_summary(raw)
            for i,t in enumerate(b["txs"]):
                try:
                    msgs = decode_txraw(t)
                except Exception:
                    continue
                target = [m for m in msgs if m.get("type_url") in (
                    "/cosmos.staking.v1beta1.MsgUndelegate",
                    "/cosmos.staking.v1beta1.MsgCancelUnbondingDelegation",
                )]
                if not target:
                    continue
                _, rrraw = get(f"{base}/block_results?height={h}", timeout=20)
                rr = results_summary(rrraw)
                code = rr["tx_codes"][i] if i < len(rr["tx_codes"]) else None
                if code not in (None,0):
                    continue
                corroboration = None
                try:
                    _, sraw = get(f"{secondary}/block?height={h}", timeout=20)
                    sb = block_summary(sraw)
                    corroboration = {
                        "block_hash_match": sb.get("block_hash") == b.get("block_hash"),
                        "time_match": sb.get("time") == b.get("time"),
                        "secondary_block_hash": sb.get("block_hash"),
                    }
                except Exception as e:
                    corroboration = {"error": type(e).__name__ + ": " + str(e)}
                return {
                    "status": "FOUND",
                    "requests_attempted": attempted,
                    "height": h,
                    "time": b.get("time"),
                    "block_hash": b.get("block_hash"),
                    "tx_index": i,
                    "tx_code": code,
                    "messages": target,
                    "corroboration": corroboration,
                }
        except Exception:
            errors += 1
    return {"status":"NOT_FOUND_IN_BOUNDED_WINDOW","requests_attempted":attempted,"request_errors":errors,"center":center,"radius":radius}

def main():
    receipt = {
        "freeze_commit": "93e0c6abff72d1d645c709382d8f06ccc558a34e",
        "scope": "source-only; no market endpoints or outcomes",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "probes": [],
    }

    for spec in PROBES:
        entry = {"chain": spec["chain"], "fixed_height": spec["height"], "sources": {}}
        canonical = []
        for name, base in spec["sources"].items():
            src = {"base": base}
            try:
                bs, braw = get(f"{base}/block?height={spec['height']}")
                rs, rraw = get(f"{base}/block_results?height={spec['height']}")
                b = block_summary(braw)
                rr = results_summary(rraw)
                txs = b.pop("txs")
                decoded = []
                for i,t in enumerate(txs):
                    try:
                        staking = [m for m in decode_txraw(t) if m.get("type_url","").startswith("/cosmos.staking.")]
                        if staking:
                            decoded.append({"tx_index":i,"code":rr["tx_codes"][i] if i < len(rr["tx_codes"]) else None,"staking_messages":staking})
                    except Exception as de:
                        decoded.append({"tx_index":i,"decode_error":str(de)})
                src.update({
                    "block_http": bs,
                    "block_sha256": sha256(braw),
                    "block": b,
                    "block_results_http": rs,
                    "block_results_sha256": sha256(rraw),
                    "block_results": rr,
                    "decoded_staking_txs": decoded,
                    "block_search_exact_height": block_search(base, f"block.height = {spec['height']}"),
                    "block_search_complete_unbonding": block_search(
                        base,
                        f"complete_unbonding.amount EXISTS AND block.height >= {spec['event_probe_range'][0]} AND block.height <= {spec['event_probe_range'][1]}"
                    ),
                })
                canonical.append((name,b.get("block_hash"),b.get("time"),b.get("app_hash")))
            except Exception as e:
                src["error"] = type(e).__name__ + ": " + str(e)
            entry["sources"][name] = src

        ok = [x for x in canonical if x[1] and x[2]]
        entry["independent_reconciliation"] = {
            "successful_sources": len(ok),
            "block_hash_match": len(ok) >= 2 and len({x[1] for x in ok}) == 1,
            "time_match": len(ok) >= 2 and len({x[2] for x in ok}) == 1,
            "app_hash_match": len(ok) >= 2 and len({x[3] for x in ok}) == 1,
            "successful_source_names": [x[0] for x in ok],
        }
        if spec.get("raw_scan"):
            rspec = spec["raw_scan"]
            entry["raw_staking_scan"] = scan_raw_for_staking(
                spec["sources"][rspec["primary"]],
                spec["sources"][rspec["secondary"]],
                rspec["center"],
                rspec["radius"],
            )
        receipt["probes"].append(entry)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
