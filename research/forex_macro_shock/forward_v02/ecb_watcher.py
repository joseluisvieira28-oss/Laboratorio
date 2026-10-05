"""Official ECB release identity/first-seen logic. No price or surprise logic."""
import re
import urllib.parse
from html.parser import HTMLParser
from datetime import date, datetime

import collector as c


class Document(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.meta = {}; self.h1 = []
        self.text = []; self.in_h1 = False; self.hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ['script', 'style']:
            self.hidden += 1
        if tag == 'h1': self.in_h1 = True
        if tag == 'a' and attrs.get('href'): self.links.append(attrs['href'])
        if tag == 'meta': self.meta[attrs.get('property', attrs.get('name', ''))] = attrs.get('content', '')

    def handle_endtag(self, tag):
        if tag in ['script', 'style']: self.hidden = max(0, self.hidden - 1)
        if tag == 'h1': self.in_h1 = False

    def handle_data(self, text):
        if not self.hidden:
            self.text.append(text)
            if self.in_h1: self.h1.append(text)


def allowed_release(url, target_day):
    u = urllib.parse.urlsplit(url)
    stamp = date.fromisoformat(target_day).strftime('%y%m%d')
    year = str(date.fromisoformat(target_day).year)
    return (u.scheme == 'https' and u.netloc == 'www.ecb.europa.eu'
            and not u.query and not u.fragment and not u.username
            and bool(re.fullmatch(r'/press/pr/date/' + year + r'/html/ecb\.mp' + stamp + r'~[a-zA-Z0-9]+\.en\.html', u.path)))


def discover(raw, target_day):
    doc = Document(); doc.feed(raw.decode('utf-8'))
    urls = []
    for href in doc.links:
        url = urllib.parse.urljoin(c.SOURCES['ecb_index'], href)
        if allowed_release(url, target_day) and url not in urls:
            urls.append(url)
    return urls


def publication(raw, url, target_day):
    if not allowed_release(url, target_day):
        raise ValueError('UNOFFICIAL_OR_WRONG_DATE_URL')
    doc = Document(); doc.feed(raw.decode('utf-8'))
    title = ' '.join(doc.h1).strip().lower()
    text = ' '.join(' '.join(doc.text).split())
    meta = doc.meta.get('article:published_time', doc.meta.get('date', ''))
    if 'monetary policy decisions' not in title:
        raise ValueError('WRONG_RELEASE_TITLE')
    day = date.fromisoformat(target_day)
    visible_date = day.strftime('%d %B %Y').lstrip('0')
    meta_date = meta[:10] == target_day
    if not meta_date and visible_date not in text:
        raise ValueError('RELEASE_DATE_UNPROVEN')
    lowered = text.lower()
    if 'governing council' not in lowered or not re.search(r'(interest rates?|deposit facility|refinancing operations)', lowered):
        raise ValueError('NO_SUBSTANTIVE_POLICY_DECISION')
    if any(x in lowered for x in ['release will be published', 'content coming soon', 'placeholder']):
        raise ValueError('PLACEHOLDER_RELEASE')
    return {'event_id': 'ECB-' + target_day, 'semantic_publication_detected': True,
            'official_url': url, 'content_sha256': c.digest(raw),
            'published_metadata': meta or None, 'actual_global_publication_ms': None}


def first_seen(store, identity):
    # First qualifying receipt is durable evidence; no mutable side state.
    for payload, in store.db.execute("SELECT payload FROM receipts WHERE json_extract(payload,'$.source')='ecb_release' ORDER BY seq"):
        import json
        row = json.loads(payload)
        if row.get('validation', {}).get('event_id') == identity:
            return row['received_ms']
    return None


def timing_interval(last_negative_ms, received_ms, rtt_ms):
    return (last_negative_ms is not None and 0 <= received_ms - last_negative_ms <= 2000
            and rtt_ms <= 1000)
