// Fit checks: each `test` is the intersection of two parts that must NOT overlap.
// tests/fit.sh exports every test; an empty result means the parts clear each other.
include <../lib/constants.scad>
include <../lib/smart.scad>
use <../lib/profile.scad>
use <../parts/smart_base.scad>
use <../parts/smart_bin.scad>
use <../parts/power_bin.scad>
use <../parts/tile_key.scad>
use <../parts/drawer_unit.scad>

test = "foot_in_socket";
FLOOR_TOP = BAY_TOP + FALSE_FLOOR_T;

if (test == "foot_in_socket") intersection() { smart_base(2, 2); translate([-GRID / 2, -GRID / 2, 0]) smart_bin_body(1, 1, 3); }
if (test == "foot_rotated")   intersection() { smart_base(2, 2); translate([-GRID / 2, -GRID / 2, 0]) rotate(90) smart_bin_body(1, 1, 3); }
if (test == "bin_2x1_on_tile") intersection() { smart_base(2, 2); translate([0, -GRID / 2, 0]) smart_bin_body(2, 1, 3, 2, 1); }
if (test == "bin_across_tiles") intersection() {
    union() { translate([-GRID, 0, 0]) smart_base(2, 2); translate([GRID, 0, 0]) smart_base(2, 2); }
    translate([0, -GRID / 2, 0]) smart_bin_body(2, 1, 3);
}
if (test == "floor_in_bin")   intersection() { smart_bin_body(2, 2, 5, 2, 2); smart_bin_floor(2, 2, 2, 2); }
if (test == "floor_passes_lip") intersection() {   // floor lifted to the height of the lip
    smart_bin_body(2, 2, 5, 1, 1); translate([0, 0, 5 * UNIT_Z - FLOOR_TOP + 2]) smart_bin_floor(2, 2, 1, 1);
}
if (test == "floor_in_label_bin") intersection() { smart_bin_body(2, 2, 4, 2, 2, true); smart_bin_floor(2, 2, 2, 2, true); }
if (test == "floor_passes_label_tab") intersection() {
    smart_bin_body(2, 2, 4, 2, 2, true); translate([0, 0, 4 * UNIT_Z - FLOOR_TOP + 2]) smart_bin_floor(2, 2, 2, 2, true);
}
if (test == "bin_on_label_bin") intersection() { smart_bin_body(1, 1, 3, 1, 1, true); translate([0, 0, 3 * UNIT_Z]) smart_bin_body(1, 1, 3); }
if (test == "sleeve_in_bin")  intersection() {
    union() { smart_bin_body(2, 2, 5, 2, 2); smart_bin_floor(2, 2, 2, 2); }
    smart_bin_sleeve(2, 2, 5, 2, 2, JAR_D);
}
if (test == "bin_on_bin")     intersection() { smart_bin_body(1, 1, 3); translate([0, 0, 3 * UNIT_Z]) smart_bin_body(1, 1, 3); }
if (test == "board_in_power_bin") intersection() { power_bin_body(4); power_board_ghost(); }
if (test == "lid_in_power_bin") intersection() { power_bin_body(4); power_bin_lid(4); }
module seated_power_bin(turn) { translate([GRID / 2, GRID / 2, 0]) rotate(turn) { power_bin_body(4); feed_heads(); } }
if (test == "power_bin_seated")      intersection() { smart_base(2, 2, power = true); seated_power_bin(0); }
if (test == "power_bin_half_turn")   intersection() { smart_base(2, 2, power = true); seated_power_bin(180); }
if (test == "power_bin_quarter_turn_blocked") intersection() { smart_base(2, 2, power = true); seated_power_bin(90); }
if (test == "power_bin_on_normal_cell_blocked") intersection() { smart_base(2, 2, power = true); translate([-GRID, -GRID, 0]) seated_power_bin(0); }
if (test == "normal_bin_on_power_cell") intersection() { smart_base(2, 2, power = true); translate([GRID / 2, GRID / 2, 0]) smart_bin_body(1, 1, 3); }
if (test == "tiles_side_by_side") intersection() { translate([-GRID, 0, 0]) smart_base(2, 2); translate([GRID * 1.5, GRID / 2, 0]) smart_base(3, 3); }
if (test == "key_in_tiles")   intersection() {
    union() { translate([-GRID, 0, 0]) smart_base(2, 2); translate([GRID, 0, 0]) smart_base(2, 2); }
    translate([0, -GRID / 2 + KEY_OFFSET, -UNDER_H]) rotate(-90) tile_key();
}
if (test == "bin_board_in_foot") intersection() { smart_bin_body(1, 1, 3); bin_board_ghost(); }
if (test == "tile_4x4_and_bin") intersection() { smart_base(4, 4); translate([-GRID * 1.5, -GRID * 1.5, 0]) smart_bin_body(1, 1, 3); }
if (test == "drawer_closed")  intersection() {
    union() { drawer_shell(4, 3, 13); drawer_shell_floor(4, 3, 3, 2); }
    union() { drawer_body(4, 3, 13, 3, 2); drawer_clear(4, 3, 13, 3, 2); }
}
if (test == "drawer_open")    intersection() {
    union() { drawer_shell(4, 3, 13); drawer_shell_floor(4, 3, 3, 2); }
    translate([0, -70, 0]) union() { drawer_body(4, 3, 13, 3, 2); drawer_clear(4, 3, 13, 3, 2); }
}
if (test == "drawer_floor_in_shell") intersection() { drawer_shell(4, 3, 13); drawer_shell_floor(4, 3, 3, 2); }
if (test == "drawer_unit_on_tile") intersection() { smart_base(4, 3); drawer_shell(4, 3, 13); }
if (test == "bin_on_drawer_unit") intersection() { drawer_shell(4, 3, 13); translate([-GRID * 1.5, -GRID, 13 * UNIT_Z]) smart_bin_body(1, 1, 3); }
// Control: this one MUST overlap, to prove the check can fail.
if (test == "control_overlap") intersection() { smart_base(2, 2); translate([-GRID / 2 + 3, -GRID / 2, 0]) smart_bin_body(1, 1, 3); }

// Row boards: everything that goes into the cavity must clear the tile (the pins pass
// through their holes), the edge connectors, and each other.
SIZES = [[2, 2, false], [4, 4, false], [4, 3, false], [3, 3, false], [2, 3, false], [2, 2, true], [2, 3, true], [4, 3, true]];
for (c = SIZES) {
    name = str(c[0], "x", c[1], c[2] ? "_starter" : "");
    if (test == str("fittings_in_", name)) intersection() { smart_base(c[0], c[1], c[2]); tile_fittings_ghost(c[0], c[1], c[2]); }
    if (test == str("fittings_vs_ports_", name)) intersection() { edge_connectors_ghost(c[0], c[1]); tile_fittings_ghost(c[0], c[1], c[2]); }
    if (test == str("main_vs_rest_", name)) intersection() {
        main_board_ghost(c[0], c[1]);
        union() { row_strips_ghost(c[0], c[1], c[2]); link_cables_ghost(c[0], c[1]); if (c[2]) feed_board_ghost(c[0], c[1]); }
    }
    if (test == str("strips_vs_rest_", name)) intersection() {
        row_strips_ghost(c[0], c[1], c[2]);
        union() { link_cables_ghost(c[0], c[1]); if (c[2]) feed_board_ghost(c[0], c[1]); }
    }
}
// Control: a row strip 1 mm out of place MUST collide (its pins miss their holes).
if (test == "strip_shifted_blocked") intersection() { smart_base(2, 2); translate([1, 0, 0]) row_strips_ghost(2, 2); }
// A bin on a tile with all fittings in place: the pins are the only thing it may touch.
if (test == "fittings_under_bin") intersection() {
    translate([-GRID / 2, -GRID / 2, 0]) smart_bin_body(1, 1, 3);
    difference() { tile_fittings_ghost(2, 2); translate([-100, -100, -0.01]) cube([200, 200, 5]); }
}
