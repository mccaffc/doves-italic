#!/bin/sh
# Publish the type tester to docs/ for GitHub Pages.
# Single source of truth stays trials/tester.html; docs/ is a generated copy.
# Excludes the Doves roman (EULA: no distribution) — comparison is supplied locally by the user.
set -e
cd "$(dirname "$0")/.."

mkdir -p trials/fonts docs/fonts
cp trials/tester.html docs/index.html
# Publish the canonical builds to both testers so rebakes cannot leave stale fonts.
for destination in trials/fonts docs/fonts; do
  cp build/DovesItalic-Trial1.ttf build/DovesItalic-Trial2.ttf "$destination/"
done

echo "docs/ ready:"
ls -la docs docs/fonts