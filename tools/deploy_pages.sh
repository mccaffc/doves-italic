#!/bin/sh
# Publish the type tester to docs/ for GitHub Pages.
# Single source of truth stays trials/tester.html; docs/ is a generated copy.
# Excludes the Doves roman (EULA: no distribution) — the tester hides that panel.
set -e
cd "$(dirname "$0")/.."

mkdir -p docs/fonts
cp trials/tester.html docs/index.html
cp trials/fonts/DovesItalic-Trial1.ttf trials/fonts/DovesItalic-Trial2.ttf docs/fonts/

echo "docs/ ready:"
ls -la docs docs/fonts