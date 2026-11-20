// Fit check: bins seated on a baseplate, one of them stacked. Open this in OpenSCAD to look around.
include <lib/constants.scad>
use <parts/baseplate.scad>
use <parts/bin.scad>

SEAT = SOCKET_PROFILE[0][0];   // a foot rests on the bottom of the socket

color("dimgray") baseplate(3, 2);

color("orange") translate([-GRID, GRID / 2, SEAT]) rotate(90) bin(2, 1, 3);
color("steelblue") translate([GRID / 2, 0, SEAT]) bin(2, 2, 2);
color("tomato") translate([GRID / 2, 0, SEAT + 2 * UNIT_Z]) bin(2, 2, 3);
