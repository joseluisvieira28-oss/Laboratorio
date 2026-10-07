#!/usr/bin/env python3
import base64, hashlib, json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

OUT = "research/pos_unbonding_completion_001_v0_3_raw_block/SOURCE_PROBE_RECEIPT_V03.json"

PROBES = [
    {
        "chain": "dydx",
        "height": 15000000,
        "sources": {
            "kingnodes": "https://dydx-ops-archive-rpc.kingnodes.com",
            "polkachu": "https://dydx-dao-archive-rpc.polkachu.com",
        },
        "event_probe_range": [14950000, 15050000],
    },
    {
        "chain": "celestia",
        "height": 2500000,
        "sources": {
            "dteam": "https://rpc.archive.celestia.mainnet.dteam.tech",
            "validatus": "https://rpc.archive.celestia.validatus.com",
        },
        "event_probe_range": [2450000, 2550000],
    },
]

UA = "CryptoLab-Unbonding-V03-SourceProbe/1.0"

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
    shift = 0
    out = 0
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

def first_len(buf, field_no):
    for n,w,v in fields(buf):
        if n == field_no and w == 2:
            return v
    return None

def all_len(buf, field_no):
    return [v for n,w,v in fields(buf) if n == field_no and w == 2]

def first_varint(buf, field_no):
    for n,w,v in fields(buf):
        if n == field_no and w == 0:
            return v
    return None

def text_field(buf, field_no):
    v = first_len(buf, field_no)
    return v.decode("utf-8", "replace") if v is not None else None

def decode_coin(buf):
    if not buf:
        return None
    return {"denom": text_field(buf,1), "amount": text_field(buf,2)}

def decode_staking_any(anybuf):
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
    return [decode_staking_any(x) for x in all_len(body,1)]

def block_summary(raw):
    j = parse_json(raw)
    r = j.get("result",{})
    b = r.get("block",{})
    h = b.get("header",{})
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
        evs = r.get(key) or []
        phases[key] = [
            {
                "type": e.get("type"),
                "attributes": [
                    {"key": a.get("key"), "value": a.get("value"), "index": a.get("index")}
                    for a in (e.get("attributes") or [])
                ],
            }
            for e in evs
            if e.get("type") == "complete_unbonding"
        ]
    codes = []
    for x in (r.get("txs_results") or []):
        codes.append(x.get("code",0))
    return {"height": r.get("height"), "complete_unbonding": phases, "tx_codes": codes}

def search_complete_unbonding(base, lo, hi):
    q = f"complete_unbonding.amount EXISTS AND block.height >= {lo} AND block.height <= {hi}"
    url = base + "/block_search?" + urllib.parse.urlencode({
        "query": q, "page": "1", "per_page": "10", "order_by": "asc"
    })
    try:
        status, raw = get(url, timeout=45)
        j = parse_json(raw)
        result = j.get("result",{})
        return {
            "status": status,
            "sha256": sha256(raw),
            "query": q,
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
        return {"error": type(e).__name__ + ": " + str(e), "query": q}

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
                decoded = []
                tx_codes = rr["tx_codes"]
                for i, t in enumerate(b.pop("txs")):
                    try:
                        msgs = decode_txraw(t)
                        staking = [m for m in msgs if m.get("type_url","").startswith("/cosmos.staking.")]
                        if staking:
                            decoded.append({"tx_index": i, "code": tx_codes[i] if i < len(tx_codes) else None, "staking_messages": staking})
                    except Exception as de:
                        decoded.append({"tx_index": i, "decode_error": str(de)})
                src.update({
                    "block_http": bs,
                    "block_sha256": sha256(braw),
                    "block": b,
                    "block_results_http": rs,
                    "block_results_sha256": sha256(rraw),
                    "block_results": rr,
                    "decoded_staking_txs": decoded,
                    "block_search_probe": search_complete_unbonding(base, *spec["event_probe_range"]),
                })
                canonical.append((name, b.get("block_hash"), b.get("time"), b.get("app_hash")))
            except Exception as e:
                src["error"] = type(e).__name__ + ": " + str(e)
            entry["sources"][name] = src

        ok = [x for x in canonical if x[1] and x[2]]
        entry["independent_reconciliation"] = {
            "successful_sources": len(ok),
            "block_hash_match": len(ok) >= 2 and len({x[1] for x in ok}) == 1,
            "time_match": len(ok) >= 2 and len({x[2] for x in ok}) == 1,
            "app_hash_match": len(ok) >= 2 and len({x[3] for x in ok}) == 1,
        }
        receipt["probes"].append(entry)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
