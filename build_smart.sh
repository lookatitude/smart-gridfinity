#!/usr/bin/env bash
# Export printable STLs for the powered ("smart") parts into build/smart/.
# File names end in the filament to use and, where it is not 1, how many to print.
# Floors and sleeves hold one piece per compartment: use "split to objects" in the slicer
# if you want to arrange them separately. Floors are already turned plate-down.
# Tiles need supports under the socket floor. Sleeves are optional.
# Bins marked "label" have label tabs; jar bins do not, because the tab would be in the way.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/smart

render() {   # render <output name> <source file> [-D overrides...]
    local out="build/smart/$1.stl" src="$2"
    shift 2
    echo "rendering $out"
    openscad -o "$out" "$@" "$src" 2>&1 | grep -E 'WARNING|ERROR' || true
    [[ -s "$out" ]] || { echo "failed: $out" >&2; exit 1; }
}

bin() {   # bin <name> <cells x> <cells y> <units z> <compartments x> <compartments y> [label]
    local name="$1" size=(-D cells_x="$2" -D cells_y="$3" -D units_z="$4"
                          -D compartments_x="$5" -D compartments_y="$6"
                          -D label_tabs="$([[ "${7:-}" == label ]] && echo true || echo false)")
    render "${name}_body"        parts/smart_bin.scad "${size[@]}" -D 'part="body"'
    render "${name}_floor_clear" parts/smart_bin.scad "${size[@]}" -D 'part="floor"'
}

sleeve() {   # sleeve <name> <cells x> <cells y> <units z> <compartments x> <compartments y> <jar diameter>
    render "$1_sleeve_clear" parts/jar_sleeve.scad -D cells_x="$2" -D cells_y="$3" -D units_z="$4" \
        -D compartments_x="$5" -D compartments_y="$6" -D jar_diameter="$7"
}

tile() {   # tile <cells x> <cells y> <copies>
    render "tile_$1x$2_print$3" parts/smart_base.scad -D cells_x="$1" -D cells_y="$2"
}

# Test set: a 2x2 tile, a 2x2 starter tile, a 2x1 bin in two compartments, two 1x1 bins,
# the power bin.
tile 2 2 1
render starter_tile_2x2 parts/smart_base.scad -D cells_x=2 -D cells_y=2 -D power_cell=true
render tile_key_print4 parts/tile_key.scad
bin test_bin_2x1 2 1 3 2 1
bin test_bin_1x1_label_print2 1 1 4 1 1 label
render power_bin_body parts/power_bin.scad -D 'part="body"'
render power_bin_lid  parts/power_bin.scad -D 'part="lid"'

# Full collection (layout in tests/grid_sim.py): eight tiles of three sizes, and the bins.
tile 4 3 2
tile 3 3 4
tile 2 3 1
render starter_tile_2x3 parts/smart_base.scad -D cells_x=2 -D cells_y=3 -D power_cell=true
bin paint_bin_2x2_print12 2 2 5 2 2
bin cleaner_bin_2x1       2 1 7 2 1
bin bottle_bin_4x3        4 3 8 3 2
bin pen_holder_2x1        2 1 10 2 1 label

# Drawer unit, 4x3 cells, 13 units high, drawer in 3x2 compartments.
# The shell prints standing on its back wall. Drawer body and clear part are one two-colour print.
for p in shell floor drawer clear; do
    render "drawer_unit_4x3_$p" parts/drawer_unit.scad -D "part=\"$p\""
done

# Optional clear sleeves, printed as needed.
sleeve paint_bin_2x2  2 2 5 2 2 25.1
sleeve bottle_bin_4x3 4 3 8 3 2 48.2
