#!/usr/bin/env bash
# Export printable STLs into build/. Add a line per model you want.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build

render() {   # render <output name> <source file> [-D overrides...]
    local out="build/$1.stl" src="$2"
    shift 2
    echo "rendering $out"
    openscad -o "$out" "$@" "$src" 2>&1 | grep -E 'WARNING|ERROR' || true
    [[ -s "$out" ]] || { echo "failed: $out" >&2; exit 1; }
}

# Baseplate too big for the bed: export one STL per distinct tile size.
# The file name says how many copies of that tile to print.
render_tiled() {   # render_tiled <cells x> <cells y>
    local nx="$1" ny="$2" list="build/.tiles.echo"
    openscad -o "$list" -D cells_x="$nx" -D cells_y="$ny" parts/baseplate_tiled.scad 2>/dev/null
    sed -n 's/^ECHO: "TILE \([0-9]*\) \([0-9]*\)"$/\1 \2/p' "$list" | sort | uniq -c |
        while read -r count w h; do
            render "baseplate_${nx}x${ny}_tile_${w}x${h}_print${count}" parts/baseplate.scad \
                -D cells_x="$w" -D cells_y="$h"
        done
    rm -f "$list"
}

render baseplate_2x2 parts/baseplate.scad -D cells_x=2 -D cells_y=2
render bin_1x1x3     parts/bin.scad       -D cells_x=1 -D cells_y=1 -D units_z=3
render bin_2x1x3     parts/bin.scad       -D cells_x=2 -D cells_y=1 -D units_z=3

# Example drawer-sized plate. Change the size to your drawer, in cells.
render_tiled 9 7
