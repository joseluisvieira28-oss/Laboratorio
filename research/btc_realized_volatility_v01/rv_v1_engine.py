#!/usr/bin/env python3
"""Frozen BTC RV V1 research only. Public, checksum-verified Binance archive; NO API auth/trading.
Read PRE_OUTCOME_SCIENCE_FREEZE_2026-10-14.md before change. NO post-outcome tuning.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import pathlib
import statistics
import sys
import urllib.request
import zipfile

UTC = dt.timezone.utc
HOUR = 3600_000
START = int(dt.datetime(2021, 1, 1, tzinfo=UTC).timestamp() * 1000)
END = int(dt.datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000)
WARM = int(dt.datetime(2020, 1, 1, tzinfo=UTC).timestamp() * 1000)
BASE = "https://data.binance.vision/data/futures/um/monthly"
FEE = 0.0008
COSTS = {"BASE": 0.0002, "STRESS": 0.0005}
ARMS = ("EMA50_BENCH", "EMA50_RV_FILTER", "RV_EXPANSION_ENTRY")


class SourceBlocked(Exception):
    pass


def ts_ms(raw):
    v = int(raw)
    if v >= 10**15:
        if v % 1000:  # Require exact millisecond candle boundaries.
            raise SourceBlocked("microseconds are not on whole-ms boundary")
        v //= 1000
    if not (1400000000000 < v < 1900000000000):
        raise SourceBlocked("invalid timestamp " + str(raw))
    return v


def months(year_a, year_b):
    for year in range(year_a, year_b + 1):
        for month in range(1, 13):
            yield year, month


def verified_rows(group, filename, receipt):
    link = f"{BASE}/{group}/{filename}"
    request = urllib.request.Request(link + ".CHECKSUM", headers={"User-Agent": "CryptoLab-research-source-only/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            checksum = response.read(400).decode("ascii", "strict").strip()
        expected = checksum.split()[0].lower()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise SourceBlocked("bad publisher checksum text for " + filename)
        request = urllib.request.Request(link, headers={"User-Agent": "CryptoLab-research-source-only/0.1"})
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read(25_000_000)
    except Exception as exc:
        raise SourceBlocked("public archive fetch failed " + filename + ": " + str(exc)[:260]) from exc
    actual = hashlib.sha256(payload).hexdigest()
    if expected != actual:
        raise SourceBlocked("publisher SHA256 mismatch " + filename)
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as pack:
            found = [n for n in pack.namelist() if n.endswith(".csv")]
            if len(found) != 1 or not found[0].endswith(filename.replace(".zip", ".csv")):
                raise SourceBlocked("unexpected ZIP member " + filename)
            raw = pack.read(found[0]).decode("utf-8-sig")
            rows = list(csv.reader(io.StringIO(raw)))
    except (zipfile.BadZipFile, UnicodeError, ValueError) as exc:
        raise SourceBlocked("archive format failed " + filename) from exc
    receipt.append({"file": filename, "publisher_sha256": expected, "rows": len(rows)})
    return rows


def load_public():
    receipts = []
    hours = []
    funding = {}
    for y, m in months(2020, 2025):
        filename = f"BTCUSDT-1h-{y}-{m:02}.zip"
        rows = verified_rows("klines/BTCUSDT/1h", filename, receipts)
        for row in rows:
            if not row or not row[0].strip().isdigit():
                continue
            if len(row) < 5:
                raise SourceBlocked("kline short row " + filename)
            t = ts_ms(row[0])
            o, hi, lo, cl = [float(row[j]) for j in (1, 2, 3, 4)]
            if not (lo > 0 and lo <= min(o, cl) <= max(o, cl) <= hi and all(math.isfinite(x) for x in (o, hi, lo, cl))):
                raise SourceBlocked("invalid OHLC " + filename)
            hours.append((t, o, hi, lo, cl))
    if not hours or hours[0][0] != WARM or hours[-1][0] != END - HOUR:
        raise SourceBlocked("source date coverage is not full UTC 2020-25")
    for i, h in enumerate(hours):
        if h[0] != WARM + i * HOUR:
            raise SourceBlocked("duplicate/missing/out-of-order UTC 1h candle at " + str(i))
    if len(hours) != (END-WARM)//HOUR:
        raise SourceBlocked("hourly source coverage count mismatch")
    for y, m in months(2021, 2025):
        filename = f"BTCUSDT-fundingRate-{y}-{m:02}.zip"
        rows = verified_rows("fundingRate/BTCUSDT", filename, receipts)
        if len(rows) < 2:
            raise SourceBlocked("missing funding rows " + filename)
        header = [s.strip().lower() for s in rows[0]]
        is_header = not rows[0][0].strip().isdigit()
        if is_header:
            def pos(keys, fallback):
                return next((i for i, h in enumerate(header) if h in keys), fallback)
            ti = pos({"calc_time", "fundingtime", "funding_time"}, 0)
            ri = pos({"last_funding_rate", "fundingrate", "funding_rate"}, -1)
            mi = pos({"markprice", "mark_price"}, -1)
        else:
            ti, ri, mi = 0, 2, -1
        for row in rows[1:] if is_header else rows:
            if not row or not row[ti].strip().isdigit():
                continue
            t = ts_ms(row[ti])
            rate = float(row[ri])
            mark = float(row[mi]) if mi >= 0 and row[mi] else None
            if t % HOUR != 0 or not math.isfinite(rate) or abs(rate) > 0.1:
                raise SourceBlocked("malformed funding record " + filename)
            if mark is not None and (not math.isfinite(mark) or mark <= 0):
                raise SourceBlocked("invalid funding mark " + filename)
            if not START <= t < END or t in funding:
                raise SourceBlocked("funding outside frozen window/duplicate " + filename)
            funding[t] = (rate, mark)
    if len(funding) < 4500:
        raise SourceBlocked("funding source implausibly incomplete " + str(len(funding)))
    receipt = {"market_rows": len(hours), "funding_events": len(funding),
               "funding_exact_mark_events": sum(v[1] is not None for v in funding.values()),
               "publisher_files": receipts,
               "market_start_ms": WARM, "market_end_exclusive_ms": END}
    return hours, funding, receipt


def features(hours):
    if len(hours) % 4:
        raise SourceBlocked("hours must form full UTC 4h candles")
    bars = []
    for j in range(0, len(hours), 4):
        block = hours[j:j+4]
        if block[0][0] % (4*HOUR) or any(block[k][0] != block[0][0]+k*HOUR for k in range(4)):
            raise SourceBlocked("misaligned UTC 4h source")
        bars.append((block[0][0], block[0][1], max(x[2] for x in block),
                     min(x[3] for x in block), block[-1][4]))
    closing = [b[4] for b in bars]
    ema = [None] * len(bars)
    for i in range(49, len(bars)):
        ema[i] = sum(closing[:50])/50 if i == 49 else ema[i-1] + 2/51*(closing[i]-ema[i-1])
    ratios = [None]*len(bars)
    returns = [None]+[math.log(closing[i]/closing[i-1]) for i in range(1, len(bars))]
    for i in range(126, len(bars)):
        window = returns[i-125:i+1]
        long = statistics.pstdev(window)
        if long > 0:
            ratios[i] = statistics.pstdev(returns[i-23:i+1])/long
    decisions = {}
    for i in range(130, len(bars)):
        t = bars[i][0]+4*HOUR  # FIRST hour after this 4h candle completed
        trend = closing[i]>ema[i] and ema[i]>ema[i-3]
        cross = closing[i-1]<=ema[i-1] and closing[i]>ema[i]
        r, prev = ratios[i], ratios[i-1]
        expanding = (r is not None and prev is not None and r>1.35 and r>prev)
        rv_cross = expanding and prev<=1.35
        signals = {"EMA50_BENCH":trend and cross,
                   "EMA50_RV_FILTER":trend and cross and expanding,
                   "RV_EXPANSION_ENTRY":trend and rv_cross}
        decisions[t] = {"signals":signals,"close_below":closing[i]<ema[i]}
    return decisions


def replay(hours, funding, decisions, arm, slip):
    equity = 10000.0
    position = None
    trades = []
    peak, maxdd = equity, 0.0
    yearly = {str(y): 0.0 for y in range(2021, 2026)}
    costtot = {"entry_fee":0.0, "exit_fee":0.0,"funding":0.0}
    prior_year = 2020
    for t, op, hi, lo, cl in hours:
        if t < START:
            continue
        # Funding at settlement timestamp: only an existing position BEFORE this hour qualifies.
        if position is not None and t in funding:
            rate, mark = funding[t]
            price = op if mark is None else mark
            paid = -position["quantity"]*price*rate
            equity += paid
            position["funding"] += paid
            costtot["funding"] += paid
        d = decisions.get(t)
        reason = None
        if position is not None and d:
            if d["close_below"]:
                reason = "EMA50"
            elif t-position["opened"] >= 180*4*HOUR:
                reason = "TIME30D"
        if position is not None and reason is None and lo<=position["stop"]:
            reason = "STOP"
        if reason and position is not None:
            raw = min(op,position["stop"]) if reason=="STOP" else op
            sell = raw*(1-slip)
            fee = position["quantity"]*sell*FEE
            proceeds = position["quantity"]*(sell-position["entry"])
            net = proceeds -fee + position["funding"] -position["entry_fee"]
            equity += proceeds-fee
            costtot["exit_fee"] += fee
            trades.append({"arm":arm,"time":t,"opened":position["opened"],"reason":reason,
                           "entry":position["entry"],"exit":sell,"quantity":position["quantity"],
                           "entry_fee":position["entry_fee"],"exit_fee":fee,
                           "funding":position["funding"],"net":net})
            yearly[str(dt.datetime.fromtimestamp(t/1000,UTC).year)] += net
            position = None
        # One entry per observed 4h boundary; no same-timestamp exit/re-entry.
        if position is None and reason is None and d and d["signals"][arm]:
            buy = op*(1+slip)
            quantity = (equity*.2)/buy
            fee = quantity*buy*FEE
            if quantity>0 and fee<equity:
                equity -= fee
                costtot["entry_fee"] += fee
                position = {"opened":t,"entry":buy,"stop":buy*.96,
                            "quantity":quantity,"entry_fee":fee,"funding":0.0}
        # Hourly conservative MTM (no hypothetical exit close fee; terminal flag explicit)
        mtm = equity+(position["quantity"]*(cl-position["entry"]) if position else 0.0)
        peak = max(peak,mtm)
        maxdd = min(maxdd,mtm/peak-1)
    last = hours[-1][4]
    terminal = equity+(position["quantity"]*(last-position["entry"]) if position else 0.0)
    pnls = [t["net"] for t in trades]
    wins = [p for p in pnls if p>0]
    losses = [-p for p in pnls if p<0]
    pf = sum(wins)/sum(losses) if losses else None
    top3 = sum(sorted(wins,reverse=True)[:3])
    ret = {"arm":arm,"slippage_bps_each_side":round(slip*10000),
           "closed":len(trades),"wins":len(wins),"losses":len(losses),
           "pf":pf,"closed_net":sum(pnls),"terminal_equity":terminal,
           "terminal_return_pct":(terminal/10000-1)*100,
           "hourly_mtm_max_drawdown_pct":100*maxdd, "yearly_closed_net":yearly,
           "top3_winner_net":top3,"static_closed_net_minus_top3":sum(pnls)-top3,
           "funding_total":costtot["funding"],"entry_fee_total":costtot["entry_fee"],
           "exit_fee_total":costtot["exit_fee"],"open_position":position is not None}
    return ret,trades


def candidacy(result, benchmark):
    criteria = {
        "min_60_trades":result["closed"]>=60,
        "2024_2025_min_8_exits":False,  # computed from receipts, not realized yearly PnL proxy.
        "base_stress_positive":False,   # set by combined evaluator below.
        "pf_gt_1_15":result["pf"] is not None and result["pf"]>1.15,
        "base_dd_lt_20":result["hourly_mtm_max_drawdown_pct"]>=-20,
        "at_least_four_positive_years":sum(v>0 for v in result["yearly_closed_net"].values())>=4,
        "top3_resilience":result["static_closed_net_minus_top3"]>0,
        "beats_ema_control":False,
    }
    return criteria


def main():
    output = pathlib.Path(os.environ.get("RV_OUT", "research_rv_outputs"))
    output.mkdir(parents=True,exist_ok=True)
    try:
        market, funding, provenance = load_public()
        (output/"publisher_source_receipt.json").write_text(json.dumps(provenance,indent=2))
        decisions = features(market)
        outcomes = {}
        all_trades = []
        for label, slip in COSTS.items():
            outcomes[label] = {}
            for arm in ARMS:
                result, trades = replay(market,funding,decisions,arm,slip)
                outcomes[label][arm] = result
                for tr in trades:
                    tr["scenario"]=label
                all_trades.extend(trades)
        controls = {}
        for arm in ARMS[1:]:
            b=outcomes["BASE"][arm]
            s=outcomes["STRESS"][arm]
            e=outcomes["BASE"]["EMA50_BENCH"]
            n_by_year = {str(year):sum(1 for tr in all_trades if tr["arm"]==arm
                    and tr["scenario"]=="BASE" and
                    dt.datetime.fromtimestamp(tr["time"]/1000,UTC).year==year)
                    for year in range(2021,2026)}
            criteria = candidacy(b,e)
            criteria["2024_2025_min_8_exits"] = n_by_year["2024"]>=8 and n_by_year["2025"]>=8
            criteria["base_stress_positive"] = b["terminal_return_pct"]>0 and s["terminal_return_pct"]>0
            criteria["pf_gt_1_15"] = all(x["pf"] is not None and x["pf"]>1.15 for x in (b,s))
            criteria["stress_dd_lt_25"] = s["hourly_mtm_max_drawdown_pct"]>=-25
            criteria["beats_ema_control"] = (b["closed_net"]/max(1,b["closed"]) >
              e["closed_net"]/max(1,e["closed"])) if arm=="EMA50_RV_FILTER" else (
                  b["terminal_return_pct"] > e["terminal_return_pct"] and b["pf"] is not None
                  and e["pf"] is not None and b["pf"]>e["pf"])
            controls[arm] = {"criteria":criteria,"historical_only":True,
                             "historical_gate":"DESCRIPTIVE_PASS_NOT_OOS" if all(criteria.values()) else "NO_HISTORICAL_CANDIDACY",
                             "n_by_exit_year":n_by_year}
        envelope={"science_authority":"RESEARCH_ONLY","live_trading":"NO_GO",
                  "period":"2021-01 through 2025-12, 2020 warmup; PROTECTED_2026_UNTOUCHED",
                  "funding_exact_mark_count":provenance["funding_exact_mark_events"],
                  "funding_count":provenance["funding_events"],
                  "model_outputs":outcomes,"candidacy":controls,
                  "interpretation":"Already-studied market years; no independent OOS or exchange executable quotes.",
                  "note":"Return and DD are simulated. Mark funding price is historical exact only when archive includes authenticated markPrice; otherwise 1h OPEN proxy."}
        (output/"rv_v1_results.json").write_text(json.dumps(envelope,indent=2,allow_nan=False))
        if all_trades:
            with (output/"rv_v1_trade_ledger.csv").open("w",newline="") as fh:
                writer=csv.DictWriter(fh,fieldnames=list(all_trades[0]))
                writer.writeheader()
                writer.writerows(all_trades)
        print(json.dumps({"state":"HISTORICAL_RESEARCH_FINISHED","candidate_states":
              {k:v["historical_gate"] for k,v in controls.items()},
              "summary":{scenario:{arm:{"closed":v["closed"],
                        "return_pct":round(v["terminal_return_pct"],4),
                        "pf":None if v["pf"] is None else round(v["pf"],4)}
                        for arm,v in arms.items()} for scenario,arms in outcomes.items()}},indent=2))
    except (SourceBlocked, ValueError, OSError, ZeroDivisionError) as exc:
        receipt={"state":"SOURCE_BLOCKED_OR_ENGINE_INVALID","error":str(exc),"live_trading":"NO_GO"}
        (output/"fail_closed.json").write_text(json.dumps(receipt,indent=2))
        print(json.dumps(receipt))
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
