const path = require('path');
const fs = require('fs');

const root = process.argv[2];
const snapshot = process.argv[3];
const outPath = process.argv[4];
if (!root || !snapshot || !outPath) throw new Error('usage: node extractor.js ROOT SNAPSHOT OUT');

const configs = {
  '2023-03-17': {
    knownAt: 1679071439,
    minTs: 1679071439 + 30 * 86400,
    maxTs: Date.parse('2023-12-31T23:59:59Z') / 1000,
    repo: '0xnirmal/emissions-adapters',
    commit: '539e7cf40a4cecc73953f3ae2b196b3fa66ae34a',
    protocols: {
      'aptos.ts': '*',
      'dydx.ts': '*',
      'forta.ts': ['other', 'backers', 'core contributors', 'OpenZeppelin'],
      'pendle.ts': ['Investors', 'Advisors', 'Ecosystem fund', 'Team'],
      'liquity.ts': ['Team and advisors', 'Service providers', 'Investors', 'Endowment'],
    },
  },
  '2024-03-25': {
    knownAt: 1711404688,
    minTs: 1711404688 + 30 * 86400,
    maxTs: Date.parse('2024-12-31T23:59:59Z') / 1000,
    repo: 'danaugrs/emissions-adapters',
    commit: 'ad6bcfa961d6f0bd9cd5d589656b8f78daf7be7a',
    protocols: {
      'aptos.ts': '*',
      'dydx.ts': ['future employees & consultants', 'employees and consultants', 'investors'],
      'forta.ts': ['other', 'backers', 'core contributors', 'OpenZeppelin'],
      'perpetual-protocol.ts': ['Team and advisors'],
      'apecoin.ts': ['yuga labs', 'Jane Goodall Legacy Foundation', 'launch contributors', 'founders'],
      'gmt.ts': '*',
      'liquity.ts': ['Team and advisors', 'Service providers', 'Investors', 'Endowment'],
      'sui.ts': '*',
      'starknet.ts': '*',
      'arbitrum.ts': '*',
      'celestia.ts': '*',
      'pyth.ts': '*',
      'optimism.ts': ['Team', 'Investors'],
      'cyberConnect.ts': '*',
      'immutable.ts': ['Project Development', 'Private Sale'],
    },
  },
};

const cfg = configs[snapshot];
if (!cfg) throw new Error(`unknown snapshot ${snapshot}`);

const rows = [];
const sourceFiles = [];
for (const [file, allowed] of Object.entries(cfg.protocols)) {
  const full = path.join(root, 'protocols', file);
  if (!fs.existsSync(full)) throw new Error(`missing frozen source file ${full}`);
  const protocol = require(full).default;
  if (!protocol || !protocol.meta || !protocol.meta.token) throw new Error(`missing token metadata ${file}`);
  const token = String(protocol.meta.token);
  const sources = Array.isArray(protocol.meta.sources) ? protocol.meta.sources.map(String) : [];
  if (sources.length === 0) throw new Error(`no provenance URL ${file}`);
  sourceFiles.push({file, token, sources});

  const allowedSet = allowed === '*' ? null : new Set(allowed);
  for (const [section, rawValue] of Object.entries(protocol)) {
    if (['meta', 'categories', 'documented'].includes(section)) continue;
    if (allowedSet && !allowedSet.has(section)) continue;
    if (typeof rawValue === 'function') continue;
    const values = (Array.isArray(rawValue) ? rawValue.flat(Infinity) : [rawValue]);
    for (const r of values) {
      if (!r || typeof r !== 'object') continue;
      if (r.type === 'cliff') {
        const ts = Number(r.start);
        const amount = Number(r.amount);
        if (!Number.isFinite(ts) || !Number.isFinite(amount)) throw new Error(`bad cliff ${file}/${section}`);
        if (amount <= 0 || ts < cfg.minTs || ts > cfg.maxTs) continue;
        rows.push({token, timestamp: ts, amount, section, kind: 'cliff', file, sources});
      } else if (r.type === 'step') {
        const start = Number(r.start);
        const duration = Number(r.stepDuration);
        const steps = Number(r.steps);
        const amount = Number(r.amount);
        if (![start, duration, steps, amount].every(Number.isFinite)) throw new Error(`bad step ${file}/${section}`);
        if (amount <= 0 || steps <= 0 || duration <= 0) continue;
        for (let i = 0; i < steps; i++) {
          const ts = start + (i + 1) * duration;
          if (ts < cfg.minTs || ts > cfg.maxTs) continue;
          rows.push({token, timestamp: ts, amount, section, kind: 'step', file, sources});
        }
      }
    }
  }
}

// Aggregate same token/timestamp across allocations; preserve exact components/provenance.
const byKey = new Map();
for (const r of rows) {
  const key = `${r.token}|${r.timestamp}`;
  if (!byKey.has(key)) byKey.set(key, {
    token: r.token,
    timestamp: r.timestamp,
    amount: 0,
    component_count: 0,
    sections: new Set(),
    kinds: new Set(),
    source_files: new Set(),
    sources: new Set(),
  });
  const x = byKey.get(key);
  x.amount += r.amount;
  x.component_count += 1;
  x.sections.add(r.section);
  x.kinds.add(r.kind);
  x.source_files.add(r.file);
  for (const s of r.sources) x.sources.add(s);
}

const events = [...byKey.values()].map(x => ({
  token: x.token,
  timestamp: x.timestamp,
  scheduled_at_utc: new Date(x.timestamp * 1000).toISOString(),
  scheduled_unlock_tokens: x.amount,
  component_count: x.component_count,
  sections: [...x.sections].sort(),
  kinds: [...x.kinds].sort(),
  source_files: [...x.source_files].sort(),
  sources: [...x.sources].sort(),
  known_at_utc: new Date(cfg.knownAt * 1000).toISOString(),
  known_lead_days: (x.timestamp - cfg.knownAt) / 86400,
  source_repo: cfg.repo,
  source_commit: cfg.commit,
  pit_status: 'IMMUTABLE_PROVIDER_SNAPSHOT_STATIC_EXACT',
  outcome_data_accessed: false,
})).sort((a,b) => a.timestamp - b.timestamp || a.token.localeCompare(b.token));

for (const e of events) {
  if (e.timestamp < cfg.minTs || e.timestamp > cfg.maxTs) throw new Error('date quarantine breach');
  if (e.known_lead_days < 30) throw new Error('PIT lead breach');
  if (e.outcome_data_accessed !== false) throw new Error('outcome guard breach');
}

const receipt = {
  snapshot,
  source_repo: cfg.repo,
  source_commit: cfg.commit,
  known_at_utc: new Date(cfg.knownAt * 1000).toISOString(),
  event_count: events.length,
  distinct_tokens: [...new Set(events.map(x => x.token))].sort(),
  years: [...new Set(events.map(x => new Date(x.timestamp*1000).getUTCFullYear()))].sort(),
  source_files: sourceFiles,
  guards: {
    only_cliff_or_step: true,
    dynamic_functions_skipped: true,
    linear_schedules_skipped: true,
    future_post_2024_rows_serialized: false,
    market_data_accessed: false,
    price_data_accessed: false,
    returns_computed: false,
    pnl_computed: false,
  },
};
fs.writeFileSync(outPath, JSON.stringify({receipt, events}, null, 2) + '\n');
console.log(JSON.stringify(receipt, null, 2));
