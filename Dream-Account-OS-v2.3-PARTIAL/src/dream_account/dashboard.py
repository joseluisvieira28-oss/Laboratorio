from __future__ import annotations

import html
from pathlib import Path

from .scanner import ScanResult


def render(result: ScanResult, path: str) -> None:
    rows = "".join(f"<tr><td>{html.escape(c.symbol)}</td><td>{c.score}</td><td>{c.tier}</td><td>{c.status}</td><td>{', '.join(c.rejection_reasons) or '—'}</td></tr>" for c in result.candidates[:10])
    health = html.escape(str(result.api_health or {}))
    document = f"""<!doctype html><html><head><meta charset='utf-8'><title>Dream Account OS</title><style>body{{font-family:system-ui;background:#090d18;color:#e7ecf5;max-width:1100px;margin:40px auto}}.card{{background:#121a2a;padding:20px;border-radius:14px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #273148;text-align:left}}.status{{color:#e7b75b}}code{{white-space:pre-wrap}}</style></head><body><h1>CHF 56 DREAM ACCOUNT — OS v2.2</h1><div class='card'><b>Scanner health:</b> <span class='status'>{result.status}</span><br><b>REST status:</b> {result.status}<br><b>WebSocket status:</b> NOT_VALIDATED<br><b>Last message:</b> —<br><b>Last snapshot:</b> {result.observed_at}<br><b>Data coverage:</b> {result.data_coverage_pct}%<br><b>Stale feeds:</b> {'YES' if result.status != 'PASS' else 'NO'}<br><b>Market regime:</b> {result.regime or 'UNAVAILABLE'}<br><b>Pairs scanned:</b> {result.pairs_scanned}<br><b>Fast pass:</b> {result.fast_pass}<br><b>Deep pass:</b> {result.deep_pass}</div><div class='card'><h2>MEXC API health</h2><code>{health}</code></div><div class='card'><h2>Account</h2>Balance: CHF 56<br>Normal risk: CHF 0.84–1.12<br>Exceptional maximum: CHF 1.68<br>Execution: DISABLED</div><div class='card'><h2>Paper validation</h2>Open: 0<br>Closed live-market: 0<br>Expectancy: INSUFFICIENT SAMPLE<br>Profit factor: INSUFFICIENT SAMPLE<br>Drawdown: 0%</div><div class='card'><h2>Top candidates</h2><table><tr><th>Symbol</th><th>Score</th><th>Tier</th><th>Status</th><th>Reason</th></tr>{rows}</table></div><div class='card'><h2>Errors</h2>{'<br>'.join(map(html.escape, result.errors)) or 'None'}</div></body></html>"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
