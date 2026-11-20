// Frames for the introduction animation (docs/intro.gif). One frame per value of f:
//   starter tile -> two more tiles slide in and connect -> power bin -> bins drop in
//   -> each bin is identified -> two compartments are called and light up.
// Every part is named by a tag as it arrives, and everything stands on a gridded surface.
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

// A tag that floats above a part and faces the camera. Teal tags are IDs the base has read;
// pale tags name a part as it arrives; amber marks the compartment that was asked for.
module tag(label, z, w = 34, bg = "#0b6f85", fg = "white", stalk = 28) {
    translate([0, 0, z]) rotate(CAM) {
        color(bg) linear_extrude(1) rounded_rect([w, 15], 3);
        color(fg) translate([0, 0, 1]) linear_extrude(0.6)
            text(label, size = 8, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
    }
    color(bg) translate([0, 0, z - stalk - 6]) cylinder(d = 1.6, h = stalk, $fn = 12);
}
module name(label, z, w) { tag(label, z, w, "#e9eef3", "#0c1117", 24); }

// The surface everything stands on, with the 42 mm Gridfinity grid drawn on it.
module ground(cx = 8, cy = 4) translate([-GRID, 0, -UNDER_H]) {
    color("#1f2a36") translate([0, 0, -1.5]) linear_extrude(1.5) square([cx * GRID + 24, cy * GRID + 24], center = true);
    color("#41556b") linear_extrude(0.25) {
        for (i = [0 : cx]) translate([(i - cx / 2) * GRID, 0]) square([0.9, cy * GRID], center = true);
        for (k = [0 : cy]) translate([0, (k - cy / 2) * GRID]) square([cx * GRID, 0.9], center = true);
    }
}
ground();

// A short line on the joint between two tiles, shown once they have connected.
module joined(x) { color("#18b6d6") translate([x, 0, SOCKET_H + 0.2]) cube([2.4, 2 * GRID - 6, 1.2], center = true); }

// ---- base -----------------------------------------------------------------------------
color("slategray") translate([GRID, 0, 0]) smart_base(2, 2, power = true);                 // starter tile
if (f <= 8) translate([GRID, 0, 0]) name("Starter tile", 46, 62);
if (f >= 3) color("dimgray") translate([-GRID + arrive(3, 8, -70), 0, 0]) smart_base(2, 2);
if (f >= 9) color("slategray") translate([-3 * GRID + arrive(9, 14, -70), 0, 0]) smart_base(2, 2);
if (f >= 3 && f <= 14) translate([-GRID + arrive(3, 8, -70), 0, 0]) name("Tile", 46, 30);
if (f >= 9 && f <= 14) translate([-3 * GRID + arrive(9, 14, -70), 0, 0]) name("Tile", 46, 30);
if (f >= 8 && f <= 20) joined(0);
if (f >= 14 && f <= 20) joined(-2 * GRID);

// ---- power bin, on the power cell (back right of the starter tile) -----------------------
if (f >= 15) translate([GRID * 1.5, GRID / 2, arrive(15, 20, 80)]) {
    color("#444") power_bin_body(4);
    color("goldenrod") feed_heads();
    color("#666") power_bin_lid(4);
    if (f <= 20) name("Power bin", 4 * UNIT_Z + 34, 54);
}

// ---- bins -----------------------------------------------------------------------------
// [x, y, cells x, cells y, units, colour, compartments x, compartments y, first frame, ID]
BINS = [[-GRID,       -GRID / 2, 2, 1, 3, "slateblue", 2, 1, 21, "3A"],
        [-3 * GRID,    0,        2, 2, 5, "steelblue", 2, 2, 26, "7F"],
        [-GRID * 1.5,  GRID / 2, 1, 1, 4, "tomato",    1, 1, 31, "C2"],
        [ GRID * 0.5, -GRID / 2, 1, 1, 4, "seagreen",  1, 1, 36, "19"]];
for (k = [0 : len(BINS) - 1]) {
    b = BINS[k];
    if (f >= b[8]) translate([b[0], b[1], arrive(b[8], b[8] + 4, 70)]) {
        bin(b[2], b[3], b[4], b[5], b[6], b[7]);
        if (f <= b[8] + 4) name("Bin", b[4] * UNIT_Z + 30, 28);
    }
    if (f >= 41 + k && f <= 45) translate([b[0], b[1], 0]) tag(str("ID ", b[9]), b[4] * UNIT_Z + 42, 44);
}

// ---- called: one compartment of the gold bin, then one of the blue bin -------------------
if (f == 46 || f == 48 || f == 49 || f >= 54)
    translate([BINS[0][0], BINS[0][1], 0]) { glow(2, 1, 3, 2, 1, 1, 0); translate([GRID / 2, 0, 0]) tag("Found", 3 * UNIT_Z + 44, 42, "#ffc94a", "#0c1117"); }
if (f == 50 || f == 52 || f == 53 || f >= 54)
    translate([BINS[1][0], BINS[1][1], 0]) { glow(2, 2, 5, 2, 2, 0, 1); translate([-GRID / 2, GRID / 2, 0]) tag("Found", 5 * UNIT_Z + 44, 42, "#ffc94a", "#0c1117"); }
