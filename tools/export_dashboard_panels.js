#!/usr/bin/env node
/**
 * export_dashboard_panels.js — export the interactive dashboard's ACTUAL panel charts as JSON
 * fragments, so the report can embed the very same charts (not rebuilt look-alikes).
 *
 *   node tools/export_dashboard_panels.js          # writes analysis/figures/interactive/dash_<chartid>.json
 *   node tools/export_dashboard_panels.js --ci     # ALSO writes dash_<chartid>_ci.json (95% CIs switched on)
 *
 * How it works: the dashboard (analysis/figures/interactive_dashboard.html, built by
 * tools/final_report_html.py) keeps its chart code in an inline <script>. That script is executed
 * here in a headless node:vm sandbox with a stubbed DOM and a stubbed Plotly whose react()/newPlot()
 * calls are captured per chart-div id. Each captured {traces, layout, config} is written verbatim —
 * the same objects the browser hands to Plotly, with the dashboard's own default state (all filters
 * on, effort-connecting lines on, CI checkboxes off, panel dropdowns at their markup defaults).
 *
 * The report renderer (tools/report_to_html.py) consumes analysis/figures/interactive/manifest.json
 * and the dash_*.json fragments to place these charts inline.
 *
 * Exit status: 0 when every expected panel was captured; non-zero otherwise (with a per-panel report).
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.resolve(__dirname, '..');
const DASH = path.join(ROOT, 'analysis', 'figures', 'interactive_dashboard.html');
const OUT = path.join(ROOT, 'analysis', 'figures', 'interactive');
const MANIFEST = path.join(OUT, 'manifest.json');

// chart div id -> panel key as it appears in the dashboard's <h2> headings
const PANELS = [
  ['chart1a', '1a'], ['chart1b', '1b'], ['chart1c', '1c'], ['chart1d', '1d'], ['chart1e', '1e'],
  ['chart1f', '1f'], ['chart2', '2'], ['chart3', '3'], ['chart4', '4'], ['chart5', '5'],
];
// panels whose 95%-CI checkbox the dashboard exposes (chart1a..chart1e; checkbox ids are showci1a..showci1e)
const CI_PANELS = new Set(['chart1a', 'chart1b', 'chart1c', 'chart1d', 'chart1e']);
const CI_CHECKBOX_FOR = new Map([...CI_PANELS].map((id) => [id.replace('chart', 'showci'), id]));

// Dashboard markup defaults that the chart code reads back (mirrors interactive_dashboard.html):
//   #showlines is `checked`; #sortsel defaults to its first option; #selmet defaults to its first option.
const markupDefaults = {
  showlines: true,
  sortsel: 'tokens_desc',
  selmet: 'recall',
};

function extractAppScript(html) {
  const blocks = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)]
    .filter(m => !/\bsrc\s*=/.test(m[1]))
    .map(m => m[2]);
  const app = blocks.find(s => s.includes('const DATA') && s.includes('function drawView'));
  if (!app) throw new Error('could not find the dashboard app <script> (needs "const DATA" + "function drawView")');
  return app;
}

function panelTitles(html) {
  const byKey = {};
  for (const m of html.matchAll(/<h2>\s*([0-9]+[a-f]?)\s*·\s*([^<]+?)\s*<\/h2>/g)) byKey[m[1]] = m[2];
  return byKey;
}

/** Run the dashboard app headlessly; returns Map<chartId, {traces, layout, config}>. */
function capturePanels(appScript, { ci }) {
  const captured = new Map();
  const record = (div, traces, layout, config) => {
    const id = typeof div === 'string' ? div : (div && div.__id) || null;
    if (id) captured.set(id, { traces, layout, config });
  };

  const elements = new Map();
  const makeElement = (id) => {
    const el = {
      __id: id,
      checked: id === 'showlines' ? !!markupDefaults.showlines : false,
      value: markupDefaults[id] !== undefined ? markupDefaults[id] : '',
      options: [],
      textContent: '',
      style: {},
      dataset: {},
      classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
      on: () => el,
      off() {}, trigger() {},
      addEventListener() {}, removeEventListener() {},
      appendChild: (c) => c, removeChild: () => {}, insertBefore: (c) => c,
      setAttribute() {}, getAttribute: () => null, removeAttribute() {},
      querySelector: () => null, querySelectorAll: () => [],
      getBoundingClientRect: () => ({ top: 0, bottom: 1, left: 0, right: 0, width: 0, height: 0 }),
      focus() {}, blur() {}, click() {}, scrollIntoView() {},
      add(o) { el.options.push(o); },      // <select>.add(option)
      remove() {},
    };
    let html = '';
    Object.defineProperty(el, 'innerHTML', {           // selects are repopulated via innerHTML=''
      get: () => html,
      set: (v) => { html = v; el.options.length = 0; },
      configurable: true,
    });
    return el;
  };

  const getElementById = (id) => {
    if (!elements.has(id)) elements.set(id, makeElement(id));
    const el = elements.get(id);
    if (ci && CI_CHECKBOX_FOR.has(id)) el.checked = true;   // --ci pass: switch the 95% CI toggle on
    return el;
  };

  class IntersectionObserverStub {
    constructor() {}
    observe() {} unobserve() {} disconnect() {} takeRecords() { return []; }
  }

  const documentStub = {
    getElementById,
    querySelector: () => null,
    querySelectorAll: () => [],
    createElement: (t) => makeElement('created:' + t),
    createElementNS: (ns, t) => makeElement('created:' + t),
    addEventListener() {}, removeEventListener() {},
    body: makeElement('body'), head: makeElement('head'), documentElement: makeElement('html'),
  };
  const windowStub = {
    document: documentStub,
    innerWidth: 1400, innerHeight: 900,
    addEventListener() {}, removeEventListener() {},
    IntersectionObserver: IntersectionObserverStub,
  };
  windowStub.window = windowStub;
  windowStub.self = windowStub;

  const PlotlyStub = {
    react: (div, traces, layout, config) => record(div, traces, layout, config),
    newPlot: (div, traces, layout, config) => record(div, traces, layout, config),
    extend() {}, addTraces() {}, relayout() {}, restyle() {}, purge() {}, resize() {},
    Plots: {}, Icons: {}, Config: {},
  };

  const sandbox = {
    document: documentStub,
    window: windowStub,
    self: windowStub,
    Plotly: PlotlyStub,
    IntersectionObserver: IntersectionObserverStub,
    Option: function Option(text, value) { return { text, value }; },
    console,
    setTimeout: (fn) => { try { fn(); } catch (_) {} return 0; },
    clearTimeout() {}, requestAnimationFrame: (fn) => { try { fn(); } catch (_) {} return 0; },
  };

  const context = vm.createContext(sandbox);
  vm.runInContext(appScript, context, { filename: 'interactive_dashboard_app.js', timeout: 60000 });

  // The app draws every panel at load; redraw defensively so each capture is the final state.
  // (`const VIEWS` is not on the global object, so we call the exposed function declarations only.)
  try { vm.runInContext('typeof redrawAll === "function" && redrawAll();', context, { timeout: 60000 }); } catch (_) {}
  return captured;
}

function stringifyAsciiStable(value, indent) {
  // Match the existing manifest's Python `json.dumps(..., indent=1)` byte style: ensure-ASCII escapes.
  return JSON.stringify(value, null, indent)
    .replace(/[\u0080-\uffff]/g, (c) => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
}

function main() {
  const wantCi = process.argv.includes('--ci');
  const html = fs.readFileSync(DASH, 'utf8');
  const appScript = extractAppScript(html);
  const titles = panelTitles(html);

  const passes = [{ suffix: '', ci: false }];
  if (wantCi) passes.push({ suffix: '_ci', ci: true });

  fs.mkdirSync(OUT, { recursive: true });
  const manifest = fs.existsSync(MANIFEST) ? JSON.parse(fs.readFileSync(MANIFEST, 'utf8')) : {};
  const rows = [];
  const missing = [];

  for (const pass of passes) {
    const captured = capturePanels(appScript, { ci: pass.ci });
    for (const [chartId, key] of PANELS) {
      // a CI variant only means something where the panel HAS a CI toggle (chart1a..chart1e)
      if (pass.ci && !CI_PANELS.has(chartId)) continue;
      const frag = captured.get(chartId);
      const file = path.join(OUT, `dash_${chartId}${pass.suffix}.json`);
      const label = titles[key] ? `${key} · ${titles[key]}` : chartId;
      if (!frag) {
        if (!pass.suffix) missing.push(chartId);
        rows.push({ panel: chartId + pass.suffix, traces: '—', updatemenus: '—', named: '—', bytes: 0, status: 'MISSING' });
        continue;
      }
      const payload = { traces: frag.traces, layout: frag.layout, config: frag.config };
      const text = stringifyAsciiStable(payload, 1) + '\n';
      fs.writeFileSync(file, text);
      // re-read and re-parse so a serialization problem cannot pass silently
      JSON.parse(fs.readFileSync(file, 'utf8'));
      const named = Array.isArray(frag.traces) && frag.traces.some(t => t && t.name);
      const menus = frag.layout && frag.layout.updatemenus ? frag.layout.updatemenus.length : 0;
      rows.push({
        panel: chartId + pass.suffix,
        traces: Array.isArray(frag.traces) ? frag.traces.length : '?',
        updatemenus: menus,
        named: named ? 'yes' : 'no',
        bytes: Buffer.byteLength(text),
        status: 'ok',
      });
      manifest[`dash_${chartId}${pass.suffix}`] = {
        source: `interactive_dashboard.html panel ${label}${pass.ci ? ' (95% CIs on)' : ' (dashboard default state)'}; `
              + `exported by tools/export_dashboard_panels.js`,
        title: label + (pass.ci ? ' — 95% CIs on' : ''),
      };
    }
  }

  fs.writeFileSync(MANIFEST, stringifyAsciiStable(manifest, 1) + '\n');

  const pad = (s, n) => String(s).padEnd(n);
  console.log(pad('panel', 14) + pad('traces', 8) + pad('menus', 7) + pad('named', 7) + pad('bytes', 10) + 'status');
  console.log('-'.repeat(50));
  for (const r of rows) {
    console.log(pad(r.panel, 14) + pad(r.traces, 8) + pad(r.updatemenus, 7) + pad(r.named, 7) + pad(r.bytes, 10) + r.status);
  }
  console.log(`\nfragments written to ${path.relative(ROOT, OUT)}/ (${rows.filter(r => r.status === 'ok').length} files); manifest updated (${Object.keys(manifest).length} entries)`);

  if (missing.length) {
    console.error(`\nERROR: expected panels missing a capture: ${missing.join(', ')}`);
    process.exitCode = 1;
  }
}

main();
