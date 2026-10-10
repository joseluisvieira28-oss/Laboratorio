from __future__ import annotations

import json
import pathlib
import urllib.error
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

def get_status(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-AMM-LVR-001/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(2048)
            return {"status": r.status, "content_type": r.headers.get("content-type"), "sample": body.decode("utf-8", "ignore")[:500]}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "content_type": e.headers.get("content-type"), "sample": e.read(1024).decode("utf-8", "ignore")[:500]}
    except Exception as e:
        return {"status": None, "error": type(e).__name__, "detail": str(e)[:500]}

def rpc(url: str, method: str, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
            return {"status": r.status, "result": data.get("result"), "error": data.get("error")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": e.read(1024).decode("utf-8", "ignore")[:500]}
    except Exception as e:
        return {"status": None, "error": type(e).__name__, "detail": str(e)[:500]}

probes = {
    "dune_query_page": get_status("https://dune.com/queries/4931834"),
    "dune_csv_no_key": get_status("https://api.dune.com/api/v1/query/4931834/results/csv?limit=1"),
    "binance_um_bookticker_2024_01_15": get_status("https://data.binance.vision/data/futures/um/daily/bookTicker/ETHUSDT/ETHUSDT-bookTicker-2024-01-15.zip"),
    "binance_um_bookticker_2025_03_08": get_status("https://data.binance.vision/data/futures/um/daily/bookTicker/ETHUSDT/ETHUSDT-bookTicker-2025-03-08.zip"),
    "binance_live_spot_bookticker": get_status("https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=ETHUSDT"),
}

eth_rpc = "https://ethereum-rpc.publicnode.com"
probes["ethereum_public_rpc_latest_block"] = rpc(eth_rpc, "eth_blockNumber", [])
probes["ethereum_public_rpc_searcher_code"] = rpc(
    eth_rpc, "eth_getCode",
    ["0x767c8bb1574bee5d4fe35e27e0003c89d43c5121", "latest"]
)

hist_ready = (
    probes["dune_csv_no_key"].get("status") == 200
    and probes["binance_um_bookticker_2025_03_08"].get("status") == 200
)
forward_ready = (
    probes["binance_live_spot_bookticker"].get("status") == 200
    and probes["ethereum_public_rpc_latest_block"].get("status") == 200
    and isinstance(probes["ethereum_public_rpc_latest_block"].get("result"), str)
)

receipt = {
    "lab_id": "AMM-LVR-CROSSVENUE-001",
    "phase": "SOURCE_ATTACK_V0.2",
    "economic_outcomes_opened": False,
    "pnl_computed": False,
    "historical_free_fullcost_ready": hist_ready,
    "historical_free_verdict": "HISTORICAL_FREE_SOURCE_PASS" if hist_ready else "HISTORICAL_FREE_SOURCE_BLOCKED",
    "forward_free_source_ready": forward_ready,
    "forward_free_verdict": "FORWARD_FREE_SOURCE_PASS" if forward_ready else "FORWARD_FREE_SOURCE_BLOCKED",
    "probes": probes,
    "notes": [
        "Dune public page availability is not equivalent to API result export availability.",
        "A 2024 Binance bookTicker object may exist while later historical continuity is absent.",
        "Forward source pass only proves no-auth current source access; it is not an economic edge result.",
        "Known searcher address is from published paper example and used only to test public chain observability."
    ],
}

(OUT / "source_attack_v0_2_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(receipt, indent=2, sort_keys=True))

# Fail only if BOTH routes are unusable. A historical block with a forward pass is a valid source-gate outcome.
if not hist_ready and not forward_ready:
    raise SystemExit(2)
