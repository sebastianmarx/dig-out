#!/usr/bin/env bash
# Renders every art asset headless and post-processes them into frontend/public/assets.
# Usage (from repo root): art/scripts/render_all.sh   (set BLENDER=... if blender is not on PATH)
set -euo pipefail
cd "$(dirname "$0")/../.."
BLENDER="${BLENDER:-blender}"
script() { if command -v wslpath >/dev/null; then wslpath -w "art/scripts/$1"; else echo "art/scripts/$1"; fi; }
run() { "$BLENDER" --factory-startup -b --python "$(script "$1")" -- "${@:2}"; }

run build_cellblock.py
for place in cafeteria showers infirmary recreation yard; do run build_place.py --place "$place"; done
run build_board.py
for n in 01 02 03 04 05 06; do run build_character.py --char "char.$n"; done
run build_items.py
(cd art && npm run postprocess)
