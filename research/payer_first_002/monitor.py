#!/usr/bin/env python3
"""Historical Aave V3 Base LiquidationCall monitor (read-only, offline demonstration).

Only consumes a known public explorer transcription. It is NOT a live node, an RPC
client, an independent raw receipt verifier, or an early-warning model.
"""
import argparse
from decimal import Decimal
import hashlib
import html
import json
from pathlib import Path

BASE_CHAIN_ID = 8453
AAVE_BASE_POOL = "0xa238dd80c259a72e81d7e4664a9801593f98d1c5"
LIQUIDATION_TOPIC = "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
USDC_BASE = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
WETH_BASE = "0x4200000000000000000000000000000000000006"


def _hex(value, length):
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != length + 2:
        raise ValueError("malformed hex field")
    try:
        bytes.fromhex(value[2:])
    except ValueError as err:
        raise ValueError("non-hex field") from err
    return value.lower()


def _address_from_topic(topic):
    t = _hex(topic, 64)
    if int(t[2:26], 16) != 0:
        raise ValueError("nonzero address padding")
    return "0x" + t[-40:]


def _address_from_word(word):
    return _address_from_topic("0x" + word)


def decode_liquidation(event):
    if event.get("chain_id") != BASE_CHAIN_ID:
        raise ValueError("unexpected chain")
    if event.get("transaction_status") != "success":
        raise ValueError("transaction failed or confirmation absent")
    if not isinstance(event.get("block_number"), int) or event["block_number"] <= 0:
        raise ValueError("invalid block number")
    _hex(event.get("transaction_hash"), 64)
    if _hex(event.get("address"), 40) != AAVE_BASE_POOL:
        raise ValueError("unexpected emitting contract")
    topics = event.get("topics")
    if not isinstance(topics, list) or len(topics) != 4:
        raise ValueError("expected four topics")
    if _hex(topics[0], 64) != LIQUIDATION_TOPIC:
        raise ValueError("unexpected event signature")
    collateral = _address_from_topic(topics[1])
    debt = _address_from_topic(topics[2])
    user = _address_from_topic(topics[3])
    if (collateral, debt) != (WETH_BASE, USDC_BASE):
        raise ValueError("unrecognized asset decimals")
    data = _hex(event.get("data"), 256)[2:]
    words = [data[i:i + 64] for i in range(0, 256, 64)]
    debt_raw = int(words[0], 16)
    col_raw = int(words[1], 16)
    liquidator = _address_from_word(words[2])
    flag = int(words[3], 16)
    if flag not in (0, 1) or debt_raw <= 0 or col_raw <= 0:
        raise ValueError("invalid liquidation numeric fields")
    amount_usdc = Decimal(debt_raw) / Decimal(10**6)
    amount_weth = Decimal(col_raw) / Decimal(10**18)
    event_id = f"8453:{event['transaction_hash'].lower()}:{event['log_index_display']}"
    return {
        "event_id": event_id, "event": "AAVE_V3_LIQUIDATION_CONFIRMED",
        "chain": "Base", "block_number": event["block_number"],
        "timestamp_utc": event["block_timestamp_utc"],
        "tx_hash": event["transaction_hash"], "borrower_address": user,
        "liquidator_address": liquidator,
        "debt_asset": "USDC", "collateral_asset": "WETH",
        "debt_repaid_usdc": str(amount_usdc),
        "collateral_liquidated_weth": str(amount_weth),
        "received_a_token": bool(flag),
        "explorer_url": event["provenance"]["source_url"],
        "provenance_grade": "EXPLORER_TRANSCRIBED_NOT_RPC_VERIFIED",
        "semantic_limit": "Observed liquidation, not a forecast or proof of liquidator PnL"
    }


def monitor(events, threshold_usdc=Decimal("40000")):
    if threshold_usdc < 0:
        raise ValueError("negative threshold")
    seen = set()
    results = []
    for e in events:
        d = decode_liquidation(e)
        if d["event_id"] in seen:
            continue
        seen.add(d["event_id"])
        if Decimal(d["debt_repaid_usdc"]) >= threshold_usdc:
            d["alert_rule"] = f"confirmed_liquidation_debt >= {threshold_usdc} USDC"
            results.append(d)
    return results


def render_html(results):
    body = []
    for r in results:
        debt = Decimal(r["debt_repaid_usdc"])
        col = Decimal(r["collateral_liquidated_weth"])
        body.append(
            '<article class="card"><div class="eyebrow">Evento histórico confirmado · Base / Aave V3</div>'
            f'<div class="metrics"><div><span>Dívida liquidada</span><strong>{debt:,.2f} USDC</strong></div>'
            f'<div><span>Colateral liquidado</span><strong>{col:,.4f} WETH</strong></div></div>'
            f'<p>Bloco {r["block_number"]:,} · {html.escape(r["timestamp_utc"])} UTC</p>'
            f'<p class="small">Regra: {html.escape(r["alert_rule"])} · Origem: transcrição de evento BaseScan</p>'
            f'<a href="{html.escape(r["explorer_url"])}">Consultar recibo no explorador</a>'
            '</article>'
        )
    if not body:
        body = ['<article class="card">Nenhum evento atravessou o limite configurado.</article>']
    return """<!doctype html><html lang="pt"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Treasury Risk Watch — prova offline</title><style>
body{font-family:system-ui,sans-serif;background:#101b28;color:#edf3f8;max-width:850px;margin:50px auto;padding:0 18px;line-height:1.6}
.card{background:#192c3d;border:1px solid #355166;border-radius:16px;padding:24px;margin:24px 0}
.eyebrow{font-size:.8rem;color:#c2d6e4;letter-spacing:1px;text-transform:uppercase}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:18px 0}
.metrics span{display:block;color:#9cb5c6;font-size:.84rem}.metrics strong{font-size:1.5rem}a{color:#9cddff}.small{font-size:.86rem;color:#b4c7d7}
.notice{background:#29313b;padding:15px;border-left:3px solid #f1be6c;border-radius:6px}
@media(max-width:550px){.metrics{grid-template-columns:1fr}}</style>
<h1>💎 Treasury Risk Watch</h1><p>Prova de conceito histórica: descodificação determinística de evento Aave V3 na rede Base.</p>
""" + "".join(body) + """<p class="notice"><strong>Limites:</strong> este exemplo não está ligado a uma RPC em tempo real,
reproduz uma transcrição de dados apresentados no BaseScan, não valida independentemente o recibo bruto e NÃO prevê liquidações futuras.
Não calcula lucros, não gere ativos, não monitora clientes nem fornece garantias de segurança.</p></html>"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixture", default="fixture_aave_base_liquidation.json")
    p.add_argument("--threshold", type=Decimal, default=Decimal("40000"))
    p.add_argument("--out", default="results.json")
    p.add_argument("--html", default="demo.html")
    a = p.parse_args()
    fixture = json.loads(Path(a.fixture).read_text(encoding="utf-8"))
    r = monitor([fixture], a.threshold)
    Path(a.out).write_text(json.dumps({"alerts":r,"source_fixture_sha256":hashlib.sha256(Path(a.fixture).read_bytes()).hexdigest()},indent=2,ensure_ascii=False),encoding="utf-8")
    Path(a.html).write_text(render_html(r),encoding="utf-8")
    print(json.dumps({"alerts":len(r),"source_fixture_sha256":hashlib.sha256(Path(a.fixture).read_bytes()).hexdigest()},indent=2))

if __name__ == "__main__":
    main()
