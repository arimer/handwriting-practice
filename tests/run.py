#!/usr/bin/env python3
"""Smoke / regression test for the practice-sheet page (see README, section "Tests").

Loads a temporary copy of index.html in headless Chrome, drives the controls with tests/driver.js and checks
  1. checks and invariants (letter options, size slider range, layout inside the page, no external requests, no script errors),
  2. print page counts per sheet type and paper (PDF),
  3. a golden snapshot (tests/golden.json): sheet counts, rows, slider size/max and a hash of every sheet's SVG.
Without tests/golden.json step 3 is skipped with a warning. Results are always written to tests/out/ (results.json and
a ready-to-commit golden.json) plus report.md; on GitHub the report is also shown as the job summary and the
workflow uploads tests/out/ as an artifact.
Needs only Python 3 and Chrome (set CHROME to use a specific binary).
"""
import html, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, 'tests')
OUT = os.path.join(TESTS, 'out')
GOLDEN = os.path.join(TESTS, 'golden.json')
TMP_PREFIX = '.smoke-tmp-'  # temp pages live next to index.html (relative font/script paths) and are git-ignored

# expected A4 pages for the whole lowercase alphabet at the default letter options
PAGES = {
    'portrait':  {'copperplate': 3, 'lines': 2, 'bands': 2, 'slantgrid': 3, 'dots': 2, 'squares': 2},
    'landscape': {'copperplate': 4, 'lines': 3, 'bands': 3, 'slantgrid': 4, 'dots': 3, 'squares': 3},
}

CAPTURE = ("window.__errs=[];window.addEventListener('error',e=>window.__errs.push('error: '+e.message));"
           "window.addEventListener('unhandledrejection',e=>window.__errs.push('rejection: '+(e.reason&&e.reason.message||e.reason)));"
           "var __ce=console.error;console.error=function(){window.__errs.push('console.error: '+[].join.call(arguments,' '));__ce.apply(console,arguments)};")

CI = bool(os.environ.get('CI'))


def find_chrome():
    cands = [os.environ.get('CHROME'),
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
             'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
    for c in cands:
        if c and (os.path.isfile(c) or shutil.which(c)):
            return c
    sys.exit('Chrome not found. Install Google Chrome or set CHROME=/path/to/chrome.')


CHROME = find_chrome()
FLAGS = ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--window-size=1400,1000']
if CI:
    FLAGS += ['--no-sandbox', '--disable-dev-shm-usage']


def page(name, cfg):
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    drv = open(os.path.join(TESTS, 'driver.js'), encoding='utf-8').read()
    path = os.path.join(ROOT, TMP_PREFIX + name + '.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('<script>window.__SMOKE=' + json.dumps(cfg) + ';' + CAPTURE + '</script>\n' + src + '\n<script>' + drv + '</script>\n')
    return path


def chrome(args, timeout):
    return subprocess.run([CHROME] + FLAGS + args, capture_output=True, timeout=timeout)


def run_matrix():
    path = page('matrix', {'mode': 'matrix'})
    try:
        r = chrome(['--virtual-time-budget=240000', '--dump-dom', 'file://' + path], 600)
    finally:
        os.remove(path)
    dom = r.stdout.decode('utf-8', 'replace')
    m = re.findall(r'<pre id="smoke-result">(\{.*?\})</pre>', dom, re.S)
    if not m:
        sys.exit('The driver produced no result (page did not finish?).\n' + r.stderr.decode('utf-8', 'replace')[-2000:])
    return json.loads(html.unescape(m[-1]))


def pdf_pages(type_, paper):
    path = page('print', {'mode': 'print', 'type': type_, 'paper': paper})
    pdf = os.path.join(OUT, 'print-%s-%s.pdf' % (type_, paper))
    try:
        chrome(['--virtual-time-budget=6000', '--no-pdf-header-footer', '--print-to-pdf=' + pdf, 'file://' + path], 120)
    finally:
        os.remove(path)
    n = len(re.findall(rb'/Type\s*/Page[^s]', open(pdf, 'rb').read())) if os.path.exists(pdf) else -1
    if os.path.exists(pdf):
        os.remove(pdf)
    return n


def diff(expected, actual, path=''):
    """Yield readable differences between two JSON values."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        for k in sorted(set(expected) | set(actual)):
            if k not in actual:
                yield '%s: missing now (was %s)' % (path + k, json.dumps(expected[k])[:80])
            elif k not in expected:
                yield '%s: new (%s)' % (path + k, json.dumps(actual[k])[:80])
            else:
                yield from diff(expected[k], actual[k], path + k + '.')
    elif isinstance(expected, list) and isinstance(actual, list) and len(expected) == len(actual):
        for i, (e, a) in enumerate(zip(expected, actual)):
            yield from diff(e, a, '%s[%d].' % (path.rstrip('.'), i))
    elif expected != actual:
        yield '%s: expected %s, got %s' % (path.rstrip('.'), json.dumps(expected)[:80], json.dumps(actual)[:80])


def md(text):
    return str(text).replace('|', '\\|').replace('\n', ' ')


def report(res, pages, golden_diff, failures, warnings):
    """Markdown report: written to tests/out/report.md and, on GitHub, to the job summary."""
    checks = res['checks']
    bad = [c for c in checks if not c['ok']]
    keyed = re.compile(r'^\w+/(portrait|landscape)/(lower|upper|both)')
    n_print_ok = sum(1 for k, v in pages.items() if v == PAGES[k.split('/')[1]][k.split('/')[0]])
    out = ['# Smoke test: ' + ('FAILED' if failures else 'passed'), '']
    out.append('- **Checks:** %d, failed %d' % (len(checks), len(bad)))
    out.append('- **Print page counts:** %d of %d as expected' % (n_print_ok, len(pages)))
    if golden_diff is None:
        out.append('- **Golden snapshot:** not checked, `tests/golden.json` does not exist yet')
    else:
        out.append('- **Golden snapshot:** %d cases, %s' % (len(res['cases']), 'unchanged' if not golden_diff else '%d difference(s)' % len(golden_diff)))
    out.append('')
    if failures:
        out += ['## Problems', '']
        out += ['- ' + md(f) for f in failures]
        out += ['', 'If the change is intended, replace `tests/golden.json` with the `golden.json` from the `smoke-results` artifact.', '']
    for w in warnings:
        out += ['> **Note:** ' + md(w), '']

    other = [c for c in checks if not keyed.match(c['name'])]
    out += ['<details><summary>Letter options, privacy and errors (%d checks)</summary>' % len(other), '',
            '| | Check | Detail |', '|---|---|---|']
    out += ['| %s | %s | %s |' % ('✅' if c['ok'] else '❌', md(c['name']), md(c['detail'])) for c in other]
    out += ['', '</details>', '']

    out += ['<details><summary>Sheet types × paper × letters (%d combinations)</summary>' % len(res['cases']), '',
            '| Type | Paper | Letters | Size mm | Slider max | Sheets | Rows | Layout checks |', '|---|---|---|---|---|---|---|---|']
    for key, c in sorted(res['cases'].items()):
        t, p, l = key.split('/')
        mine = [x for x in checks if x['name'].startswith(key + ' ') or x['name'].startswith(key + ':')]
        ok = all(x['ok'] for x in mine)
        out.append('| %s | %s | %s | %s | %s | %d | %d | %s |' % (t, p, l, c['size'], c['max'], len(c['sheets']),
                   sum(x['rows'] for x in c['sheets']), ('✅ %d' if ok else '❌ %d') % len(mine)))
    out += ['', '</details>', '']

    out += ['<details><summary>Print page counts (lowercase alphabet)</summary>', '',
            '| Type | Paper | Expected | Got | |', '|---|---|---|---|---|']
    for k, v in pages.items():
        t, p = k.split('/')
        want = PAGES[p][t]
        out.append('| %s | %s | %d | %d | %s |' % (t, p, want, v, '✅' if v == want else '❌'))
    out += ['', '</details>', '']
    text = '\n'.join(out)
    with open(os.path.join(OUT, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(text)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write(text)


def main():
    os.makedirs(OUT, exist_ok=True)
    failures, warnings = [], []

    print('Driving the page (%s)...' % CHROME, flush=True)
    res = run_matrix()
    for c in res['checks']:
        if not c['ok']:
            failures.append('check failed: %s (%s)' % (c['name'], c['detail']))
    print('  %d checks, %d failed' % (len(res['checks']), sum(1 for c in res['checks'] if not c['ok'])), flush=True)

    print('Printing PDFs...', flush=True)
    pages = {}
    for paper, per in PAGES.items():
        for type_, want in per.items():
            got = pdf_pages(type_, paper)
            pages['%s/%s' % (type_, paper)] = got
            if got != want:
                failures.append('print pages %s/%s: expected %d, got %d' % (type_, paper, want, got))
    print('  ' + ', '.join('%s %s=%d' % (k.split('/')[1][:4], k.split('/')[0], v) for k, v in pages.items()), flush=True)

    golden_now = {'cases': res['cases']}
    json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1, sort_keys=True)
    with open(os.path.join(OUT, 'golden.json'), 'w') as f:
        json.dump(golden_now, f, indent=1, sort_keys=True)
        f.write('\n')

    d = None
    if os.path.exists(GOLDEN):
        d = list(diff(json.load(open(GOLDEN)), golden_now))
        print('Golden snapshot: %d difference(s)' % len(d), flush=True)
        failures += ['golden: ' + x for x in d[:60]]
        if len(d) > 60:
            failures.append('golden: ... and %d more' % (len(d) - 60))
    else:
        warnings.append('tests/golden.json does not exist yet, snapshot not checked. Download the "smoke-results" artifact, '
                        'commit its golden.json as tests/golden.json.')

    report(res, pages, d, failures, warnings)
    for w in warnings:
        print(('::warning::' if CI else 'WARNING: ') + w)
    for f in failures:
        print(('::error::' if CI else 'FAIL: ') + f)
    if failures:
        print('\n%d problem(s). If the change is intended, replace tests/golden.json with tests/out/golden.json.' % len(failures))
        sys.exit(1)
    print('\nOK')


if __name__ == '__main__':
    main()
