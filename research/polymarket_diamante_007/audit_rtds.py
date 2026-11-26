"""Verify user-provided RTDS captures. Run against a directory of original gzip files."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
args = parser.parse_args()

def utc(seconds):
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()

def quantile(values, p):
    return round(sorted(values)[int(p * (len(values)-1))], 3)

seen = {}
results = {}
for path in sorted(args.input.glob("BTC_rtds*.gz")):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    result = {"sha256": digest, "bytes": path.stat().st_size}
    results[path.name] = result
    if digest in seen:
        result["duplicate_of"] = seen[digest]
        continue
    seen[digest] = path.name
    counts, seconds, delays = Counter(), defaultdict(set), defaultdict(list)
    first, last = math.inf, -math.inf
    prior = -math.inf
    twap = {}
    complete_twap = {}
    with gzip.open(path, "rb") as stream:
        for line in stream:
            counts["lines"] += 1
            try:
                frame = json.loads(line)
                recv = float(frame["recv_ts"])
                first, last = min(first, recv), max(last, recv)
                counts["reception_regressions"] += recv < prior
                prior = recv
                inner = frame.get("raw")
                if not inner:
                    counts["lifecycle_or_empty"] += 1
                    continue
                message = json.loads(inner)
                payload = message.get("payload")
                if not isinstance(payload, dict) or payload.get("symbol") != "btc/usd":
                    counts["other_frames"] += 1
                    continue
                if isinstance(payload.get("data"), list):
                    counts["batch_history_frames"] += 1
                    if message.get("topic") == "crypto_prices_twap_sixty":
                        for item in payload["data"]:
                            sample_time = int(item["timestamp"])
                            if sample_time <= recv*1000:
                                sample = int(item["full_accuracy_value"]), recv
                                complete_twap.setdefault(sample_time, sample)
                    continue
                topic = message["topic"]
                source = int(payload["timestamp"])
                if topic == "crypto_prices_twap_sixty":
                    sample = int(payload["full_accuracy_value"]), recv
                    twap.setdefault(source, sample)
                    complete_twap.setdefault(source, sample)
                counts[topic] += 1
                seconds[topic].add(source // 1000)
                delays[topic].append(recv * 1000 - source)
            except (ValueError, TypeError, KeyError, OverflowError):
                counts["decode_errors"] += 1
    windows = []
    day = datetime.fromtimestamp(first, tz=timezone.utc).replace(hour=12,minute=0,second=0,microsecond=0)
    for index in range(12):
        start = int(day.timestamp()) + index * 300
        a, b = twap.get(start*1000), twap.get((start+300)*1000)
        c, d = complete_twap.get(start*1000), complete_twap.get((start+300)*1000)
        windows.append({"slug": f"btc-updown-5m-{start}", "exact_tick_direction":
                        ("up" if b[0]>=a[0] else "down") if a and b else None,
                        "direction_with_history": ("up" if d[0]>=c[0] else "down") if c and d else None,
                        "start_with_history_lag_seconds": round(c[1]-start,3) if c else None,
                        "end_with_history_lag_seconds": round(d[1]-start-300,3) if d else None,
                        "start_available_after_seconds": round(a[1]-start,3) if a else None,
                        "end_available_after_seconds": round(b[1]-start-300,3) if b else None})
    result.update(gzip_to_eof=True, exact_boundary_diagnostic=windows, counts=dict(counts), first_receive=utc(first), last_receive=utc(last),
                  topics={topic: {"distinct_source_seconds": len(seconds[topic]),
                                  "negative_delay": sum(x < 0 for x in values),
                                  "p50_delay_ms": quantile(values, .5),
                                  "p95_delay_ms": quantile(values, .95),
                                  "p99_delay_ms": quantile(values, .99),
                                  "max_source_gap_seconds": max(b-a for a,b in zip(
                                      sorted(seconds[topic]),sorted(seconds[topic])[1:]))}
                          for topic, values in delays.items()})
print(json.dumps({"files": results, "frames_excluding_duplicate_files": sum(
    f.get("counts", {}).get("lines", 0) for f in results.values())}, indent=2))
