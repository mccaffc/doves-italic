# Doves Italic — a private-use companion italic study

An italic companion for the Doves Type roman, built by adapting
[Cormorant Italic](https://github.com/CatharsisFonts/Cormorant) (SIL OFL)
to Doves' metrics and pushing its letterforms toward Doves DNA.

**Status: study / trial.** Built for private use. Not a finished typeface.

## What's here

| Path | What |
| --- | --- |
| `sources/` | Source variable fonts (Cormorant Italic, EB Garamond Italic — both OFL) |
| `build/` | Baked trial fonts (`DovesItalic-Trial1.ttf`, `DovesItalic-Trial2.ttf`) |
| `trials/` | Specimen page + **type tester** (the GitHub Pages site) |
| `tools/` | Python pipeline: bake, measure, quote construction, proofs |
| `OFL.txt` | SIL Open Font License 1.1 — applies to all font files here |

The live tester is at **https://mccaffc.github.io/doves-italic/**.

## Builds

- **Trial 1** — Cormorant Italic wght 550, scaled to Doves x-height (374),
  leaned to 7°, word space matched to Doves (193 units).
- **Trial 2** — Trial 1 plus four quote marks redrawn to Doves construction:
  ball head → throat → hooked tail, Doves' asymmetric placement
  (left quotes low, right quotes high) and Doves advances.

## Local use

```sh
cd trials && python3 -m http.server 8741
# http://localhost:8741/tester.html
```

The tester shows the selected build, font loading result, review status and local
save status. It remembers your text and sheet settings in this browser. Select
text to apply local features; choose **Done with selection** to return to the
whole sheet. **Copy sheet CSS** exports global settings; print includes local
formatting. Both builds can be downloaded directly.

Open **Study status & comparison** to load your licensed Doves roman for the
Roman / Both views. The file stays in the tab: it is never uploaded or persisted.
Without it, those controls stay visibly disabled. Font loading failures display
an explicit fallback warning.

## Licensing notes

- All font files in this repo are **Cormorant-derived under SIL OFL 1.1**
  (see `OFL.txt`). No Reserved Font Name is used.
- The Doves Type roman itself is **not** included and is **not** redistributable:
  it is licensed from Typespec for Chris's own use. Nothing in this repo
  contains Doves Type software.
- Tools and scripts: private study code, no license granted.

## Pipeline quick reference

```sh
.venv/bin/python tools/bake_font.py     # Trial 1 from Cormorant VF
.venv/bin/python tools/bake_quotes.py   # Trial 2 = Trial 1 + Doves quotes
.venv/bin/python tools/dna_study.py     # metric comparison vs Doves roman
tools/deploy_pages.sh                   # publish tester to docs/ for Pages
```

*(The bake/measure tools read the Doves roman from local Google Drive storage;
that path exists only on the owner's machine and is not part of the repo.)*
