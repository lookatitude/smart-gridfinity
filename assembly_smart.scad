// Powered system, first test set: two 2x2 tiles joined edge to edge,
// a 2x1 bin, two 1x1 bins and the power bin.
// view: "set" whole set, "tile" / "under" one tile, "bin" one bin with its false floor lifted,
// "foot" a 2x1 bin from below, "controller" the power bin with its lid lifted,
// "compartments" three bins split into compartments.
include <lib/constants.scad>
include <lib/smart.scad>
use <lib/profile.scad>
use <parts/smart_base.scad>
use <parts/smart_bin.scad>
use <parts/power_bin.scad>
use <parts/tile_key.scad>
use <parts/drawer_unit.scad>

view = "set";   // [set, tile, under, bin, foot, controller, compartments, floor, sleeves, joint, collection, drawers, powerfoot, label, allparts, drawerparts, boards]

module smart_bin(nx, ny, uz, body = "orange", lift = 0, cx = 1, cy = 1, label = false) {
    color(body) smart_bin_body(nx, ny, uz, cx, cy, label);
    translate([0, 0, lift]) color("white", 0.8) smart_bin_floor(nx, ny, cx, cy, label);
}

// Bins with label tabs: a 2x1 in two compartments, floors lifted, and a 1x1.
if (view == "label") {
    translate([-GRID * 0.9, 0, 0]) smart_bin(2, 1, 4, "gold", lift = 26, cx = 2, label = true);
    translate([GRID * 1.1, 0, 0]) smart_bin(1, 1, 4, "tomato", label = true);
}

if (view == "compartments") {
    translate([-GRID * 1.6, 0, 0]) smart_bin(2, 1, 3, "gold", cx = 3);
    translate([GRID * 0.2, 0, 0]) smart_bin(1, 1, 3, "tomato", cx = 2, cy = 2);
    translate([GRID * 2, 0, 0]) smart_bin(2, 2, 3, "steelblue", cx = 2, cy = 2);
}

module controller(lift = 0) {   // the power bin
    color("#444") power_bin_body(4);
    color("goldenrod") feed_heads();
    translate([0, 0, lift]) color("#666") power_bin_lid(4);
}

if (view == "set") {
    color("dimgray") translate([-GRID, 0, 0]) smart_base(2, 2);
    color("slategray") translate([GRID, 0, 0]) smart_base(2, 2, power = true);
    translate([-GRID, -GRID / 2, 0]) smart_bin(2, 1, 3, "gold", cx = 2);
    translate([-GRID * 1.5, GRID / 2, 0]) smart_bin(1, 1, 4, "tomato", label = true);
    translate([GRID * 0.5, -GRID / 2, 0]) smart_bin(1, 1, 4, "steelblue", label = true);
    translate([GRID * 1.5, GRID / 2, 0]) controller();
}

if (view == "tile") color("dimgray") smart_base(2, 2);

if (view == "under") color("dimgray") rotate([180, 0, 0]) smart_base(2, 2);

if (view == "bin") smart_bin(1, 1, 3, "orange", lift = 30);

if (view == "floor") rotate([180, 0, 0]) color("white", 0.8) smart_bin_floor(2, 2, 2, 2);

if (view == "foot") rotate([180, 0, 0]) {
    color("gold") smart_bin_body(2, 1, 3);
}

if (view == "controller") rotate([0, 0, 0]) {
    color("slategray") smart_base(2, 2, power = true);
    translate([GRID / 2, GRID / 2, 26]) controller(lift = 14);
}

// The power bin from below, showing the four screw heads.
if (view == "powerfoot") rotate([180, 0, 0]) { color("#444") power_bin_body(4); color("goldenrod") feed_heads(); }

// Jar bins.
// Left: 2x2 cells, 5 units high, four compartments with clear sleeves, for the 20 ml paint jars.
// Middle: 2x1 cells, 7 units high, two compartments, for the two 60 ml cleaner bottles;
// they nearly fill their compartments, so there is no sleeve.
// Right: 4x3 cells, 8 units high (56 mm), six compartments with sleeves, for the 210 ml bottles.
if (view == "sleeves") {
    floor_top = BAY_TOP + FALSE_FLOOR_T + 0.1;
    translate([-GRID * 4.2, 0, 0]) {
        smart_bin(2, 2, 5, "steelblue", cx = 2, cy = 2);
        color("white", 0.8) smart_bin_sleeve(2, 2, 5, 2, 2, JAR_D);
        for (p = [[-1, -1], [1, 1]]) translate([p.x * 19.9, p.y * 19.9, floor_top])
            color("dimgray") cylinder(d = JAR_D, h = JAR_H, $fn = 64);
    }
    translate([-GRID * 1.8, 0, 0]) {
        smart_bin(2, 1, 7, "seagreen", cx = 2);
        translate([19.9, 0, floor_top]) color("dimgray") cylinder(d = CLEANER_D, h = CLEANER_H, $fn = 64);
    }
    translate([GRID * 1.6, 0, 0]) {
        smart_bin(4, 3, 8, "indianred", cx = 3, cy = 2);
        color("white", 0.8) smart_bin_sleeve(4, 3, 8, 3, 2, BOTTLE_D);
        for (p = [[-1, -1], [0, 1], [1, -1]]) translate([p.x * 54.7, p.y * 30.4, floor_top])
            color("dimgray") cylinder(d = BOTTLE_D, h = BOTTLE_H, $fn = 64);
    }
}

// Two tiles of different sizes from below, pulled apart, with the bow-tie keys that lock them.
if (view == "joint") rotate([180, 0, 0]) {
    color("dimgray") translate([-GRID - 6, 0, 0]) smart_base(2, 2);
    color("slategray") translate([GRID * 1.5 + 6, GRID / 2, 0]) smart_base(3, 3);
    for (y = [-GRID / 2, GRID / 2]) translate([0, y + KEY_OFFSET, -UNDER_H]) rotate(-90)
        color("orange") tile_key();
}

// The whole collection, laid out exactly as in tests/grid_sim.py: 12 x 6 cells on eight
// tiles of three sizes. Cell (0, 0) is front left.
module at(cx, cy, w, h) { translate([(cx + w / 2) * GRID, (cy + h / 2) * GRID, 0]) children(); }
if (view == "collection") translate([-6 * GRID, -3 * GRID, 0]) {
    for (row = [0, 3]) {
        color("dimgray")   at(0, row, 4, 3) smart_base(4, 3);
        color("slategray") at(4, row, 3, 3) smart_base(3, 3);
        color("dimgray")   at(7, row, 3, 3) smart_base(3, 3);
        color("slategray") at(10, row, 2, 3) smart_base(2, 3, power = (row == 3));
    }
    at(0, 0, 4, 3) smart_bin(4, 3, 8, "indianred", cx = 3, cy = 2);
    for (p = [[4, 0], [6, 0], [8, 0], [10, 0], [4, 2], [6, 2], [8, 2], [10, 2], [0, 4], [2, 4], [4, 4], [6, 4]])
        at(p.x, p.y, 2, 2) smart_bin(2, 2, 5, "steelblue", cx = 2, cy = 2);
    at(0, 3, 2, 1) smart_bin(2, 1, 7, "seagreen", cx = 2);
    at(2, 3, 2, 1) smart_bin(2, 1, 10, "goldenrod", cx = 2);
    at(11, 5, 1, 1) controller();
}

// Three 4x3 drawer units side by side on three 4x3 tiles, plus a 2x3 tile for the controller.
// The middle drawer is pulled out.
module drawer_unit(open = 0) {
    color("slategray") drawer_shell(4, 3, 13);
    color("gainsboro") drawer_shell_floor(4, 3, 3, 2);
    translate([0, -open, 0]) {
        color("orange") drawer_body(4, 3, 13, 3, 2);
        color("white", 0.8) drawer_clear(4, 3, 13, 3, 2);
    }
}
if (view == "drawers") translate([-7 * GRID, -1.5 * GRID, 0]) {
    for (k = [0 : 2]) {
        color(k % 2 ? "slategray" : "dimgray") at(4 * k, 0, 4, 3) smart_base(4, 3);
        at(4 * k, 0, 4, 3) drawer_unit(k == 1 ? 75 : 0);
    }
    color("slategray") at(12, 0, 2, 3) smart_base(2, 3, power = true);
    at(13, 2, 1, 1) controller();
    at(12, 0, 2, 1) smart_bin(2, 1, 10, "goldenrod", cx = 2);
}

// One tile with one of its cells picked out, to explain the two words.
if (view == "tile_vs_cell") {
    color("dimgray") smart_base(2, 2);
    color("orange") translate([GRID / 2, GRID / 2, 0.05])
        linear_extrude(SOCKET_H + 0.1) difference() {
            rounded_rect([GRID - 0.2, GRID - 0.2], SOCKET_R);
            rounded_rect([GRID - 4.4, GRID - 4.4], 2);
        }
    color("orange", 0.55) translate([GRID / 2, GRID / 2, 0.05])
        linear_extrude(0.3) rounded_rect([GRID - 4.4, GRID - 4.4], 2);
}

// Every printed part, laid out separately with its name: base and bins, then the drawer unit.
TAG_COLOR = "#e9eef3";   // light: the pictures are shown on a dark page
module tag(t, dy = -52) { color(TAG_COLOR) translate([0, dy, 0]) linear_extrude(0.6) text(t, size = 8, halign = "center", font = "Liberation Sans:style=Bold"); }
if (view == "allparts") {
    translate([0, 0, UNDER_H]) color("dimgray") smart_base(2, 2);                      tag("tile 2x2", -56);
    translate([105, 0, 0]) { translate([0, 0, UNDER_H]) color("slategray") smart_base(2, 2, power = true); tag("starter tile", -56); }
    translate([185, 0, 0]) { for (y = [-10, 10]) translate([0, y, 0]) color("orange") tile_key(); tag("keys", -34); }
    translate([245, 0, 0]) { color("tomato") smart_bin_body(1, 1, 3); tag("bin 1x1", -34); }
    translate([305, 0, 0]) { translate([0, 0, 11.6]) rotate([180, 0, 0]) color("white", 0.85) smart_bin_floor(1, 1); tag("false floor", -34); }
    translate([0, -140, 0]) { color("gold") smart_bin_body(2, 1, 4, 2, 1, true); tag("bin 2x1, label tabs", -34); }
    translate([105, -140, 0]) { color("indianred") smart_bin_body(2, 1, 7, 2, 1); tag("tall bin 2x1", -34); }
    translate([215, -160, 0]) { color("steelblue") smart_bin_body(2, 2, 5, 2, 2); tag("paint bin 2x2", -56); }
    translate([320, -160, 0]) { translate([0, 0, -11.6]) color("white", 0.85) smart_bin_sleeve(2, 2, 5, 2, 2, JAR_D); tag("jar sleeves", -56); }
    translate([400, 0, 0]) { translate([0, 0, FEED_HEAD_H]) { color("#444") power_bin_body(4); color("goldenrod") feed_heads(); } tag("power bin", -34); }
    translate([400, -140, 0]) { translate([0, 0, -28]) color("#666") power_bin_lid(4); tag("power bin lid", -34); }
}
if (view == "drawerparts") {
    color("slategray") drawer_shell(4, 3, 13); tag("drawer shell", -82);
    translate([200, 0, 0]) { translate([0, 0, 11.6]) rotate([180, 0, 0]) color("gainsboro") drawer_shell_floor(4, 3, 3, 2); tag("shell floor", -82); }
    translate([400, 0, 0]) { translate([0, 0, -11.9]) { color("orange") drawer_body(4, 3, 13, 3, 2); color("white", 0.85) drawer_clear(4, 3, 13, 3, 2); } tag("drawer", -82); }
}

// A tile from below with everything that goes into its cavity. The boards are stand-ins:
// green = first row's board with the electronics, gold = strips of the further rows,
// white = flat cables, orange = feed board of the power cell, blue = edge connectors.
module fitted_tile(nx, ny, power) rotate([180, 0, 0]) {
    color("dimgray") smart_base(nx, ny, power = power);
    color("seagreen") main_board_ghost(nx, ny);
    color("goldenrod") row_strips_ghost(nx, ny, power);
    color("white") link_cables_ghost(nx, ny);
    if (power) color("darkorange") feed_board_ghost(nx, ny);
    color("steelblue") edge_connectors_ghost(nx, ny);
}
if (view == "boards") fitted_tile(2, 2, true);
if (view == "boards_big") fitted_tile(4, 3, false);
// The two row boards on their own, pin side up, at full length.
if (view == "rowboards") {
    color("seagreen") translate([0, 0, 0]) main_board_ghost(1, 1);
    color("goldenrod") translate([0, -40, 0]) row_strip_ghost(4);
}
