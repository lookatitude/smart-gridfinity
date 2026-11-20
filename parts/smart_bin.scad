// Bin for the powered base. Its first cell (front left) carries the bin board: a round
// board with four contact rings, glued into the foot. Bins larger than one cell get a
// second, unpopulated board in the diagonally opposite foot; only its centre pad is used,
// wired to the same ID chip, so the same ID shows up in two cells.
// The cavity can be split into compartments, independent of the cell count. Every
// compartment has a loose false floor printed in clear filament, with a holder for
// one LED on its underside, so the floor of that compartment glows.
// Printed pieces: smart_bin_body() in any colour, smart_bin_floor() in clear.
include <../lib/constants.scad>
include <../lib/smart.scad>
include <../lib/printer.scad>
use <../lib/profile.scad>
use <bin.scad>

/* [Smart bin] */
cells_x = 1;
cells_y = 1;
units_z = 3;
compartments_x = 1;   // compartments side by side, independent of the cell count
compartments_y = 1;   // compartments front to back
label_tabs = false;   // a label tab at the back of every compartment (not for jar bins)
part    = "all";   // [all, body, floor]

if (part == "all" || part == "body")
    color("orange") smart_bin_body(cells_x, cells_y, units_z, compartments_x, compartments_y, label_tabs);
if (part == "all")
    color("white", 0.7) smart_bin_floor(cells_x, cells_y, compartments_x, compartments_y, label_tabs);
// Exported on its own, the false floor is turned plate-down, the way it prints.
if (part == "floor") rotate([180, 0, 0])
    color("white", 0.7) smart_bin_floor(cells_x, cells_y, compartments_x, compartments_y, label_tabs);

FOOT_BAND = (GRID - CLEARANCE) / 2 - FOOT_PROFILE[1][1];   // half-width of the foot's vertical band
FLOOR_TOP = BAY_TOP + FALSE_FLOOR_T;                       // top of the false floors

function cell_pos(i, j, nx, ny) = [(i - (nx - 1) / 2) * GRID, (j - (ny - 1) / 2) * GRID, 0];

// Inner size of the bin cavity, and the edges of compartment k of n along one axis.
function cavity_size(nx, ny) = [nx * GRID - CLEARANCE - 2 * WALL, ny * GRID - CLEARANCE - 2 * WALL];
function comp_edge(k, n, len) = -len / 2 + k * len / n;
function comp_mid(k, n, len) = (comp_edge(k, n, len) + comp_edge(k + 1, n, len)) / 2;

module smart_bin_body(nx = 1, ny = 1, uz = 3, cx = 1, cy = 1, label = false) {
    assert(uz >= 3, "A smart bin needs at least 3 height units: the false floor takes 4.6 mm");
    assert(!label || cavity_size(nx, ny).y / cy >= LABEL_DEPTH + 18,
           "Compartments are too shallow front to back for a label tab: the LED would not fit under the shortened floor");
    render(convexity = 8) {
        difference() {
            union() {
                bin(nx, ny, uz, lip = true, magnets = true);
                ledge(nx, ny);
                dividers(nx, ny, uz, cx, cy);
                if (label) label_tabs(nx, ny, uz, cy);
            }
            if (label) label_wire_channels(nx, ny, cx, cy);
            translate(cell_pos(0, 0, nx, ny)) foot_board_cut();
            if (nx * ny > 1) translate(cell_pos(nx - 1, ny - 1, nx, ny)) foot_board_cut();
            grid_copies(nx, ny) for (side = [90, 270]) rotate(side) latch_cuts();
        }
        grid_copies(nx, ny) for (side = [90, 270]) rotate(side) latch_bump();
    }
}

// A label tab along the back of every row of compartments, and under each the fixed
// floor step that lets the shortened false floor drop straight in.
module label_tabs(nx, ny, uz, cy) {
    inner = cavity_size(nx, ny);
    top = uz * UNIT_Z;
    for (b = [0 : cy - 1]) {
        yb = comp_edge(b + 1, cy, inner.y);
        back = yb + WALL / 2;
        translate([-inner.x / 2 - WALL / 2, 0, 0]) rotate([90, 0, 90]) linear_extrude(inner.x + WALL)
            polygon([[back, top], [yb - LABEL_DEPTH, top], [yb - LABEL_DEPTH, top - LABEL_T],
                     [back, top - LABEL_T - LABEL_DEPTH - WALL / 2]]);
        translate([-inner.x / 2 - WALL / 2, yb - LABEL_DEPTH, FLOOR_Z - EPS])
            cube([inner.x + WALL, LABEL_DEPTH + WALL / 2, FLOOR_TOP - FLOOR_Z + EPS]);
    }
}

// With label tabs, the floor step under each tab blocks the gap between two rows of
// compartments. This cuts a low channel through the step for the wires. It is too low for
// an LED board, so in a labelled bin with more than one row the chain is threaded through
// before the last LED is soldered.
module label_wire_channels(nx, ny, cx, cy) {
    inner = cavity_size(nx, ny);
    if (cy > 1) for (a = [0 : cx - 1], b = [0 : cy - 2])
        translate([comp_mid(a, cx, inner.x) - 3, comp_edge(b + 1, cy, inner.y) - LABEL_DEPTH - 1, FLOOR_Z])
            cube([6, LABEL_DEPTH + 2 + DIVIDER_T, 2.4]);
}

// The false floors must pass the narrow opening under the stacking lip, so they are
// smaller than the cavity. This thicker wall at the bottom closes the gap round them.
module ledge(nx, ny) {
    outer = [nx * GRID - CLEARANCE, ny * GRID - CLEARANCE];
    translate([0, 0, FLOOR_Z - EPS]) linear_extrude(FLOOR_TOP - FLOOR_Z + EPS) difference() {
        rounded_rect(outer - 2 * [WALL - EPS, WALL - EPS], BIN_R - WALL);
        rounded_rect(outer - 2 * [LIP_INSET, LIP_INSET], BIN_R - LIP_INSET);
    }
}

// Walls that split the cavity into cx by cy compartments. Each has a gap at its foot,
// under the false floors, for the wires to the lights of the other compartments.
module dividers(nx, ny, uz, cx, cy) {
    inner = cavity_size(nx, ny);
    h = uz * UNIT_Z - FLOOR_Z;
    gap_h = BAY_TOP - FLOOR_Z - 0.2;
    translate([0, 0, FLOOR_Z - EPS]) difference() {
        union() {
            if (cx > 1) for (k = [1 : cx - 1])
                translate([comp_edge(k, cx, inner.x) - DIVIDER_T / 2, -inner.y / 2 - WALL / 2, 0])
                    cube([DIVIDER_T, inner.y + WALL, h]);
            if (cy > 1) for (k = [1 : cy - 1])
                translate([-inner.x / 2 - WALL / 2, comp_edge(k, cy, inner.y) - DIVIDER_T / 2, 0])
                    cube([inner.x + WALL, DIVIDER_T, h]);
        }
        for (a = [0 : cx - 1], b = [0 : cy - 1]) {
            if (a > 0) translate([comp_edge(a, cx, inner.x) - DIVIDER_T,
                                  comp_mid(b, cy, inner.y) - WIRE_GAP_W / 2, 0])
                cube([2 * DIVIDER_T, WIRE_GAP_W, gap_h]);
            if (b > 0) translate([comp_mid(a, cx, inner.x) - WIRE_GAP_W / 2,
                                  comp_edge(b, cy, inner.y) - DIVIDER_T, 0])
                cube([WIRE_GAP_W, 2 * DIVIDER_T, gap_h]);
        }
    }
}

// False floors: one clear tray per compartment, dropped in upside down, with a ring
// underneath that holds the LED board facing up into the plate.
module smart_bin_floor(nx = 1, ny = 1, cx = 1, cy = 1, label = false) {
    outer = [nx * GRID - CLEARANCE, ny * GRID - CLEARANCE];
    inner = cavity_size(nx, ny);
    inset = LIP_INSET + FALSE_FLOOR_FIT;
    rim = 1.2;
    side = DIVIDER_T / 2 + FALSE_FLOOR_FIT;   // tray edge to divider centre line
    ring_d = LED_PCB_D + 2 * LED_FIT;
    render(convexity = 4)
        for (a = [0 : cx - 1], b = [0 : cy - 1]) {
            x0 = comp_edge(a, cx, inner.x) + (a > 0 ? side : -1);
            x1 = comp_edge(a + 1, cx, inner.x) - (a < cx - 1 ? side : -1);
            y0 = comp_edge(b, cy, inner.y) + (b > 0 ? side : -1);
            y1 = label ? comp_edge(b + 1, cy, inner.y) - LABEL_DEPTH - FALSE_FLOOR_FIT
                       : comp_edge(b + 1, cy, inner.y) - (b < cy - 1 ? side : -1);
            lim = outer / 2 - [inset, inset];
            mid = [(max(x0, -lim.x) + min(x1, lim.x)) / 2, (max(y0, -lim.y) + min(y1, lim.y)) / 2];
            translate([0, 0, FLOOR_Z]) {
                linear_extrude(BAY_TOP - FLOOR_Z) difference() {
                    tray_outline(outer, inset, x0, x1, y0, y1);
                    offset(delta = -rim) tray_outline(outer, inset, x0, x1, y0, y1);
                }
                translate([0, 0, BAY_TOP - FLOOR_Z]) linear_extrude(FALSE_FLOOR_T)
                    tray_outline(outer, inset, x0, x1, y0, y1);
            }
            translate([mid.x, mid.y, BAY_TOP - LED_HOLDER_H])
                difference() {
                    cylinder(d = ring_d + 2 * LED_HOLDER_T, h = LED_HOLDER_H + EPS);
                    translate([0, 0, -EPS]) cylinder(d = ring_d, h = LED_HOLDER_H + 1);
                    translate([-1.5, 0, -EPS]) cube([3, ring_d, LED_HOLDER_H + 1]);   // wire exit
                }
        }
}

// Clear sleeves: one piece per compartment with a hole for the jar. Each stands on its
// false floor; the light travels up the clear walls and the top edge glows round the jar.
// Hollow, to save filament: a thin base, an outer wall and a ring round the jar.
// The printable front end is parts/jar_sleeve.scad.
module smart_bin_sleeve(nx = 1, ny = 1, uz = 3, cx = 1, cy = 1, jar_d = JAR_D) {
    outer = [nx * GRID - CLEARANCE, ny * GRID - CLEARANCE];
    inner = cavity_size(nx, ny);
    inset = LIP_INSET + FALSE_FLOOR_FIT;
    side = DIVIDER_T / 2 + FALSE_FLOOR_FIT;
    hole = jar_d + 2 * JAR_FIT;
    lim = outer / 2 - [inset, inset];   // the sleeve cannot reach past the false-floor outline
    render(convexity = 4)
        for (a = [0 : cx - 1], b = [0 : cy - 1]) {
            x0 = comp_edge(a, cx, inner.x) + (a > 0 ? side : -1);
            x1 = comp_edge(a + 1, cx, inner.x) - (a < cx - 1 ? side : -1);
            y0 = comp_edge(b, cy, inner.y) + (b > 0 ? side : -1);
            y1 = comp_edge(b + 1, cy, inner.y) - (b < cy - 1 ? side : -1);
            bx = [max(x0, -lim.x), min(x1, lim.x)];
            by = [max(y0, -lim.y), min(y1, lim.y)];
            assert(min(bx[1] - bx[0], by[1] - by[0]) - hole >= 2 * SLEEVE_MIN,
                   "Compartment too small for a sleeve round this jar");
            mid = [(bx[0] + bx[1]) / 2, (by[0] + by[1]) / 2];
            translate([0, 0, FLOOR_TOP]) difference() {
                linear_extrude(uz * UNIT_Z - FLOOR_TOP) difference() {
                    tray_outline(outer, inset, x0, x1, y0, y1);
                    translate(mid) circle(d = hole);
                }
                translate([0, 0, SLEEVE_BASE]) linear_extrude(uz * UNIT_Z) difference() {
                    offset(delta = -SLEEVE_WALL) tray_outline(outer, inset, x0, x1, y0, y1);
                    translate(mid) circle(d = hole + 2 * SLEEVE_WALL);
                }
            }
        }
}

module tray_outline(outer, inset, x0, x1, y0, y1) {
    intersection() {
        rounded_rect(outer - 2 * [inset, inset], BIN_R - inset);
        translate([x0, y0]) square([x1 - x0, y1 - y0]);
    }
}

// Recess for the bin board, the pocket above it for its parts, and the cable hole.
module foot_board_cut() {
    translate([0, 0, -EPS]) cylinder(d = BIN_BOARD_D + 2 * BIN_BOARD_FIT, h = BIN_BOARD_T - PAD_PROUD + EPS);
    cylinder(d = PARTS_POCKET_D, h = PARTS_POCKET_TOP);
    // wider over one arc, toward the back of the bin, for the board's LED solder pads
    translate([0, 0, BIN_BOARD_T - PAD_PROUD]) linear_extrude(PARTS_POCKET_TOP - BIN_BOARD_T + PAD_PROUD)
        intersection() {
            circle(r = PAD_NOTCH_R);
            polygon([[0, 0], for (a = [90 - PAD_NOTCH_ANGLE / 2 : 5 : 90 + PAD_NOTCH_ANGLE / 2]) 30 * [cos(a), sin(a)]]);
        }
    cylinder(d = CABLE_HOLE_D, h = FLOOR_Z + EPS);
}

// Stand-in for the bin board, for fit checks only.
module bin_board_ghost() {
    translate([0, 0, -PAD_PROUD]) cylinder(d = BIN_BOARD_D, h = BIN_BOARD_T);
}

// Slots that free a sprung beam in the +Y side of the foot.
module latch_cuts() {
    half = LATCH_LEN / 2;
    inner = FOOT_BAND - LATCH_T - LATCH_GAP;
    translate([-half, inner, -EPS]) cube([LATCH_LEN + 0.8, LATCH_GAP, 3.2]);          // behind the beam
    translate([half, inner, -EPS]) cube([0.8, LATCH_T + LATCH_GAP + 1, 3.2]);         // free end
    translate([-half, inner, 2.6]) cube([LATCH_LEN + 0.8, LATCH_T + LATCH_GAP + 3, 0.6]);  // above the beam
}

// Bump at the free end of the beam; it clicks into the groove in the socket wall.
module latch_bump() {
    translate([LATCH_LEN / 2 - 4, 0, 0]) rotate([90, 0, 90]) linear_extrude(3)
        polygon([
            [FOOT_BAND - EPS, GROOVE_Z - 0.75],
            [FOOT_BAND + LATCH_BUMP, GROOVE_Z - 0.2],
            [FOOT_BAND + LATCH_BUMP, GROOVE_Z + 0.2],
            [FOOT_BAND - EPS, GROOVE_Z + 0.75],
        ]);
}
