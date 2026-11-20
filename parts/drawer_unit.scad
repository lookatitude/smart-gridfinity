// Smart drawer unit: "a bin with an outer shell".
// The shell is the smart part. Its bottom is the ordinary smart bin foot and floor (pads,
// magnets, latches, bin board); it has three walls, a plain closed top with a stacking
// lip (decided: no powered sockets on top), and an open front. The drawer is passive: a box with compartments that
// slides on the shell's false floor. No contact makes or breaks when it slides.
//
// Light: one LED per drawer compartment sits under the shell's false floor, below a hole.
// The drawer bottom has a clear window over each LED, and each column has a clear strip
// in the front panel, lit by the front-row LED, so a closed drawer can show which column.
//
// Printed pieces: drawer_shell() (print standing on its back wall), drawer_shell_floor()
// (plate down), drawer_body() and drawer_clear() (one two-colour print, bottom down).
include <../lib/constants.scad>
include <../lib/smart.scad>
include <../lib/printer.scad>
use <../lib/profile.scad>
use <smart_bin.scad>

/* [Drawer unit] */
cells_x = 4;
cells_y = 3;
units_z = 13;          // 13 x 7 = 91 mm: whatever stacks on top sits exactly there
compartments_x = 3;
compartments_y = 2;
part = "all";          // [all, shell, floor, drawer, clear]
pull_out = 0;          // preview only: how far the drawer is open

assert(fits_bed([cells_x * GRID, units_z * UNIT_Z + LIP_H, cells_y * GRID]),
       "Shell is larger than the printer bed (it prints standing on its back wall)");

if (part == "all" || part == "shell") color("slategray") drawer_shell(cells_x, cells_y, units_z);
if (part == "all") color("gainsboro") drawer_shell_floor(cells_x, cells_y, compartments_x, compartments_y);
if (part == "floor") rotate([180, 0, 0])
    drawer_shell_floor(cells_x, cells_y, compartments_x, compartments_y);
if (part == "all" || part == "drawer") translate([0, -pull_out, 0]) color("orange")
    drawer_body(cells_x, cells_y, units_z, compartments_x, compartments_y);
if (part == "all" || part == "clear") translate([0, -pull_out, 0]) color("white", 0.7)
    drawer_clear(cells_x, cells_y, units_z, compartments_x, compartments_y);

SHELL_WALL  = LIP_INSET;   // 2.6 mm: the false floor then fits exactly as in a bin
SHELL_ROOF  = 1.6;
DRAWER_FIT  = 0.4;         // each side
DRAWER_GAP  = 0.3;         // above and below
DRAWER_WALL = 1.2;
DRAWER_BOTTOM = 1.2;
LED_HOLE_D  = 8;           // hole in the shell floor over each LED
WINDOW_D    = 18;          // clear window in the drawer bottom
STRIP_W     = 8;           // clear strip in the front panel
STRIP_H     = 24;
PULL_R      = 14;          // finger notch in the top of the front panel
SHELL_FLOOR_TOP = BAY_TOP + FALSE_FLOOR_T;

function shell_outer(nx, ny) = [nx * GRID - CLEARANCE, ny * GRID - CLEARANCE];
// Drawer box: x range, y range (front face flush with the shell front), z range.
function drawer_x(nx) = (shell_outer(nx, 1).x - 2 * SHELL_WALL) / 2 - DRAWER_FIT;
function drawer_y0(ny) = -shell_outer(1, ny).y / 2;
function drawer_y1(ny) = shell_outer(1, ny).y / 2 - SHELL_WALL - DRAWER_FIT;
function drawer_z0() = SHELL_FLOOR_TOP + DRAWER_GAP;
function drawer_z1(uz) = uz * UNIT_Z - SHELL_ROOF - DRAWER_GAP;
// Inside of the drawer, and the centre of compartment (a, b).
function inside_x(nx) = drawer_x(nx) - DRAWER_WALL;
function inside_y0(ny) = drawer_y0(ny) + SHELL_WALL;
function inside_y1(ny) = drawer_y1(ny) - DRAWER_WALL;
function comp_centre(nx, ny, cx, cy, a, b) = [
    -inside_x(nx) + (a + 0.5) * 2 * inside_x(nx) / cx,
    inside_y0(ny) + (b + 0.5) * (inside_y1(ny) - inside_y0(ny)) / cy];
function drawer_inside_height(uz) = drawer_z1(uz) - drawer_z0() - DRAWER_BOTTOM;

echo(str("Drawer inside: ", 2 * inside_x(cells_x), " x ", inside_y1(cells_y) - inside_y0(cells_y),
         " x ", drawer_inside_height(units_z), " mm"));

module drawer_shell(nx = 4, ny = 3, uz = 13) {
    outer = shell_outer(nx, ny);
    top = uz * UNIT_Z;
    render(convexity = 8) difference() {
        union() {
            smart_bin_body(nx, ny, uz);
            // walls thickened to SHELL_WALL over the full height
            translate([0, 0, FLOOR_Z]) linear_extrude(top - FLOOR_Z) difference() {
                rounded_rect(outer - 2 * [WALL - EPS, WALL - EPS], BIN_R - WALL);
                rounded_rect(outer - 2 * [SHELL_WALL, SHELL_WALL], BIN_R - SHELL_WALL);
            }
            // closed top, just under the stacking lip
            translate([0, 0, top - SHELL_ROOF]) linear_extrude(SHELL_ROOF)
                rounded_rect(outer - 2 * [WALL - EPS, WALL - EPS], BIN_R - WALL);
        }
        // open front, from the false floor up to the roof
        translate([-outer.x / 2 + SHELL_WALL, -outer.y / 2 - 1, SHELL_FLOOR_TOP])
            // deep enough to remove the rounded inner corners, so the opening is square
            cube([outer.x - 2 * SHELL_WALL, BIN_R + 1 + EPS, top - SHELL_ROOF - SHELL_FLOOR_TOP]);
    }
}

// One-piece false floor the drawer slides on: opaque, with a hole over each LED and a
// ring underneath that holds the LED board.
module drawer_shell_floor(nx = 4, ny = 3, cx = 3, cy = 2) {
    ring_d = LED_PCB_D + 2 * LED_FIT;
    render(convexity = 4) difference() {
        union() {
            smart_bin_floor(nx, ny, 1, 1);
            for (a = [0 : cx - 1], b = [0 : cy - 1])
                translate(concat(comp_centre(nx, ny, cx, cy, a, b), [BAY_TOP - LED_HOLDER_H]))
                    difference() {
                        cylinder(d = ring_d + 2 * LED_HOLDER_T, h = LED_HOLDER_H + EPS);
                        translate([0, 0, -EPS]) cylinder(d = ring_d, h = LED_HOLDER_H + 1);
                        translate([-1.5, 0, -EPS]) cube([3, ring_d, LED_HOLDER_H + 1]);
                    }
        }
        for (a = [0 : cx - 1], b = [0 : cy - 1])
            translate(concat(comp_centre(nx, ny, cx, cy, a, b), [BAY_TOP - EPS]))
                cylinder(d = LED_HOLE_D, h = FALSE_FLOOR_T + 2 * EPS);
    }
}

module drawer_box(nx, ny, uz) {
    translate([-drawer_x(nx), drawer_y0(ny), drawer_z0()])
        cube([2 * drawer_x(nx), drawer_y1(ny) - drawer_y0(ny), drawer_z1(uz) - drawer_z0()]);
}

module drawer_body(nx = 4, ny = 3, uz = 13, cx = 3, cy = 2) {
    ix = inside_x(nx);
    iy0 = inside_y0(ny); iy1 = inside_y1(ny);
    z0 = drawer_z0(); z1 = drawer_z1(uz);
    render(convexity = 6) difference() {
        union() {
            difference() {
                drawer_box(nx, ny, uz);
                translate([-ix, iy0, z0 + DRAWER_BOTTOM]) cube([2 * ix, iy1 - iy0, z1]);
            }
            if (cx > 1) for (k = [1 : cx - 1])
                translate([-ix + k * 2 * ix / cx - DRAWER_WALL / 2, iy0 - EPS, z0])
                    cube([DRAWER_WALL, iy1 - iy0 + 2 * EPS, z1 - z0]);
            if (cy > 1) for (k = [1 : cy - 1])
                translate([-ix - EPS, iy0 + k * (iy1 - iy0) / cy - DRAWER_WALL / 2, z0])
                    cube([2 * ix + 2 * EPS, DRAWER_WALL, z1 - z0]);
        }
        drawer_clear_shape(nx, ny, uz, cx, cy);
        // finger notch
        translate([0, drawer_y0(ny) - 1, z1]) rotate([-90, 0, 0])
            cylinder(r = PULL_R, h = SHELL_WALL + 2);
    }
}

// Clear body: a window in the bottom of every compartment, and for each column a strip
// from the front-row window forward and up the front panel.
module drawer_clear(nx = 4, ny = 3, uz = 13, cx = 3, cy = 2) {
    render(convexity = 4) drawer_clear_shape(nx, ny, uz, cx, cy);
}

module drawer_clear_shape(nx, ny, uz, cx, cy) {
    z0 = drawer_z0();
    for (a = [0 : cx - 1]) {
        for (b = [0 : cy - 1])
            translate(concat(comp_centre(nx, ny, cx, cy, a, b), [z0]))
                cylinder(d = WINDOW_D, h = DRAWER_BOTTOM);
        c = comp_centre(nx, ny, cx, cy, a, 0);
        translate([c.x - STRIP_W / 2, drawer_y0(ny), z0]) {
            cube([STRIP_W, c.y - drawer_y0(ny), DRAWER_BOTTOM]);
            cube([STRIP_W, SHELL_WALL, STRIP_H]);
        }
    }
}
