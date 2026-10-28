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

## Licensing note

The code is under the [PolyForm Noncommercial License 1.0.0](LICENSE): free for personal, educational and other noncommercial use, not for commercial use. It is source-available, not open source. The license covers only the code, not the fonts below.

Font files have their own licenses (check before using one commercially). The only font committed to git is Playwrite CA (SIL Open Font License 1.1, © The Playwrite Project Authors; licence text in `fonts/PlaywriteCA-OFL.txt`). All other font files stay local: `fonts/` is git-ignored except for that font and its licence files, and the manifest in git lists only that font.
