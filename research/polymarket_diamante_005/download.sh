#!/usr/bin/env bash
set -euo pipefail
rev=92fb1141c220c54587ad0efbbf9963b442acd4e1
root="https://huggingface.co/datasets/mileswangs/polymarket-btc-updown-5m-orderbook-tick-data/resolve/$rev"
mkdir -p data
get() {
    curl -fSL --retry 2 --max-time 180 "$root/$1" -o "data/$2.tmp"
    mv "data/$2.tmp" "data/$2"
}
get markets.parquet markets.parquet
export root
export -f get
seq -w 8 21 | xargs -P 5 -I % bash -ec 'get onchain_fills/date=2026-08-%/part-0.parquet fills-%.parquet'
for source in l2 trades; do
    get "$source/date=2026-08-08/part-0.parquet" "$source-08.parquet"
done
for source in chainlink_streams chainlink_streams_twap60s; do
    get "$source/date=2026-08-08/BTCUSD.parquet" "$source-08.parquet"
done
