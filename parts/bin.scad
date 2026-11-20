// Basic Gridfinity bin: one foot per cell, a hollow body and an optional stacking lip.
include <../lib/constants.scad>
include <../lib/printer.scad>
use <../lib/profile.scad>

/* [Bin] */
cells_x = 1;
cells_y = 1;
units_z = 3;       // height in 7 mm units, lip not included
lip     = true;    // stacking lip on top
magnets = false;   // magnet holes under each foot

assert(fits_bed([cells_x * GRID, cells_y * GRID, units_z * UNIT_Z + LIP_H]),
       "Bin is larger than the printer bed");

bin(cells_x, cells_y, units_z, lip, magnets);

module bin(nx = 1, ny = 1, uz = 3, lip = true, magnets = false) {
    assert(uz >= 2, "A bin needs at least 2 height units to have a cavity");

    outer = [nx * GRID - CLEARANCE, ny * GRID - CLEARANCE];
    top   = uz * UNIT_Z;
    lip_h = lip ? LIP_H - LIP_TRIM : 0;

    render(convexity = 4) difference() {
        union() {
            grid_copies(nx, ny) foot();
            translate([0, 0, FOOT_H - EPS])
                linear_extrude(top - FOOT_H + lip_h + EPS) rounded_rect(outer, BIN_R);
        }

        if (lip) {
            // Cavity narrows at 45 degrees under the lip so the overhang prints without support.
            stepped_solid(outer, BIN_R, [
                [FLOOR_Z, WALL],
                [top - (LIP_INSET - WALL), WALL],
                [top, LIP_INSET],
            ]);
            // The lip is the baseplate socket, so a bin stacks exactly as it sits on a plate.
            translate([0, 0, top - EPS]) socket([nx * GRID, ny * GRID]);
        } else {
            stepped_solid(outer, BIN_R, [[FLOOR_Z, WALL], [top + 1, WALL]]);
        }

        if (magnets)
            grid_copies(nx, ny)
                for (sx = [-1, 1], sy = [-1, 1])
                    translate([sx * MAGNET_OFFSET, sy * MAGNET_OFFSET, -EPS])
                        cylinder(d = MAGNET_D, h = MAGNET_H + EPS);
    }
}
