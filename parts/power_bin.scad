// Power bin: brings 12-24 V into the grid and houses the hub radio (pcb/power_board).
// It only works on the power cell of a starter tile. Four brass screw heads stand proud
// of its foot and reach the feed pins in that cell's wells. It seats in two orientations,
// half a turn apart, and both are electrically correct; a quarter turn off, the screw
// heads land on the socket floor and the bin does not seat.
include <../lib/constants.scad>
include <../lib/smart.scad>
use <../lib/profile.scad>
use <bin.scad>
use <smart_bin.scad>

/* [Power bin] */
units_z = 4;
part    = "all";   // [all, body, lid]

if (part == "all" || part == "body") color("dimgray") power_bin_body(units_z);
if (part == "all") color("goldenrod") feed_heads();
if (part == "all" || part == "lid") color("gray") power_bin_lid(units_z);

module power_bin_body(uz = 4) {
    back = (GRID - CLEARANCE) / 2;
    render(convexity = 8) {
        difference() {
            union() {
                bin(1, 1, uz, lip = true, magnets = true);
                // two ledges the board rests on
                for (s = [-1, 1]) translate([s * (POWER_BOARD.x / 2 + 0.6), 0, (FLOOR_Z - 0.2 + POWER_BOARD_Z) / 2])
                    cube([5.2, GRID - CLEARANCE - 2 * WALL + EPS, POWER_BOARD_Z - FLOOR_Z + 0.2], center = true);
            }
            for (x = FEED_X) translate([x, 0, -EPS]) cylinder(d = FEED_SCREW_D, h = FLOOR_Z + 2 * EPS);
            translate([0, back - 3, DC_JACK_Z]) rotate([-90, 0, 0]) cylinder(d = DC_JACK_D, h = 4);
            for (side = [90, 270]) rotate(side) latch_cuts();
        }
        for (side = [90, 270]) rotate(side) latch_bump();
    }
}

// Stand-in for the power board, for fit checks only.
module power_board_ghost() {
    translate([-POWER_BOARD.x / 2, -POWER_BOARD.y / 2, POWER_BOARD_Z]) cube(POWER_BOARD);
}

// The four screw heads under the foot. Shown in previews and used in fit checks.
module feed_heads() {
    for (x = FEED_X) translate([x, 0, -FEED_HEAD_H]) cylinder(d = FEED_HEAD_D, h = FEED_HEAD_H);
}

// The stacking lip is a socket, so the lid is the lower part of a foot.
module power_bin_lid(uz = 4) {
    h = LIP_H - LIP_TRIM;
    translate([0, 0, uz * UNIT_Z]) render() intersection() {
        foot();
        translate([-GRID, -GRID, 0]) cube([2 * GRID, 2 * GRID, h]);
    }
}
