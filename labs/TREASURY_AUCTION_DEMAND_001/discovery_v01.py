from __future__ import annotations

import csv, hashlib, io, json, math, random, re, sys, urllib.request, zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Local frozen source collector: source semantics are reused exactly, then rebound to the frozen SHA.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_gate_v01 as src

LAB_ID = "TREASURY-AUCTION-DEMAND-001"
MVE_ID = "TAD-BTC-D1-001"
EXPECTED_SOURCE_SHA = "ab2695123b04c6e320bda23e5496b1dcfadabec8c6784211a10407ac87499892"
DISCOVERY_START = date(2021, 1, 1)
DISCOVERY_END = date(2023, 12, 31)
BINANCE_BASE = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d"
OUT = Path("artifacts/treasury_auction_demand_discovery_v01")
OUT.mkdir(parents=True, exist_ok=True)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str, accept: str = "*/*") -> bytes:
    # This runner must never open BTC market archives for protected years.
    if "data.binance.vision" in url and any(y in url for y in ("2024", "2025", "2026")):
        raise RuntimeError(f"PROTECTED_BTC_URL_BLOCKED:{url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TAD-BTC-D1-001", "Accept": accept})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
        if not b:
            raise RuntimeError(f"EMPTY_RESPONSE:{url}")
        return b


def rebuild_frozen_source():
    rows, _receipts = src.fetch_pages()
    retained = []
    for r in rows:
        term = str(r.get("original_security_term", "")).strip()
        if term not in src.TERMS:
            continue
        if not src.flag_no(r.get("inflation_index_security")) or not src.flag_no(r.get("floating_rate")):
            continue
        if any(r.get(k) is None or str(r.get(k)).strip() == "" for k in src.REQ):
            continue
        ad = str(r["auction_date"])
        if not (src.START <= ad <= src.END):
            continue
        btc = src.dec(r["bid_to_cover_ratio"])
        comp = src.dec(r["comp_accepted"])
        dealer = src.dec(r["primary_dealer_accepted"])
        direct = src.dec(r["direct_bidder_accepted"])
        indirect = src.dec(r["indirect_bidder_accepted"])
        total_a = src.dec(r["total_accepted"])
        total_t = src.dec(r["total_tendered"])
        if btc <= 0 or any(x < 0 for x in (comp, dealer, direct, indirect, total_a, total_t)):
            continue
        if abs((dealer + direct + indirect) - comp) > Decimal(1):
            continue
        retained.append({
            "auction_date": ad,
            "cusip": str(r["cusip"]),
            "security_type": str(r["security_type"]),
            "original_security_term": term,
            "inflation_index_security": str(r["inflation_index_security"]),
            "floating_rate": str(r["floating_rate"]),
            "bid_to_cover_ratio": str(btc),
            "comp_accepted": str(comp),
            "primary_dealer_accepted": str(dealer),
            "direct_bidder_accepted": str(direct),
            "indirect_bidder_accepted": str(indirect),
            "total_accepted": str(total_a),
            "total_tendered": str(total_t),
        })
    retained.sort(key=lambda x: (x["original_security_term"], x["auction_date"], x["cusip"]))

    prev = {}
    canonical = []
    for r in retained:
        term = r["original_security_term"]
        cur = Decimal(r["bid_to_cover_ratio"])
        d = None if term not in prev else cur - prev[term]
        prev[term] = cur
        rr = dict(r)
        rr["delta_bid_to_cover"] = None if d is None else str(d)
        canonical.append(rr)

    cb = b"".join(src.canonical_json(r) for r in canonical)
    actual = sha(cb)
    if actual != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"TREASURY_CANONICAL_HASH_MISMATCH:{actual}")
    if len(canonical) != 337:
        raise RuntimeError(f"TREASURY_CANONICAL_COUNT_MISMATCH:{len(canonical)}")
    return canonical


def parse_checksum(b: bytes) -> str:
    m = re.search(r"\b([0-9a-fA-F]{64})\b", b.decode("utf-8-sig", "replace"))
    if not m:
        raise RuntimeError("BINANCE_CHECKSUM_PARSE_FAILURE")
    return m.group(1).lower()


def ts_to_date(x: int) -> date:
    if x > 10**15:
        sec = x / 1_000_000.0
    elif x > 10**12:
        sec = x / 1_000.0
    else:
        sec = float(x)
    return datetime.fromtimestamp(sec, tz=timezone.utc).date()


def month_iter():
    y, m = 2021, 1
    while (y, m) <= (2023, 12):
        yield y, m
        m += 1
        if m == 13:
            y += 1
            m = 1


def load_binance_daily():
    prices = {}
    meta = []
    for y, m in month_iter():
        ym = f"{y:04d}-{m:02d}"
        fn = f"BTCUSDT-1d-{ym}.zip"
        url = f"{BINANCE_BASE}/{fn}"
        zb = fetch(url, "application/zip,*/*")
        provider = parse_checksum(fetch(url + ".CHECKSUM", "text/plain,*/*"))
        actual = sha(zb)
        if actual != provider:
            raise RuntimeError(f"BINANCE_ZIP_CHECKSUM_MISMATCH:{ym}")
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise RuntimeError(f"BINANCE_MEMBER_COUNT:{ym}:{len(names)}")
            cb = z.read(names[0])
        count = 0
        for row in csv.reader(io.StringIO(cb.decode("utf-8-sig", "replace"))):
            if not row:
                continue
            try:
                ts = int(row[0])
            except ValueError:
                continue
            if len(row) < 5:
                raise RuntimeError(f"BINANCE_ROW_SHORT:{ym}")
            d = ts_to_date(ts)
            if d < DISCOVERY_START or d > DISCOVERY_END:
                continue
            op = float(row[1])
            if not math.isfinite(op) or op <= 0:
                raise RuntimeError(f"BINANCE_INVALID_OPEN:{d}")
            if d in prices:
                raise RuntimeError(f"BINANCE_DUPLICATE_DATE:{d}")
            prices[d] = op
            count += 1
        meta.append({"month": ym, "zip_sha256": actual, "provider_checksum": provider, "csv_sha256": sha(cb), "rows": count})

    expected = (DISCOVERY_END - DISCOVERY_START).days + 1
    if len(prices) != expected:
        raise RuntimeError(f"BINANCE_DAILY_COVERAGE:{len(prices)}/{expected}")
    manifest_sha = sha(json.dumps(meta, sort_keys=True, separators=(",", ":")).encode())
    return prices, meta, manifest_sha


def pf(values):
    pos = sum(x for x in values if x > 0)
    neg = -sum(x for x in values if x < 0)
    if neg == 0:
        return float("inf") if pos > 0 else 0.0
    return pos / neg


def percentile(xs, p):
    if not xs:
        return None
    q = (len(xs) - 1) * p
    lo, hi = int(math.floor(q)), int(math.ceil(q))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - q) + xs[hi] * (q - lo)


def bootstrap(values):
    n, L = len(values), 5
    if n < L:
        return [None, None]
    blocks = [values[i:i+L] for i in range(n - L + 1)]
    rng = random.Random(230911)
    means = []
    for _ in range(5000):
        s = []
        while len(s) < n:
            s.extend(blocks[rng.randrange(len(blocks))])
        s = s[:n]
        means.append(sum(s) / n)
    means.sort()
    return [percentile(means, 0.025), percentile(means, 0.975)]


def main():
    print(f"{LAB_ID} / {MVE_ID} — ONE-SHOT DISCOVERY 2021-2023 ONLY")
    print("2024 OOS LOCKED / 2025 LOCKED / 2026 FORBIDDEN")
    canonical = rebuild_frozen_source()
    prices, market_meta, market_manifest_sha = load_binance_daily()

    by_date = defaultdict(list)
    for r in canonical:
        ad = date.fromisoformat(r["auction_date"])
        if not (DISCOVERY_START <= ad <= DISCOVERY_END):
            continue
        ds = r["delta_bid_to_cover"]
        if ds is None:
            continue
        d = Decimal(ds)
        direction = 1 if d > 0 else (-1 if d < 0 else 0)
        by_date[ad].append({"term": r["original_security_term"], "cusip": r["cusip"], "delta": str(d), "direction": direction})

    event_rows = []
    conflict_dates = 0
    zero_only_dates = 0
    for ad in sorted(by_date):
        nonzero = [x for x in by_date[ad] if x["direction"] != 0]
        if not nonzero:
            zero_only_dates += 1
            continue
        dirs = {x["direction"] for x in nonzero}
        if len(dirs) != 1:
            conflict_dates += 1
            continue
        direction = next(iter(dirs))
        entry = ad + timedelta(days=1)
        exitd = entry + timedelta(days=1)
        if entry < DISCOVERY_START or exitd > DISCOVERY_END:
            continue
        if entry not in prices or exitd not in prices:
            raise RuntimeError(f"MISSING_BTC_BAR:{entry}:{exitd}")
        gross = direction * (prices[exitd] / prices[entry] - 1.0) * 10000.0
        event_rows.append({
            "auction_date": ad.isoformat(),
            "direction": "LONG" if direction == 1 else "SHORT",
            "direction_num": direction,
            "constituents": nonzero,
            "entry_date": entry.isoformat(),
            "exit_date": exitd.isoformat(),
            "entry_open": prices[entry],
            "exit_open": prices[exitd],
            "gross_bps": gross,
            "net10_bps": gross - 10.0,
            "net20_bps": gross - 20.0,
        })

    n = len(event_rows)
    longs = sum(r["direction_num"] == 1 for r in event_rows)
    shorts = sum(r["direction_num"] == -1 for r in event_rows)
    g = [r["gross_bps"] for r in event_rows]
    v10 = [r["net10_bps"] for r in event_rows]
    v20 = [r["net20_bps"] for r in event_rows]
    mean_g = sum(g) / n if n else None
    sg = sorted(g)
    median_g = (sg[n//2] if n % 2 else (sg[n//2-1] + sg[n//2]) / 2.0) if n else None
    mean10 = sum(v10) / n if n else None
    mean20 = sum(v20) / n if n else None
    pf10 = pf(v10) if n else None
    win10 = sum(x > 0 for x in v10) / n if n else None
    ci = bootstrap(v10) if n else [None, None]

    years = {}
    positive_gross_by_year = {}
    for y in (2021, 2022, 2023):
        rr = [r for r in event_rows if r["entry_date"].startswith(str(y) + "-")]
        vv = [r["net10_bps"] for r in rr]
        gg = [r["gross_bps"] for r in rr]
        years[str(y)] = {"n": len(rr), "mean_net10_bps": (sum(vv)/len(vv) if vv else None), "gross_sum_bps": sum(gg)}
        positive_gross_by_year[str(y)] = max(0.0, sum(gg))

    nonnegative_years = sum(1 for y in years.values() if y["n"] and y["mean_net10_bps"] >= 0)
    total_positive_gross = sum(positive_gross_by_year.values())
    max_positive_year_share = (max(positive_gross_by_year.values()) / total_positive_gross) if total_positive_gross > 0 else None

    gates = {
        "n_ge_180": n >= 180,
        "longs_ge_60": longs >= 60,
        "shorts_ge_60": shorts >= 60,
        "mean_net10_gt_0": mean10 is not None and mean10 > 0,
        "pf_net10_gt_1_05": pf10 is not None and pf10 > 1.05,
        "bootstrap_95_lower_gt_0": ci[0] is not None and ci[0] > 0,
        "nonnegative_years_ge_2_of_3": nonnegative_years >= 2,
        "max_positive_year_share_le_0_80": max_positive_year_share is not None and max_positive_year_share <= 0.80,
        "source_binding_pass": True,
        "access_2024_btc": False,
        "access_2025_btc": False,
        "access_2026_btc": False,
        "live_trading": False,
        "exchange_mutation": False,
    }

    promotion_keys = ["n_ge_180", "longs_ge_60", "shorts_ge_60", "mean_net10_gt_0", "pf_net10_gt_1_05", "bootstrap_95_lower_gt_0", "nonnegative_years_ge_2_of_3", "max_positive_year_share_le_0_80", "source_binding_pass"]
    classification = "DISCOVERY_PASS_CANDIDATE_2024_OOS_LOCKED" if all(gates[k] for k in promotion_keys) else "DISCOVERY_FAIL_NO_PROMOTION"

    trade_bytes = b"".join((json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n").encode() for r in event_rows)
    (OUT / "resolved_trades_v01.jsonl").write_bytes(trade_bytes)
    result = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "treasury_canonical_sha256": EXPECTED_SOURCE_SHA,
        "source_binding_pass": True,
        "btc_market_manifest_sha256": market_manifest_sha,
        "btc_monthly_archives_verified": len(market_meta),
        "latest_btc_market_date_opened": "2023-12-31",
        "access_2024_btc": False,
        "access_2025_btc": False,
        "access_2026_btc": False,
        "n_resolved": n,
        "longs": longs,
        "shorts": shorts,
        "conflict_dates_suppressed": conflict_dates,
        "zero_only_dates": zero_only_dates,
        "mean_gross_bps": mean_g,
        "median_gross_bps": median_g,
        "mean_net10_bps": mean10,
        "mean_net20_bps": mean20,
        "profit_factor_net10": pf10,
        "win_rate_net10": win10,
        "bootstrap_mean_net10_95_ci": ci,
        "bootstrap_repetitions": 5000,
        "bootstrap_seed": 230911,
        "bootstrap_block_trades": 5,
        "calendar_years": years,
        "nonnegative_years": nonnegative_years,
        "positive_gross_by_year_bps": positive_gross_by_year,
        "max_positive_year_share": max_positive_year_share,
        "gates": gates,
        "trades_sha256": sha(trade_bytes),
        "orders_submitted": False,
        "live_trading": False,
        "exchange_mutation": False,
        "oos_2024_authorized": False,
    }
    rb = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    (OUT / "discovery_result_v01.json").write_bytes(rb)
    (OUT / "market_manifest_v01.json").write_text(json.dumps(market_meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
