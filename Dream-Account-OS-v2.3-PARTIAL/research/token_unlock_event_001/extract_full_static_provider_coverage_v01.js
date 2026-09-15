const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const http = require('http');
const https = require('https');

const root = process.argv[2];
const snapshot = process.argv[3];
const freezePath = process.argv[4];
const outPath = process.argv[5];
if (!root || !snapshot || !freezePath || !outPath) {
  throw new Error('usage: node extractor.js ROOT SNAPSHOT FREEZE_JSON OUT');
}

const SNAP = {
  '2023-03-17': {
    knownAt: 1679071439,
    repo: '0xnirmal/emissions-adapters',
    commit: '539e7cf40a4cecc73953f3ae2b196b3fa66ae34a',
  },
  '2024-03-25': {
    knownAt: 1711404688,
    repo: 'danaugrs/emissions-adapters',
    commit: 'ad6bcfa961d6f0bd9cd5d589656b8f78daf7be7a',
  },
};
const cfg = SNAP[snapshot];
if (!cfg) throw new Error(`unknown snapshot ${snapshot}`);

const freeze = JSON.parse(fs.readFileSync(freezePath, 'utf8'));
if (freeze.lab_id !== 'TOKEN-UNLOCK-EVENT-001' || freeze.mve_id !== 'TUE-CLIFF-ADV30-001') {
  throw new Error('freeze identity mismatch');
}
if (freeze.status !== 'FROZEN_PRE_FULL_COVERAGE_QUALIFICATION') {
  throw new Error('freeze status mismatch');
}
if (freeze.guards.discovery_authorized_by_this_file !== false ||
    freeze.guards.year_2025_opened !== false ||
    freeze.guards.year_2026_opened !== false) {
  throw new Error('freeze guard mismatch');
}
const auth = freeze.coverage_authority.snapshots[snapshot];
if (!auth) throw new Error(`snapshot missing from freeze ${snapshot}`);
if (auth.source_repo !== cfg.repo || auth.source_commit !== cfg.commit) {
  throw new Error('snapshot source identity mismatch');
}
const candidates = auth.candidate_files;
if (!Array.isArray(candidates) || candidates.length !== auth.candidate_files_count) {
  throw new Error('frozen candidate universe malformed');
}
if (new Set(candidates).size !== candidates.length) throw new Error('duplicate frozen candidate file');

const minTs = cfg.knownAt + 30 * 86400;
const maxTs = Date.parse('2024-12-31T23:59:59Z') / 1000;

function blockedNetwork() {
  throw new Error('SOURCE_ONLY_NETWORK_BLOCK: adapter attempted runtime network access');
}
global.fetch = blockedNetwork;
http.request = blockedNetwork;
http.get = blockedNetwork;
https.request = blockedNetwork;
https.get = blockedNetwork;

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}
function flattenStatic(value) {
  if (Array.isArray(value)) return value.flat(Infinity);
  return [value];
}
function isPlaceholderToken(s) {
  const v = String(s || '').trim();
  if (!v) return true;
  if (v === '-' || /:-$/.test(v) || /undefined|null/i.test(v)) return true;
  return false;
}
function asSources(protocol) {
  const raw = protocol && protocol.meta && protocol.meta.sources !== undefined
    ? protocol.meta.sources
    : protocol && protocol.sources;
  return Array.isArray(raw) ? raw.map(String).filter(Boolean) : [];
}
function tokenRaw(protocol) {
  return protocol && protocol.meta && protocol.meta.token !== undefined
    ? protocol.meta.token
    : protocol && protocol.token;
}

const statuses = [];
const rawRows = [];

for (const file of candidates) {
  const full = path.join(root, 'protocols', file);
  const adapterId = file.replace(/\.ts$/i, '');
  const status = {
    snapshot,
    source_repo: cfg.repo,
    source_commit: cfg.commit,
    file,
    adapter_id: adapterId,
    disposition: null,
    reason: null,
    adapter_sha256: null,
    token_raw: null,
    sources: [],
    static_cliff_objects_seen: 0,
    static_step_objects_seen: 0,
    static_other_objects_seen: 0,
    dynamic_sections_skipped: 0,
    eligible_event_rows_emitted: 0,
  };

  try {
    if (!fs.existsSync(full)) throw new Error(`missing frozen source file ${full}`);
    const raw = fs.readFileSync(full);
    status.adapter_sha256 = sha256(raw);

    let loaded = require(full);
    const protocol = loaded && loaded.default !== undefined ? loaded.default : loaded;
    if (!protocol || typeof protocol !== 'object') {
      status.disposition = 'TECHNICAL_FAILURE';
      status.reason = 'MODULE_DID_NOT_EXPORT_OBJECT';
      statuses.push(status);
      continue;
    }

    const tr = tokenRaw(protocol);
    status.token_raw = tr === undefined || tr === null ? null : String(tr);
    status.sources = asSources(protocol);

    const rowsBefore = rawRows.length;
    for (const [section, rawValue] of Object.entries(protocol)) {
      if (['meta', 'token', 'sources', 'categories', 'documented'].includes(section)) continue;
      if (typeof rawValue === 'function') {
        status.dynamic_sections_skipped += 1;
        continue;
      }
      for (const r of flattenStatic(rawValue)) {
        if (!r || typeof r !== 'object') continue;

        if (r.type === 'cliff') {
          status.static_cliff_objects_seen += 1;
          const ts = Number(r.start);
          const amount = Number(r.amount);
          if (!Number.isFinite(ts) || !Number.isFinite(amount)) {
            throw new Error(`BAD_STATIC_CLIFF:${section}`);
          }
          if (amount <= 0 || ts < minTs || ts > maxTs) continue;
          rawRows.push({
            snapshot,
            adapter_id: adapterId,
            file,
            adapter_sha256: status.adapter_sha256,
            token_raw: status.token_raw,
            timestamp: ts,
            scheduled_at_utc: new Date(ts * 1000).toISOString(),
            amount,
            section,
            kind: 'cliff',
            sources: status.sources,
            known_at_utc: new Date(cfg.knownAt * 1000).toISOString(),
            known_lead_days: (ts - cfg.knownAt) / 86400,
            source_repo: cfg.repo,
            source_commit: cfg.commit,
          });
        } else if (r.type === 'step') {
          status.static_step_objects_seen += 1;
          const start = Number(r.start);
          const duration = Number(r.stepDuration);
          const steps = Number(r.steps);
          const amount = Number(r.amount);
          if (![start, duration, steps, amount].every(Number.isFinite)) {
            throw new Error(`BAD_STATIC_STEP:${section}`);
          }
          if (amount <= 0 || steps <= 0 || duration <= 0) continue;
          for (let i = 0; i < steps; i++) {
            const ts = start + (i + 1) * duration;
            if (ts < minTs || ts > maxTs) continue;
            rawRows.push({
              snapshot,
              adapter_id: adapterId,
              file,
              adapter_sha256: status.adapter_sha256,
              token_raw: status.token_raw,
              timestamp: ts,
              scheduled_at_utc: new Date(ts * 1000).toISOString(),
              amount,
              section,
              kind: 'step',
              sources: status.sources,
              known_at_utc: new Date(cfg.knownAt * 1000).toISOString(),
              known_lead_days: (ts - cfg.knownAt) / 86400,
              source_repo: cfg.repo,
              source_commit: cfg.commit,
            });
          }
        } else {
          status.static_other_objects_seen += 1;
        }
      }
    }
    status.eligible_event_rows_emitted = rawRows.length - rowsBefore;

    if (isPlaceholderToken(status.token_raw)) {
      status.disposition = 'IDENTITY_AMBIGUOUS';
      status.reason = 'TOKEN_METADATA_EMPTY_OR_PLACEHOLDER';
    } else if (status.sources.length === 0) {
      status.disposition = 'IDENTITY_AMBIGUOUS';
      status.reason = 'NO_PROVENANCE_URLS';
    } else if (status.eligible_event_rows_emitted > 0) {
      status.disposition = 'INCLUDED_RAW_IDENTITY_PENDING';
      status.reason = 'STATIC_EXACT_EVENTS_IN_WINDOW';
    } else if (status.static_cliff_objects_seen + status.static_step_objects_seen > 0) {
      status.disposition = 'NO_ELIGIBLE_STATIC_EVENT_IN_WINDOW';
      status.reason = 'STATIC_DISCRETE_OBJECTS_PRESENT_BUT_NO_EVENT_PASSED_DATE_AMOUNT_RULES';
    } else if (status.dynamic_sections_skipped > 0) {
      status.disposition = 'DYNAMIC_OR_CONTINUOUS_ONLY';
      status.reason = 'NO_MATERIALIZED_STATIC_CLIFF_OR_STEP_OBJECT';
    } else {
      status.disposition = 'NO_ELIGIBLE_STATIC_EVENT_IN_WINDOW';
      status.reason = 'STATIC_SCAN_PATTERN_DID_NOT_MATERIALIZE_AS_SCHEDULE_OBJECT';
    }
  } catch (err) {
    status.disposition = 'TECHNICAL_FAILURE';
    status.reason = String(err && err.message ? err.message : err);
  }
  statuses.push(status);
}

const allowedFiles = new Set(
  statuses.filter(x => x.disposition === 'INCLUDED_RAW_IDENTITY_PENDING').map(x => x.file)
);
const filtered = rawRows.filter(r => allowedFiles.has(r.file));

const byKey = new Map();
for (const r of filtered) {
  const key = `${r.adapter_id}|${r.token_raw}|${r.timestamp}`;
  if (!byKey.has(key)) byKey.set(key, {
    snapshot: r.snapshot,
    adapter_id: r.adapter_id,
    file: r.file,
    adapter_sha256: r.adapter_sha256,
    token_raw: r.token_raw,
    timestamp: r.timestamp,
    scheduled_at_utc: r.scheduled_at_utc,
    scheduled_unlock_tokens: 0,
    component_count: 0,
    sections: new Set(),
    kinds: new Set(),
    sources: new Set(),
    known_at_utc: r.known_at_utc,
    known_lead_days: r.known_lead_days,
    source_repo: r.source_repo,
    source_commit: r.source_commit,
    pit_status: 'IMMUTABLE_PROVIDER_SNAPSHOT_STATIC_EXACT_RAW_IDENTITY',
    outcome_data_accessed: false,
  });
  const x = byKey.get(key);
  x.scheduled_unlock_tokens += r.amount;
  x.component_count += 1;
  x.sections.add(r.section);
  x.kinds.add(r.kind);
  for (const s of r.sources) x.sources.add(s);
}
const events = [...byKey.values()].map(x => ({
  ...x,
  sections: [...x.sections].sort(),
  kinds: [...x.kinds].sort(),
  sources: [...x.sources].sort(),
})).sort((a,b) => a.timestamp - b.timestamp || a.adapter_id.localeCompare(b.adapter_id));

for (const e of events) {
  const y = new Date(e.timestamp * 1000).getUTCFullYear();
  if (!(y === 2023 || y === 2024)) throw new Error('DATE_QUARANTINE_BREACH');
  if (e.timestamp < minTs || e.timestamp > maxTs) throw new Error('DATE_BOUNDARY_BREACH');
  if (e.known_lead_days < 30) throw new Error('PIT_LEAD_BREACH');
  if (!(e.scheduled_unlock_tokens > 0 && Number.isFinite(e.scheduled_unlock_tokens))) throw new Error('AMOUNT_BREACH');
}

const dispositionCounts = {};
for (const s of statuses) dispositionCounts[s.disposition] = (dispositionCounts[s.disposition] || 0) + 1;
const receipt = {
  lab_id: 'TOKEN-UNLOCK-EVENT-001',
  mve_id: 'TUE-CLIFF-ADV30-001',
  mode: 'SOURCE_ONLY_FULL_STATIC_COVERAGE_QUALIFICATION_V01',
  snapshot,
  source_repo: cfg.repo,
  source_commit: cfg.commit,
  known_at_utc: new Date(cfg.knownAt * 1000).toISOString(),
  frozen_candidate_count: candidates.length,
  candidate_status_count: statuses.length,
  disposition_counts: dispositionCounts,
  raw_identity_event_count: events.length,
  raw_identity_adapter_count: new Set(events.map(x => x.adapter_id)).size,
  exact_timestamp_rows_only: true,
  identity_resolution_complete: false,
  binance_route_checked: false,
  guards: {
    runtime_network_block_installed: true,
    dynamic_functions_executed: false,
    market_data_accessed: false,
    price_data_accessed: false,
    returns_computed: false,
    pnl_computed: false,
    profit_factor_computed: false,
    year_2025_opened: false,
    year_2026_opened: false,
    live_trading: false,
    exchange_mutation: false,
  },
};
fs.writeFileSync(outPath, JSON.stringify({receipt, statuses, events}, null, 2) + '\n');
console.log(JSON.stringify(receipt, null, 2));
