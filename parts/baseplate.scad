// Plain Gridfinity baseplate: an open frame of sockets.
include <../lib/constants.scad>
include <../lib/printer.scad>
use <../lib/profile.scad>

/* [Baseplate] */
cells_x = 2;
cells_y = 2;

assert(fits_bed([cells_x * GRID, cells_y * GRID]),
       "Baseplate is larger than the printer bed: use parts/baseplate_tiled.scad");

baseplate(cells_x, cells_y);

module baseplate(nx = 1, ny = 1) {
    difference() {
        linear_extrude(SOCKET_H) rounded_rect([nx * GRID, ny * GRID], SOCKET_R);
        grid_copies(nx, ny) socket(through = true);
    }
}
