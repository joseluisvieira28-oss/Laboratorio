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

/*
 * Defense in depth. Candidate adapter modules are NEVER required/imported by this
 * extractor. The network block stays installed so a future regression fails closed.
 * SOURCE_ONLY_NETWORK_BLOCK
 */
function blockedNetwork() {
  throw new Error('SOURCE_ONLY_NETWORK_BLOCK: runtime network access forbidden');
}
global.fetch = blockedNetwork;
http.request = blockedNetwork;
http.get = blockedNetwork;
https.request = blockedNetwork;
https.get = blockedNetwork;

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

const typescriptPath = path.join(root, 'node_modules', 'typescript');
if (!fs.existsSync(typescriptPath)) throw new Error(`typescript dependency missing: ${typescriptPath}`);
const ts = require(typescriptPath);

function loadPeriodToSeconds() {
  const p = path.join(root, 'utils', 'time.ts');
  if (!fs.existsSync(p)) throw new Error(`missing source time authority ${p}`);
  const raw = fs.readFileSync(p, 'utf8');
  const keys = ['year', 'month', 'week', 'day', 'hour', 'minute'];
  const out = {};
  for (const key of keys) {
    const m = raw.match(new RegExp(`\\b${key}\\s*:\\s*([0-9_]+)\\b`));
    if (!m) throw new Error(`periodToSeconds.${key} not statically recoverable`);
    out[key] = Number(m[1].replace(/_/g, ''));
    if (!Number.isFinite(out[key]) || out[key] <= 0) throw new Error(`bad periodToSeconds.${key}`);
  }
  return {values: out, sha256: sha256(Buffer.from(raw, 'utf8'))};
}
const timeAuthority = loadPeriodToSeconds();
const PERIOD = Object.freeze(timeAuthority.values);
const PERIOD_MARKER = Object.freeze({__periodToSeconds: true});
const UNSUPPORTED = Symbol('UNSUPPORTED');

function isUnsupported(v) {
  return v === UNSUPPORTED;
}
function nodeTextNumber(node, sourceFile) {
  const raw = node.getText(sourceFile).replace(/_/g, '');
  const v = Number(raw);
  return Number.isFinite(v) ? v : UNSUPPORTED;
}
function propertyNameText(name, sourceFile) {
  if (!name) return null;
  if (ts.isIdentifier(name) || ts.isPrivateIdentifier(name)) return name.text;
  if (ts.isStringLiteralLike(name) || ts.isNumericLiteral(name)) return String(name.text);
  if (ts.isComputedPropertyName(name)) {
    const v = evalExpr(name.expression, new Map(), sourceFile, new Set());
    return (typeof v === 'string' || typeof v === 'number') ? String(v) : null;
  }
  return null;
}
function unwrap(node) {
  let n = node;
  while (n && (
    ts.isParenthesizedExpression(n) ||
    ts.isAsExpression(n) ||
    ts.isTypeAssertionExpression(n) ||
    ts.isNonNullExpression(n)
  )) n = n.expression;
  return n;
}
function parseStaticDate(s, format) {
  if (typeof s !== 'string') return UNSUPPORTED;
  if (!format) {
    let text = s;
    if (/^\d{4}-\d{2}-\d{2}T/.test(text) && !/[zZ]|[+-]\d\d:\d\d$/.test(text)) text += 'Z';
    const ms = Date.parse(text);
    return Number.isFinite(ms) ? Math.floor(ms / 1000) : UNSUPPORTED;
  }
  const f = String(format).toLowerCase();
  const val = String(s);
  const read = (k) => {
    const a = f.indexOf(k);
    const b = f.lastIndexOf(k);
    return a >= 0 && b >= a ? val.substring(a, b + 1) : '';
  };
  let y = read('y'), m = read('m'), d = read('d');
  if (y.length === 2) y = `20${y}`;
  if (m.length === 1) m = `0${m}`;
  if (d.length === 1) d = `0${d}`;
  if (!/^\d{4}$/.test(y) || !/^\d{2}$/.test(m) || !/^\d{2}$/.test(d)) return UNSUPPORTED;
  const ms = Date.parse(`${y}-${m}-${d}T00:00:00Z`);
  return Number.isFinite(ms) ? Math.floor(ms / 1000) : UNSUPPORTED;
}

function collectBindings(sourceFile) {
  const bindings = new Map();
  let defaultExport = null;
  for (const stmt of sourceFile.statements) {
    if (ts.isVariableStatement(stmt)) {
      for (const decl of stmt.declarationList.declarations) {
        if (ts.isIdentifier(decl.name) && decl.initializer) {
          bindings.set(decl.name.text, {kind: 'expr', node: decl.initializer});
        }
      }
    } else if (ts.isFunctionDeclaration(stmt) && stmt.name) {
      bindings.set(stmt.name.text, {kind: 'function', node: stmt});
    } else if (ts.isExportAssignment(stmt) && !stmt.isExportEquals) {
      defaultExport = stmt.expression;
    }
  }
  return {bindings, defaultExport};
}

function binaryOp(kind, a, b) {
  switch (kind) {
    case ts.SyntaxKind.PlusToken: return (typeof a === 'number' && typeof b === 'number') || (typeof a === 'string' && typeof b === 'string') ? a + b : UNSUPPORTED;
    case ts.SyntaxKind.MinusToken: return typeof a === 'number' && typeof b === 'number' ? a - b : UNSUPPORTED;
    case ts.SyntaxKind.AsteriskToken: return typeof a === 'number' && typeof b === 'number' ? a * b : UNSUPPORTED;
    case ts.SyntaxKind.SlashToken: return typeof a === 'number' && typeof b === 'number' && b !== 0 ? a / b : UNSUPPORTED;
    case ts.SyntaxKind.PercentToken: return typeof a === 'number' && typeof b === 'number' && b !== 0 ? a % b : UNSUPPORTED;
    case ts.SyntaxKind.AsteriskAsteriskToken: return typeof a === 'number' && typeof b === 'number' ? a ** b : UNSUPPORTED;
    default: return UNSUPPORTED;
  }
}

function evalFunction(fnNode, args, localEnv, sourceFile, stack) {
  const env = new Map(localEnv);
  const params = fnNode.parameters || [];
  for (let i = 0; i < params.length; i++) {
    const p = params[i];
    if (!ts.isIdentifier(p.name)) return UNSUPPORTED;
    env.set(p.name.text, {kind: 'value', value: i < args.length ? args[i] : undefined});
  }
  const body = fnNode.body;
  if (!body) return UNSUPPORTED;
  if (!ts.isBlock(body)) return evalExpr(body, env, sourceFile, stack);

  for (const stmt of body.statements) {
    if (ts.isVariableStatement(stmt)) {
      for (const decl of stmt.declarationList.declarations) {
        if (!ts.isIdentifier(decl.name) || !decl.initializer) return UNSUPPORTED;
        env.set(decl.name.text, {kind: 'expr', node: decl.initializer});
      }
      continue;
    }
    if (ts.isReturnStatement(stmt) && stmt.expression) {
      return evalExpr(stmt.expression, env, sourceFile, stack);
    }
    if (!ts.isEmptyStatement(stmt)) return UNSUPPORTED;
  }
  return UNSUPPORTED;
}

function evalExpr(inputNode, localEnv, sourceFile, stack) {
  let node = unwrap(inputNode);
  if (!node) return UNSUPPORTED;

  if (ts.isNumericLiteral(node)) return nodeTextNumber(node, sourceFile);
  if (ts.isStringLiteralLike(node)) return node.text;
  if (node.kind === ts.SyntaxKind.TrueKeyword) return true;
  if (node.kind === ts.SyntaxKind.FalseKeyword) return false;
  if (node.kind === ts.SyntaxKind.NullKeyword) return null;

  if (ts.isTemplateExpression(node)) {
    let out = node.head.text;
    for (const span of node.templateSpans) {
      const v = evalExpr(span.expression, localEnv, sourceFile, stack);
      if (!['string', 'number', 'boolean'].includes(typeof v)) return UNSUPPORTED;
      out += String(v) + span.literal.text;
    }
    return out;
  }
  if (ts.isNoSubstitutionTemplateLiteral(node)) return node.text;

  if (ts.isIdentifier(node)) {
    if (node.text === 'periodToSeconds') return PERIOD_MARKER;
    const entry = localEnv.get(node.text) || currentBindings.get(node.text);
    if (!entry) return UNSUPPORTED;
    if (entry.kind === 'value') return entry.value;
    if (entry.kind === 'function') return {__staticFunction: true, node: entry.node, env: localEnv};
    if (entry.kind === 'expr') {
      const key = entry;
      if (stack.has(key)) return UNSUPPORTED;
      stack.add(key);
      const v = evalExpr(entry.node, localEnv, sourceFile, stack);
      stack.delete(key);
      return v;
    }
    return UNSUPPORTED;
  }

  if (ts.isPropertyAccessExpression(node)) {
    const obj = evalExpr(node.expression, localEnv, sourceFile, stack);
    if (obj === PERIOD_MARKER) return Object.prototype.hasOwnProperty.call(PERIOD, node.name.text) ? PERIOD[node.name.text] : {__periodMethod: node.name.text};
    if (obj && typeof obj === 'object' && !Array.isArray(obj) && Object.prototype.hasOwnProperty.call(obj, node.name.text)) return obj[node.name.text];
    return UNSUPPORTED;
  }

  if (ts.isElementAccessExpression(node)) {
    const obj = evalExpr(node.expression, localEnv, sourceFile, stack);
    const key = evalExpr(node.argumentExpression, localEnv, sourceFile, stack);
    if ((Array.isArray(obj) || (obj && typeof obj === 'object')) && (typeof key === 'string' || typeof key === 'number')) {
      return Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : UNSUPPORTED;
    }
    return UNSUPPORTED;
  }

  if (ts.isPrefixUnaryExpression(node)) {
    const v = evalExpr(node.operand, localEnv, sourceFile, stack);
    if (typeof v !== 'number') return UNSUPPORTED;
    if (node.operator === ts.SyntaxKind.MinusToken) return -v;
    if (node.operator === ts.SyntaxKind.PlusToken) return +v;
    return UNSUPPORTED;
  }

  if (ts.isBinaryExpression(node)) {
    const a = evalExpr(node.left, localEnv, sourceFile, stack);
    const b = evalExpr(node.right, localEnv, sourceFile, stack);
    if (isUnsupported(a) || isUnsupported(b)) return UNSUPPORTED;
    return binaryOp(node.operatorToken.kind, a, b);
  }

  if (ts.isConditionalExpression(node)) {
    const cond = evalExpr(node.condition, localEnv, sourceFile, stack);
    if (typeof cond !== 'boolean') return UNSUPPORTED;
    return evalExpr(cond ? node.whenTrue : node.whenFalse, localEnv, sourceFile, stack);
  }

  if (ts.isArrayLiteralExpression(node)) {
    const out = [];
    for (const el of node.elements) {
      if (ts.isSpreadElement(el)) {
        const v = evalExpr(el.expression, localEnv, sourceFile, stack);
        if (!Array.isArray(v)) return UNSUPPORTED;
        out.push(...v);
      } else {
        out.push(evalExpr(el, localEnv, sourceFile, stack));
      }
    }
    return out;
  }

  if (ts.isObjectLiteralExpression(node)) {
    const out = {};
    for (const prop of node.properties) {
      if (ts.isPropertyAssignment(prop)) {
        const key = propertyNameText(prop.name, sourceFile);
        if (key === null) return UNSUPPORTED;
        out[key] = evalExpr(prop.initializer, localEnv, sourceFile, stack);
      } else if (ts.isShorthandPropertyAssignment(prop)) {
        out[prop.name.text] = evalExpr(prop.name, localEnv, sourceFile, stack);
      } else if (ts.isSpreadAssignment(prop)) {
        const v = evalExpr(prop.expression, localEnv, sourceFile, stack);
        if (!v || typeof v !== 'object' || Array.isArray(v) || isUnsupported(v)) return UNSUPPORTED;
        Object.assign(out, v);
      } else if (ts.isMethodDeclaration(prop)) {
        const key = propertyNameText(prop.name, sourceFile);
        if (key === null) return UNSUPPORTED;
        out[key] = UNSUPPORTED;
      } else {
        return UNSUPPORTED;
      }
    }
    return out;
  }

  if (ts.isArrowFunction(node) || ts.isFunctionExpression(node)) {
    return {__staticFunction: true, node, env: localEnv};
  }

  if (ts.isCallExpression(node)) {
    const args = node.arguments.map(a => evalExpr(a, localEnv, sourceFile, stack));
    if (args.some(isUnsupported)) return UNSUPPORTED;

    if (ts.isIdentifier(node.expression)) {
      const name = node.expression.text;
      if (name === 'manualCliff') {
        if (args.length < 2 || !args.slice(0, 2).every(Number.isFinite)) return UNSUPPORTED;
        return {type: 'cliff', start: args[0], amount: args[1]};
      }
      if (name === 'manualStep') {
        if (args.length < 4 || !args.slice(0, 4).every(Number.isFinite)) return UNSUPPORTED;
        return {type: 'step', start: args[0], stepDuration: args[1], steps: args[2], amount: args[3]};
      }
      if (name === 'readableToSeconds') return parseStaticDate(args[0]);
      if (name === 'stringToTimestamp') return parseStaticDate(args[0], args[1]);
      if (name === 'normalizeTime') {
        if (typeof args[0] === 'number') return args[0];
        return parseStaticDate(args[0], args[1]);
      }
      if (name === 'Number') {
        const v = Number(args[0]);
        return Number.isFinite(v) ? v : UNSUPPORTED;
      }
      const fn = evalExpr(node.expression, localEnv, sourceFile, stack);
      if (fn && fn.__staticFunction) return evalFunction(fn.node, args, fn.env || localEnv, sourceFile, stack);
      return UNSUPPORTED;
    }

    if (ts.isPropertyAccessExpression(node.expression)) {
      const owner = evalExpr(node.expression.expression, localEnv, sourceFile, stack);
      const method = node.expression.name.text;
      if (owner === PERIOD_MARKER && ['months', 'weeks', 'years', 'days'].includes(method)) {
        if (args.length !== 1 || !Number.isFinite(args[0])) return UNSUPPORTED;
        const unit = method.slice(0, -1);
        return PERIOD[unit] * args[0];
      }
      if (ts.isIdentifier(node.expression.expression) && node.expression.expression.text === 'Math') {
        const x = args[0];
        if (!Number.isFinite(x)) return UNSUPPORTED;
        if (method === 'floor') return Math.floor(x);
        if (method === 'ceil') return Math.ceil(x);
        if (method === 'round') return Math.round(x);
        if (method === 'trunc') return Math.trunc(x);
        return UNSUPPORTED;
      }
      if (Array.isArray(owner) && method === 'map' && args.length === 1 && args[0] && args[0].__staticFunction) {
        return owner.map((v, i) => evalFunction(args[0].node, [v, i, owner], args[0].env || localEnv, sourceFile, stack));
      }
      return UNSUPPORTED;
    }
    return UNSUPPORTED;
  }

  return UNSUPPORTED;
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
  return Array.isArray(raw) ? raw.filter(x => typeof x === 'string' && x).map(String) : [];
}
function tokenRaw(protocol) {
  return protocol && protocol.meta && protocol.meta.token !== undefined
    ? protocol.meta.token
    : protocol && protocol.token;
}

let currentBindings = new Map();
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
    static_ast_only: true,
    candidate_module_executed: false,
  };

  try {
    if (!fs.existsSync(full)) throw new Error(`missing frozen source file ${full}`);
    const raw = fs.readFileSync(full);
    status.adapter_sha256 = sha256(raw);
    const sourceText = raw.toString('utf8');
    const sourceFile = ts.createSourceFile(full, sourceText, ts.ScriptTarget.ES2020, true, ts.ScriptKind.TS);
    const parsed = collectBindings(sourceFile);
    currentBindings = parsed.bindings;
    if (!parsed.defaultExport) {
      status.disposition = 'TECHNICAL_FAILURE';
      status.reason = 'NO_DEFAULT_EXPORT';
      statuses.push(status);
      continue;
    }
    const protocol = evalExpr(parsed.defaultExport, new Map(), sourceFile, new Set());
    if (!protocol || typeof protocol !== 'object' || Array.isArray(protocol) || isUnsupported(protocol)) {
      status.disposition = 'TECHNICAL_FAILURE';
      status.reason = 'DEFAULT_EXPORT_NOT_STATIC_OBJECT';
      statuses.push(status);
      continue;
    }

    const tr = tokenRaw(protocol);
    status.token_raw = tr === undefined || tr === null || isUnsupported(tr) ? null : String(tr);
    status.sources = asSources(protocol);

    const rowsBefore = rawRows.length;
    for (const [section, rawValue] of Object.entries(protocol)) {
      if (['meta', 'token', 'sources', 'categories', 'documented', 'protocolId', 'protocolIds', 'notes'].includes(section)) continue;
      if (isUnsupported(rawValue) || (rawValue && rawValue.__staticFunction)) {
        status.dynamic_sections_skipped += 1;
        continue;
      }
      for (const r of flattenStatic(rawValue)) {
        if (isUnsupported(r) || (r && r.__staticFunction)) {
          status.dynamic_sections_skipped += 1;
          continue;
        }
        if (!r || typeof r !== 'object') continue;

        if (r.type === 'cliff') {
          status.static_cliff_objects_seen += 1;
          const tsValue = Number(r.start);
          const amount = Number(r.amount);
          if (!Number.isFinite(tsValue) || !Number.isFinite(amount)) {
            throw new Error(`BAD_STATIC_CLIFF:${section}`);
          }
          if (amount <= 0 || tsValue < minTs || tsValue > maxTs) continue;
          rawRows.push({
            snapshot,
            adapter_id: adapterId,
            file,
            adapter_sha256: status.adapter_sha256,
            token_raw: status.token_raw,
            timestamp: tsValue,
            scheduled_at_utc: new Date(tsValue * 1000).toISOString(),
            amount,
            section,
            kind: 'cliff',
            sources: status.sources,
            known_at_utc: new Date(cfg.knownAt * 1000).toISOString(),
            known_lead_days: (tsValue - cfg.knownAt) / 86400,
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
          if (amount <= 0 || steps <= 0 || duration <= 0 || !Number.isInteger(steps)) continue;
          for (let i = 0; i < steps; i++) {
            const tsValue = start + (i + 1) * duration;
            if (tsValue < minTs || tsValue > maxTs) continue;
            rawRows.push({
              snapshot,
              adapter_id: adapterId,
              file,
              adapter_sha256: status.adapter_sha256,
              token_raw: status.token_raw,
              timestamp: tsValue,
              scheduled_at_utc: new Date(tsValue * 1000).toISOString(),
              amount,
              section,
              kind: 'step',
              sources: status.sources,
              known_at_utc: new Date(cfg.knownAt * 1000).toISOString(),
              known_lead_days: (tsValue - cfg.knownAt) / 86400,
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
  source_evaluation_mode: 'TYPESCRIPT_AST_STATIC_ONLY_NO_ADAPTER_IMPORT',
  time_authority_sha256: timeAuthority.sha256,
  guards: {
    runtime_network_block_installed: true,
    candidate_modules_executed: false,
    static_ast_only: true,
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
