// Exercise the actual generated-page handler, including its clipboard call.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

for (const file of ['tools/sdlc_report_template.html', 'sdlc-report.html']) {
  test(`${file}: Copy this post includes hashtags and confirms success`, async () => {
    const page = fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
    const helper = page.slice(page.indexOf('const copy ='), page.indexOf('const HASHTAGS'));
    const handler = page.match(/^  btn\('Copy this post'.*$/m)[0];
    const writes = [], notices = [];
    let click;
    const url = 'https://example.org/report/';
    const post = `First paragraph.\n\nFinding: ${url}#c-explore\nTechnical report: ${url}REPORT.html`;
    vm.runInNewContext(helper + '\n' + handler, {
      navigator: {clipboard: {writeText: s => { writes.push(s); return Promise.resolve(); }}},
      toast: s => notices.push(s),
      window: {prompt: () => assert.fail('Unexpected manual-copy fallback')},
      btn: (label, fn) => { click = fn; },
      text: () => post,
      D: {page_url: url}, el: {id: 'c-explore'},
      shareLink: () => url + '#c-explore?model=selected',
      LI_HASHTAGS: ['CodeReview', 'DevTools', 'SoftwareEngineering'],
      tagText: tags => tags.map(s => '#' + s).join(' '),
    });
    await click();
    await Promise.resolve();
    assert.deepEqual(writes, [post.replace('#c-explore', '#c-explore?model=selected') + '\n\n#CodeReview #DevTools #SoftwareEngineering']);
    assert.deepEqual(notices, ['Post copied']);
  });
}

for (const mode of ['missing', 'rejected', 'throws']) {
  test(`clipboard ${mode}: offers selectable text without a browser prompt`, async () => {
    const page = fs.readFileSync(path.join(__dirname, '../tools/sdlc_report_template.html'), 'utf8');
    const helper = page.slice(page.indexOf('const copy ='), page.indexOf('const HASHTAGS'));
    const nodes = [], notices = [];
    const document = {
      activeElement: {focus() {}},
      body: {appendChild(n) { nodes.push(n); }},
      createElement(tag) {
        return {tag, style: {}, children: [], setAttribute() {},
          appendChild(n) { this.children.push(n); }, addEventListener() {},
          showModal() {}, focus() {}, select() { this.selected = true; },
          setSelectionRange(start, end) { this.range = [start, end]; }, remove() {}};
      },
    };
    const navigator = mode === 'missing' ? {} : {clipboard: {writeText() {
      if (mode === 'throws') throw new Error('Blocked');
      return Promise.reject(new Error('NotAllowedError'));
    }}};
    const context = {document, navigator, toast: s => notices.push(s),
      window: {prompt: () => assert.fail('Browser prompts may be blocked')}};
    await vm.runInNewContext(helper + '\ncopy("Line one\\n\\nLine two", "Post copied")', context);
    const area = nodes.flatMap(n => n.children).find(n => n.tag === 'textarea');
    assert.ok(area, 'Manual copy text is visible');
    assert.equal(area.value, 'Line one\n\nLine two');
    assert.ok(area.selected);
    assert.deepEqual(notices, [], 'Do not claim copying succeeded');
  });
}
