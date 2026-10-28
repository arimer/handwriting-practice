# Script Practice

Open `index.html` directly in your browser. No install, no server. Print with ⌘/Ctrl + P, paper A4, margins none.

## Sheet types

| Type | Guides | Row pitch |
|---|---|---|
| Copperplate guides | ascender / x-height / baseline / descender, 3:2:3 at 2 mm unit, dotted slant lines every 3 mm (55° by default) | 20 mm |
| Handwriting lines | top line, dashed x-height line, baseline | 16 mm |
| Slant bands | 5 mm x-height bands filled with dotted slant lines every 3 mm (55° by default) | 15 mm |
| Slant grid | 20 mm squares, fine 4 mm sub-lines, one diagonal per cell | 20 mm |
| Dot grid | dots every 5 mm | 15 mm |
| Square grid | 5 mm squares | 15 mm |

Rows per page are calculated so each sheet fills exactly one A4 page. Letter size auto-fits the font's x-height to the guides when you change sheet type or font; the slider overrides it. On every sheet type the slider maximum is limited so the tallest letter reaches at most 25% past the room above the baseline (the ascender line on Copperplate), so fonts with very tall ascenders get a smaller size and letters can't outgrow the sheet.

## Choosing letters

- **Letters** picks lowercase, uppercase, or both as pairs (Aa, Bb …).
- **Only these letters** limits the sheet to the letters you type (e.g. `aeoc`). Case is ignored, duplicates are dropped, the typed order is kept, and only a–z are supported. Leave it empty for the whole alphabet. The Letters choice still decides lowercase, uppercase or pairs.
- **Lines per letter** (1–10) gives each letter that many rows in a row, grouped: with 3, `a` is practised on three rows, then `e` on three rows. Extra rows continue on more sheets.

## Paper orientation

The "Paper" select switches between A4 portrait and A4 landscape. Landscape sheets have longer rows but fewer rows per page, so the alphabet continues on more sheets. The print dialog picks up the chosen orientation; paper size stays A4, margins none.

## Slant angle

On sheet types with slant lines (Copperplate guides, Slant bands) the "Slant angle" slider sets the angle from 45° to 90°; the default is 55°. It changes the guides and the sheet header, not the letters, which keep the slant of the font. Letters start in the middle of a slant space, so the spacing between repeats is a multiple of the 3 mm line spacing.

## Add, remove or rename fonts (local copy only)

The hosted page ships only Playwrite CA. To use other fonts, download the project and open `index.html` from your computer.

1. Drop font files (`.otf`, `.ttf`, `.woff`, or `.woff2`) into the `fonts/` folder, or delete ones you don't want.
2. Run the manifest script in this folder:
   - **macOS / Linux:** `./scripts/update-fonts-manifest.sh` (or `bash scripts/update-fonts-manifest.sh`)
   - **Windows:** double-click `scripts\update-fonts-manifest.cmd`

   It writes `fonts/fonts-manifest.local.js` (git-ignored) with every font file it finds except the ones
   already in the committed `fonts/fonts-manifest.js`, which it never changes. New fonts are named after their
   filename; fonts already listed keep their name and position. Deleted files are dropped.
3. Reload `index.html`. The fonts show up in the "Font (from /fonts folder)" dropdown.

Your local fonts are listed before Playwrite CA, so the first entry of `fonts/fonts-manifest.local.js` is
selected when the page loads. To rename a font in the dropdown, or change which one comes first, edit
`fonts/fonts-manifest.local.js` by hand. The script keeps your edits on the next run.

## Using a font from Google Fonts instead

If you don't want to download a file, use the "Or online Google Font" field: start typing and pick one of the suggested handwriting fonts (e.g. `Dancing Script`), or type any other font's exact name as Google Fonts lists it (e.g. `Playwrite CA Guides`). This needs an internet connection and isn't saved anywhere; the dropdown is the reliable offline option.

**Privacy:** the font is loaded from Google's servers, so your browser sends your IP address to Google. Nothing is requested until you enter a name, and the local fonts in the dropdown never contact Google.

## Updating the Google font suggestions

`google-fonts-handwriting.js` is a static snapshot of family names (the Google Fonts metadata endpoint cannot be fetched from the page because it sends no CORS header). To refresh it, download the metadata and print the new list:

```sh
curl -s https://fonts.google.com/metadata/fonts -o metadata.json
python3 - <<'EOF'
import json
raw = open('metadata.json', encoding='utf-8').read()
fams = json.loads(raw[raw.index('{'):])['familyMetadataList']   # the file starts with a few junk characters
keep = [f for f in fams if f['category'] == 'Handwriting'
        and f.get('primaryScript', '') in ('', 'Latn') and 'Guides' not in f['family']]
keep.sort(key=lambda f: f['popularity'])                          # most popular first
print('window.GOOGLE_HANDWRITING_FONTS = [')
print(',\n'.join('  ' + json.dumps(f['family']) for f in keep))
print('];')
EOF
```

Replace the array in `google-fonts-handwriting.js` with the output and update the family count and snapshot date in its header comment. "Guides" fonts are left out because they draw their own ruling lines into every letter, which clashes with the sheet's guides.

## Tests

A smoke / regression test checks that the page still behaves as it does now. It needs only Python 3 and Chrome (macOS or Linux):

```sh
python3 tests/run.py          # set CHROME=/path/to/chrome to use a specific browser
```

It loads a temporary copy of `index.html` in headless Chrome, always with the bundled Playwrite CA font, and checks:

- **Letter options:** "Only these letters" (case ignored, duplicates dropped, typed order kept, invalid input falls back to the whole alphabet, sheet titles) and "Lines per letter" (grouping, clamped to 1–10).
- **Every sheet type** × portrait/landscape × lowercase/uppercase/pairs: the letter size stays inside the slider range, the guides end above the bottom padding, and the footer sits below the guides.
- **Printing:** each sheet type and paper prints to the expected number of A4 pages (lowercase: portrait 3/2/2/3/2/2, landscape 4/3/3/4/3/3 for copperplate/lines/bands/slantgrid/dots/squares).
- **Privacy:** nothing is requested from the network, and the Google Fonts link stays unset, until a font name is typed. No script errors.
- **Golden snapshot** (`tests/golden.json`): for every combination the sheet count, rows, letter counts, slider size and maximum, and a hash of each sheet's SVG. Any change to the drawn sheets shows up as a difference.

Every run also writes a Markdown report (`tests/out/report.md`): headline numbers, problems first, then collapsible tables for the letter-option checks, every sheet type × paper × letters combination and the print page counts. On GitHub it is shown as the job summary at the top of the run page.

The test runs on every push and pull request in GitHub Actions (`.github/workflows/test.yml`, Ubuntu with Chrome). The GitHub run is the reference: the page measures the font by scanning rendered pixels, so a snapshot made on another OS or Chrome version can differ slightly without a real regression.

**Updating the snapshot:** each run uploads its results as the `smoke-results` artifact (Actions tab, open the run, Artifacts). While `tests/golden.json` does not exist the snapshot check is skipped with a warning. After an intended change to the sheets, download the artifact and replace `tests/golden.json` with the `golden.json` from it, then commit.

Not covered: your own fonts, Google Fonts loading, the `.cmd` script, real printing and how the sheets look. Test output and temporary pages (`tests/out/`, `.smoke-tmp-*.html`) are git-ignored.

## Licensing note

The code is under the [PolyForm Noncommercial License 1.0.0](LICENSE): free for personal, educational and other noncommercial use, not for commercial use. It is source-available, not open source. The license covers only the code, not the fonts below.

Font files have their own licenses (check before using one commercially). The only font committed to git is Playwrite CA (SIL Open Font License 1.1, © The Playwrite Project Authors; licence text in `fonts/PlaywriteCA-OFL.txt`). All other font files stay local: `fonts/` is git-ignored except for that font and its licence files, and the manifest in git lists only that font.
