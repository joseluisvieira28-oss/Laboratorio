from __future__ import annotations

import csv
import hashlib
import io
import json
import pathlib
import urllib.request
from collections import Counter

LAB_ID = "AMM-LVR-CROSSVENUE-001"
SOURCE_URL = (
    "https://raw.githubusercontent.com/tivas-g/"
    "Wu_Comparing_CEX_DEX_Execution/main/cexdex_data_sample_20230808.csv"
)
REQUIRED_COLUMNS = [
    "block_number","block_time","tx_hash","tx_index","from_addr","to_addr",
    "mev_bot_label","base_fees","priority_fees","cb_transfer","mev_value",
    "volume","token_bought_amount","token_sold_amount","token_bought_contract",
    "token_sold_contract","token_bought_symbol","token_sold_symbol","pair","multi_trade"
]
OUT = pathlib.Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

with urllib.request.urlopen(SOURCE_URL, timeout=45) as r:
    raw = r.read()

sha = hashlib.sha256(raw).hexdigest()
text = raw.decode("utf-8-sig")
reader = csv.DictReader(io.StringIO(text))
fields = reader.fieldnames or []
missing = [c for c in REQUIRED_COLUMNS if c not in fields]
rows = list(reader)

labels = Counter((row.get("mev_bot_label") or "").strip() for row in rows)
pairs = Counter((row.get("pair") or "").strip() for row in rows)

numeric_failures = 0
for row in rows:
    for c in ["base_fees","priority_fees","cb_transfer","mev_value","volume"]:
        v = (row.get(c) or "").strip()
        if not v:
            continue
        try:
            float(v)
        except ValueError:
            numeric_failures += 1

verdict = (
    "SOURCE_DATA_PASS"
    if rows and not missing and numeric_failures == 0
    else "SOURCE_DATA_FAIL"
)

receipt = {
    "lab_id": LAB_ID,
    "phase": "SOURCE_FEASIBILITY_ONLY",
    "verdict": verdict,
    "source_url": SOURCE_URL,
    "sha256": sha,
    "row_count": len(rows),
    "column_count": len(fields),
    "required_columns": REQUIRED_COLUMNS,
    "missing_columns": missing,
    "numeric_parse_failures": numeric_failures,
    "unique_tx_hashes": len({r.get("tx_hash") for r in rows if r.get("tx_hash")}),
    "label_count": len(labels),
    "top_labels": labels.most_common(10),
    "pair_count": len(pairs),
    "top_pairs": pairs.most_common(10),
    "economic_outcomes_opened": False,
    "cex_markouts_opened": False,
    "pnl_computed": False,
    "note": (
        "This gate validates only the public one-day sample transport/schema. "
        "It does not establish an executable edge."
    ),
}
(OUT / "source_gate_receipt.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
)
print(json.dumps(receipt, indent=2, sort_keys=True))
if verdict != "SOURCE_DATA_PASS":
    raise SystemExit(2)
