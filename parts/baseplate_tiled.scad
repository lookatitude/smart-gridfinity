// A baseplate larger than the printer bed, split into tiles that each fit.
// Tiles are whole cells, so they butt together and keep the 42 mm grid across the joints.
// Open this file to see the layout; build.sh exports one STL per distinct tile size.
include <../lib/constants.scad>
include <../lib/printer.scad>
use <baseplate.scad>

/* [Tiled baseplate] */
cells_x = 9;
cells_y = 7;
gap     = 3;   // spacing between tiles in this preview only

tiled_baseplate(cells_x, cells_y, gap);

// One line per tile, read by build.sh to decide what to export.
for (w = split_cells(cells_x, max_cells(0)), h = split_cells(cells_y, max_cells(1)))
    echo(str("TILE ", w, " ", h));

module tiled_baseplate(nx, ny, gap = 0) {
    xs = split_cells(nx, max_cells(0));
    ys = split_cells(ny, max_cells(1));
    total = [nx * GRID + (len(xs) - 1) * gap, ny * GRID + (len(ys) - 1) * gap];

    for (i = [0 : len(xs) - 1], j = [0 : len(ys) - 1]) {
        x = sum_first(xs, i) * GRID + i * gap + xs[i] * GRID / 2;
        y = sum_first(ys, j) * GRID + j * gap + ys[j] * GRID / 2;
        color((i + j) % 2 == 0 ? "dimgray" : "slategray")
            translate([x - total.x / 2, y - total.y / 2, 0])
                baseplate(xs[i], ys[j]);
    }
}
