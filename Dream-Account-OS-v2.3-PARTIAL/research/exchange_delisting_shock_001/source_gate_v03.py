import html, json, re
from datetime import datetime, timezone
from pathlib import Path
import source_gate_v02 as v2

OUT = Path(__file__).resolve().parent / 'source_evidence' / 'EDS_SOURCE_DATA_GATE_V03.json'
v2.OUT = OUT

_original_token_items = v2.token_items

ZERO_WIDTH = '\u200b\u200c\u200d\u2060\ufeff'

def normalize(s):
    s = html.unescape(s)
    s = s.translate({ord(c): None for c in ZERO_WIDTH})
    s = s.replace('\xa0', ' ')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def delist_ts(text):
    s = normalize(text)
    anchor = re.search(r'cease\s+trading\s+on\s+all(?:\s+spot)?\s+trading\s+pairs\b', s, re.I)
    if not anchor:
        return None
    tail = s[anchor.start():anchor.end()+900]
    m = re.search(r'(20\d{2})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}).{0,40}?\bUTC\b', tail, re.I)
    if not m:
        return None
    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), tzinfo=timezone.utc)

def evidence_text(text):
    s = normalize(text)
    anchor = re.search(r'cease\s+trading\s+on\s+all(?:\s+spot)?\s+trading\s+pairs\b', s, re.I)
    if not anchor:
        return None
    tail = s[anchor.start():anchor.end()+900]
    m = re.search(r'^(.*?(?:20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}).{0,40}?\bUTC\b)', tail, re.I)
    return m.group(1).strip() if m else None

def token_items(body):
    items = dict(_original_token_items(body))
    raw = html.unescape(body).translate({ord(c): None for c in ZERO_WIDTH}).replace('\xa0', ' ')
    txt = v2.textify(raw)

    # Robust line-level parse after zero-width normalization.
    for line in txt.splitlines():
        line = re.sub(r'[ \t]+', ' ', line).strip(' \t\r\n-•*')
        m = re.search(r'^(.{1,100}?)\s*\(([A-Z0-9]{2,15})\)\s*$', line)
        if m:
            name = m.group(1).strip(' -•*')
            if name:
                items.setdefault(m.group(2), name)

    # HTML-text fallback: capture visible text immediately before (SYMBOL).
    for m in re.finditer(r'>([^<>\n]{1,100}?)\s*\(([A-Z0-9]{2,15})\)\s*<', raw, re.I):
        name = re.sub(r'\s+', ' ', m.group(1)).strip(' -•*')
        if name:
            items.setdefault(m.group(2).upper(), name)

    # Plain-text fallback inside the full-token announcement body. Symbols are
    # still later required to match the exact trading-pair section.
    for m in re.finditer(r'(?:^|\n|•|\*)\s*([^\n()]{1,100}?)\s*\(([A-Z0-9]{2,15})\)', txt):
        name = re.sub(r'\s+', ' ', m.group(1)).strip(' -•*')
        if name:
            items.setdefault(m.group(2), name)

    return list(items.items())

v2.delist_ts = delist_ts
v2.evidence_text = evidence_text
v2.token_items = token_items


def main():
    rc = 0
    try:
        v2.main()
    except SystemExit as e:
        rc = int(e.code or 0)

    if OUT.exists():
        d = json.loads(OUT.read_text(encoding='utf-8'))
        d['source_remediation_version'] = 'V0.3'
        d['parser_remediation'] = {
            'zero_width_removed': True,
            'whitespace_canonicalized_for_all_pairs_timestamp': True,
            'token_name_symbol_html_and_plaintext_fallbacks': True,
            'scientific_thresholds_changed': False,
            'event_definition_changed': False,
            'market_price_values_opened': False
        }
        OUT.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    if rc:
        raise SystemExit(rc)

if __name__ == '__main__':
    main()
