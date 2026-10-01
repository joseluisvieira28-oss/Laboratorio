"""Metadata-only retrieval receipt. Never requests a quote dataset or payments."""
import concurrent.futures
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TARGETS = {
    "optionsDX": "https://www.optionsdx.com/product/btc-option-chains/",
    "Cryptarbitrage": "https://drive.google.com/file/d/1g9p2Kq8op40y4ZFQQ9AJw8a9CaDThOY8/view",
    "BRC": "https://blockchain-research-center.com/blockchain-explorer/request-data/",
    "CoinAPI": "https://www.coinapi.io/learn/academy/tutorials/coinapi-usage-free-credits-and-quota-explained",
    "Laevitas": "https://apiv2.laevitas.ch/mcp/",
    "Tardis": "https://docs.tardis.dev/downloadable-csv-files/overview.md",
    "Tardis_billing": "https://docs.tardis.dev/faq/billing-and-subscriptions.md",
    "Volar": "https://volardata.com/",
    "crypto-data.io": "https://crypto-data.io/",
    "UWA": "https://research-repository.uwa.edu.au/en/datasets/deribits-options-data/",
    "CandleFeed": "https://candlefeed.ai/data/options/",
    "ByKaranteli": "https://bykaranteli.com/data",
    "official_Deribit": "https://docs.deribit.com/",
    "QuantLet": "https://api.github.com/repos/QuantLet/BitcoinOptions",
    "bottama": "https://api.github.com/repos/bottama/Deribit-Option-Data",
    "schepal": "https://api.github.com/repos/schepal/crypto_gamma_exposure",
}

def retrieve(item):
    route, url = item
    row = {"route": route, "url": url, "method": "GET_METADATA_ONLY"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-SourceMetadata/0.4"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read(4_000_001)
            if len(data) > 4_000_000:
                raise ValueError("Metadata response exceeds frozen 4MB cap")
            row.update(status=r.status, final_url=r.url, metadata_bytes=len(data),
                       metadata_sha256=hashlib.sha256(data).hexdigest(),
                       content_type=r.headers.get("Content-Type"))
            if url.endswith("/view"):
                row["exact_object_title_present"] = b"btc_option_data_toshare.parquet" in data
            if "api.github.com/repos/" in url:
                obj = json.loads(data)
                row.update(default_branch=obj.get("default_branch"), pushed_at=obj.get("pushed_at"))
    except Exception as exc:
        row.update(status=getattr(exc, "code", None), error=f"{type(exc).__name__}: {str(exc)[:200]}")
    return row

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(retrieve, TARGETS.items()))
    result = {"date_utc": datetime.now(timezone.utc).isoformat(), "market_payload_requested": False,
              "cash_spend_usd": 0, "account_created": False, "outcomes_opened": False,
              "rows": rows, "note": "HTTP failures are transport limits, not proof of source nonexistence. Public web-tool documentation evidence is recorded separately in the route matrix."}
    p = Path("receipts/btc_options_vrp_final_20261001/public_metadata_receipt.json")
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps([{k:v for k,v in row.items() if k in ("route", "status", "error", "exact_object_title_present")} for row in rows]))
