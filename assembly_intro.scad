// Frames for the introduction animation (docs/intro.gif). One frame per value of f:
//   starter tile -> two more tiles slide in and connect -> power bin -> bins drop in
//   -> each bin is identified -> two compartments are called and light up.
// Build the GIF with tools/make_intro_gif.sh.
include <lib/constants.scad>
include <lib/smart.scad>
use <lib/profile.scad>
use <parts/smart_base.scad>
use <parts/smart_bin.scad>
use <parts/power_bin.scad>

f = 0;   // frame number, 0 to 54

function clamp(x) = min(1, max(0, x));
function prog(a, b) = clamp((f - a) / (b - a));          // 0 before frame a, 1 from frame b
function ease(p) = 1 - pow(1 - p, 2);                    // fast, then settling
function arrive(a, b, from) = from * (1 - ease(prog(a, b)));

CAM = [48, 0, 24];   // must match the camera angles in tools/make_intro_gif.sh
FLOOR_TOP = BAY_TOP + FALSE_FLOOR_T;

module bin(nx, ny, uz, body, cx = 1, cy = 1) {
    color(body) smart_bin_body(nx, ny, uz, cx, cy);
    color("white", 0.85) smart_bin_floor(nx, ny, cx, cy);
}

// The floor of one compartment glowing, and a faint column of light above it.
module glow(nx, ny, uz, cx, cy, ix, iy) {
    w = nx * GRID / cx; d = ny * GRID / cy;
    translate([-nx * GRID / 2 + (ix + 0.5) * w, -ny * GRID / 2 + (iy + 0.5) * d, 0]) {
        color("#ffe600") translate([0, 0, FLOOR_TOP + 0.3]) linear_extrude(0.6)
            square([w - 8, d - 8], center = true);
        color("#ffe600", 0.30) translate([0, 0, FLOOR_TOP + 1]) linear_extrude(uz * UNIT_Z - FLOOR_TOP + 6)
            square([w - 9, d - 9], center = true);
    }
}

// A tag that floats above a bin and faces the camera: the ID the base has read.
module tag(label, z) {
    translate([0, 0, z]) rotate(CAM) {
        color("#0b6f85") linear_extrude(1) rounded_rect([34, 15], 3);
        color("white") translate([0, 0, 1]) linear_extrude(0.6)
            text(label, size = 8, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
    }
    color("#0b6f85") translate([0, 0, z - 34]) cylinder(d = 1.6, h = 28, $fn = 12);
}

// A short line on the joint between two tiles, shown once they have connected.
module joined(x) { color("#18b6d6") translate([x, 0, SOCKET_H + 0.2]) cube([2.4, 2 * GRID - 6, 1.2], center = true); }

// ---- base -----------------------------------------------------------------------------
color("slategray") translate([GRID, 0, 0]) smart_base(2, 2, power = true);                 // starter tile
if (f >= 3) color("dimgray") translate([-GRID + arrive(3, 8, -70), 0, 0]) smart_base(2, 2);
if (f >= 9) color("slategray") translate([-3 * GRID + arrive(9, 14, -70), 0, 0]) smart_base(2, 2);
if (f >= 8 && f <= 20) joined(0);
if (f >= 14 && f <= 20) joined(-2 * GRID);

// ---- power bin, on the power cell (back right of the starter tile) -----------------------
if (f >= 15) translate([GRID * 1.5, GRID / 2, arrive(15, 20, 80)]) {
    color("#444") power_bin_body(4);
    color("goldenrod") feed_heads();
    color("#666") power_bin_lid(4);
}

// ---- bins -----------------------------------------------------------------------------
// [x, y, cells x, cells y, units, colour, compartments x, compartments y, first frame, ID]
BINS = [[-GRID,       -GRID / 2, 2, 1, 3, "slateblue", 2, 1, 21, "3A"],
        [-3 * GRID,    0,        2, 2, 5, "steelblue", 2, 2, 26, "7F"],
        [-GRID * 1.5,  GRID / 2, 1, 1, 4, "tomato",    1, 1, 31, "C2"],
        [ GRID * 0.5, -GRID / 2, 1, 1, 4, "seagreen",  1, 1, 36, "19"]];
for (k = [0 : len(BINS) - 1]) {
    b = BINS[k];
    if (f >= b[8]) translate([b[0], b[1], arrive(b[8], b[8] + 4, 70)]) bin(b[2], b[3], b[4], b[5], b[6], b[7]);
    if (f >= 41 + k && f <= 45) translate([b[0], b[1], 0]) tag(b[9], b[4] * UNIT_Z + 42);
}

// ---- called: one compartment of the gold bin, then one of the blue bin -------------------
if (f == 46 || f == 48 || f == 49 || f >= 54)
    translate([BINS[0][0], BINS[0][1], 0]) glow(2, 1, 3, 2, 1, 1, 0);
if (f == 50 || f == 52 || f == 53 || f >= 54)
    translate([BINS[1][0], BINS[1][1], 0]) glow(2, 2, 5, 2, 2, 0, 1);
