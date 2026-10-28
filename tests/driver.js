// Smoke/regression driver. tests/run.py appends this to a temporary copy of index.html and loads it in headless Chrome.
// window.__SMOKE = { mode: 'matrix' } drives every sheet type / paper / letters combination and reads the result back from the DOM;
// { mode: 'print', type, paper } only sets that state so Chrome can print the page to PDF (page count check).
(async () => {
  const S = window.__SMOKE;
  const $ = id => document.getElementById(id);
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const fire = (el, ...names) => names.forEach(n => el.dispatchEvent(new Event(n, { bubbles: true })));
  const hash = s => { let h = 5381; for (let i = 0; i < s.length; i++) h = ((h * 33) ^ s.charCodeAt(i)) >>> 0; return h.toString(16); };

  // Always use the committed font, so results never depend on fonts in a local fonts/ folder.
  const fontSelect = $('font-select');
  const hasFont = [...fontSelect.options].some(o => o.value === 'PlaywriteCA');
  fontSelect.value = 'PlaywriteCA';
  fire(fontSelect, 'change');
  await sleep(1000);

  // type last: its change handler re-fits the letter size and renders with everything set before
  async function setState({ type, paper, letters, only = '', lines = '1' }) {
    $('orientation-select').value = paper;
    $('case-select').value = letters;
    $('only-input').value = only;
    $('lines-input').value = lines;
    $('type-select').value = type;
    fire($('type-select'), 'change');
    await sleep(900);
  }

  if (S.mode === 'print') {
    await setState({ type: S.type, paper: S.paper, letters: 'lower' }); // adds nothing to the DOM: it would print as an extra page
    return;
  }

  const sheetsOf = () => [...document.querySelectorAll('.sheet')];
  const leads = () => [...document.querySelectorAll('.lead-letter')].map(e => e.textContent);
  function snapshot(paper) {
    const wmm = paper === 'landscape' ? 297 : 210;
    const data = [], layout = [];
    sheetsOf().forEach(s => {
      const svg = s.querySelector('svg');
      const r = s.getBoundingClientRect(), sv = svg.getBoundingClientRect(), f = s.querySelector('.sheet-footer').getBoundingClientRect();
      const k = wmm / r.width; // screen preview is scaled; use the sheet width as the mm reference
      data.push({
        title: s.querySelector('h2').textContent,
        rows: s.querySelectorAll('.lead-letter').length,
        trace: s.querySelectorAll('.trace-letter').length,
        svg: hash(svg.outerHTML)
      });
      layout.push({
        sheetH: +(r.height * k).toFixed(1),
        svgBottom: +((sv.bottom - r.top) * k).toFixed(1),
        footerTop: +((f.top - r.top) * k).toFixed(1)
      });
    });
    return { data, layout };
  }

  // 1. matrix: every sheet type x paper x letters, whole alphabet, auto-fitted size
  const types = [...$('type-select').options].map(o => o.value);
  const cases = {}, layouts = {};
  for (const paper of ['portrait', 'landscape']) {
    for (const letters of ['lower', 'upper', 'both']) {
      for (const type of types) {
        await setState({ type, paper, letters });
        const key = [type, paper, letters].join('/');
        const snap = snapshot(paper);
        cases[key] = {
          size: parseFloat($('size-range').value),
          min: parseFloat($('size-range').min),
          max: parseFloat($('size-range').max),
          sheets: snap.data
        };
        layouts[key] = snap.layout;
      }
    }
  }

  // 2. feature checks on the letter options, driven like a user (input events)
  const checks = [];
  const check = (name, ok, detail) => checks.push({ name, ok: !!ok, detail: ok ? '' : String(detail) });
  const typeIn = async (id, value) => { $(id).value = value; fire($(id), 'input', 'change'); await sleep(500); };
  const base = { type: 'copperplate', paper: 'portrait', letters: 'lower' };
  const title = () => sheetsOf()[0].querySelector('h2').textContent;

  await setState(base);
  check('page lists the committed font', hasFont, 'PlaywriteCA missing in #font-select');
  await typeIn('only-input', 'aeoc');
  check('only "aeoc": 4 rows', leads().join(' ') === 'a e o c', leads().join(' '));
  check('only "aeoc": sheet title', title() === 'Lowercase: a e o c', title());
  await typeIn('only-input', 'BAb');
  check('only "BAb": case ignored, duplicates dropped, typed order kept', leads().join(' ') === 'b a', leads().join(' '));
  await typeIn('only-input', '123 !');
  check('only "123 !": no valid letter, whole alphabet', leads().length === 26, leads().length);
  await typeIn('only-input', 'ae');
  await typeIn('case-select', 'upper');
  check('only "ae" + uppercase', leads().join(' ') === 'A E' && title() === 'Uppercase: A E', leads().join(' ') + ' / ' + title());
  await typeIn('case-select', 'both');
  check('only "ae" + pairs', leads().join(' ') === 'Aa Ee' && title() === 'Letter pairs: Aa Ee', leads().join(' ') + ' / ' + title());
  await typeIn('case-select', 'lower');
  await typeIn('lines-input', '3');
  check('3 lines per letter, grouped', leads().join(' ') === 'a a a e e e', leads().join(' '));
  await typeIn('only-input', 'a');
  await typeIn('lines-input', '99');
  check('lines per letter above 10 is clamped to 10', leads().length === 10, leads().length);
  await typeIn('lines-input', '0');
  check('lines per letter 0 falls back to 1', leads().length === 1, leads().length);
  await typeIn('only-input', '');
  await typeIn('lines-input', '1');

  // 3. matrix invariants (not part of the golden snapshot)
  Object.keys(cases).forEach(key => {
    const c = cases[key], isLand = key.includes('/landscape/');
    const sheetH = isLand ? 210 : 297;
    check(key + ': size inside slider range', c.size >= c.min && c.size <= c.max, c.size + ' not in ' + c.min + '..' + c.max);
    layouts[key].forEach((l, i) => {
      check(key + ' sheet ' + (i + 1) + ': guides end above the bottom padding', l.svgBottom <= sheetH - 16 + 0.6, 'svg bottom ' + l.svgBottom + ' mm, limit ' + (sheetH - 16));
      check(key + ' sheet ' + (i + 1) + ': footer below the guides', l.footerTop >= l.svgBottom, 'footer top ' + l.footerTop + ' < svg bottom ' + l.svgBottom);
    });
  });

  // 4. privacy: nothing requested from the network before a Google font name is typed
  const external = performance.getEntriesByType('resource').map(e => e.name).filter(n => /^https?:/.test(n));
  check('no external request before a font name is typed', external.length === 0, external.join(', '));
  check('#font-link has no href by default', !$('font-link').hasAttribute('href'), $('font-link').getAttribute('href'));
  check('no script errors', !(window.__errs || []).length, (window.__errs || []).join(' | '));

  const out = { cases, layouts, checks };
  document.body.insertAdjacentHTML('beforeend', '<pre id="smoke-result">' + JSON.stringify(out) + '</pre>');
})();
