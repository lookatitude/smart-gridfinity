// Powered base tile. z = 0 is the socket floor the bin foot rests on;
// the wiring cavity hangs below it and is open at the back.
// Each socket has four spring pins (ID, LED data, 5 V, ground) and four holding magnets.
include <../lib/constants.scad>
include <../lib/smart.scad>
include <../lib/printer.scad>
use <../lib/profile.scad>

/* [Smart base] */
cells_x = 2;
cells_y = 2;
power_cell = false;   // starter tile: the back right cell takes the power bin

assert(fits_bed([cells_x * GRID, cells_y * GRID]), "Tile is larger than the printer bed");
assert(cells_x * cells_y <= MAX_TILE_CELLS,
       "A smart tile can have at most 16 cells: use several tiles");
assert(cells_x >= 2 && cells_y >= 2, "A smart tile needs at least 2 x 2 cells: the first row's board reaches under the second row");
assert(cells_x <= MAX_TILE_SIDE && cells_y <= MAX_TILE_SIDE, "A smart tile is at most 4 cells each way: the row boards are four cells long");

smart_base(cells_x, cells_y, power_cell);

module smart_base(nx = 2, ny = 2, power = false) {
    size = [nx * GRID, ny * GRID];

    render(convexity = 8) difference() {
        translate([0, 0, -UNDER_H])
            linear_extrude(UNDER_H + SOCKET_H) rounded_rect(size, SOCKET_R);

        grid_copies(nx, ny) cell_top_cuts();
        cavity(nx, ny, power);
        for (i = [0 : nx - 1], j = [0 : ny - 1]) translate(base_cell(i, j, nx, ny))
            if (power && i == nx - 1 && j == ny - 1) power_cell_cuts(); else cell_through_cuts();
        edge_ports(nx, ny);
        edge_cells(nx, ny) key_pocket();
        // pilot hole for the third screw of the first row's board
        translate(base_cell(0, 0, nx, ny)) translate([MAIN_SCREW.x, MAIN_SCREW.y, CELL_BOARD_Z - EPS])
            cylinder(d = CELL_PILOT_D, h = -CELL_BOARD_Z - 0.6);
        foot_places(nx, ny) translate([0, 0, -UNDER_H - EPS])
            cylinder(d = FOOT_D, h = FOOT_RECESS + EPS);
    }
}

// Place children where the rubber feet go: on the screw post of each of the four corner cells.
module foot_places(nx, ny) {
    for (c = [[0, 0], [nx - 1, 0], [0, ny - 1], [nx - 1, ny - 1]])
        translate(base_cell(c[0], c[1], nx, ny)) translate([SCREW_POS.x, SCREW_POS.y, 0]) children();
}

function base_cell(i, j, nx, ny) = [(i - (nx - 1) / 2) * GRID, (j - (ny - 1) / 2) * GRID, 0];

// Power cell: four wells with a feed pin at the bottom of each, the pilot hole for the
// feed board's screw, and the wall-screw hole.
module power_cell_cuts() {
    for (x = FEED_X) translate([x, 0, 0]) {
        translate([0, 0, -FEED_WELL_DEPTH]) cylinder(d = FEED_WELL_D, h = FEED_WELL_DEPTH + EPS);
        translate([0, 0, -UNDER_H - EPS]) cylinder(d = PIN_HOLE_D, h = UNDER_H);
    }
    translate([0, 0, FEED_BOARD_Z - EPS]) cylinder(d = CELL_PILOT_D, h = -FEED_BOARD_Z - 0.6);
    translate([SCREW_POS.x, SCREW_POS.y, -UNDER_H - EPS]) cylinder(d = SCREW_D, h = UNDER_H + 2 * EPS);
}

// Place children at the middle of every outer cell edge, in a frame where +X runs along
// the edge in the same direction on facing edges and +Y points into the tile.
module edge_cells(nx, ny) {
    size = [nx * GRID, ny * GRID];
    for (i = [0 : nx - 1]) {
        x = (i - (nx - 1) / 2) * GRID;
        translate([x, -size.y / 2, 0]) children();
        translate([x, size.y / 2, 0]) mirror([0, 1, 0]) children();
    }
    for (j = [0 : ny - 1]) {
        y = (j - (ny - 1) / 2) * GRID;
        translate([-size.x / 2, y, 0]) multmatrix([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]]) children();
        translate([size.x / 2, y, 0]) multmatrix([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]]) children();
    }
}

// One half of the bow-tie key, as a 2D outline in the edge frame.
module key_half(grow = 0) {
    offset(delta = grow) polygon([
        [-KEY_ROOT / 2, -EPS], [KEY_ROOT / 2, -EPS], [KEY_TIP / 2, KEY_DEPTH], [-KEY_TIP / 2, KEY_DEPTH]]);
}

module key_pocket() {
    translate([KEY_OFFSET, 0, -UNDER_H - EPS]) linear_extrude(KEY_H + 0.3) key_half(KEY_FIT);
}

// Solid block left standing in the cavity round each pocket.
module key_block() {
    translate([KEY_OFFSET - KEY_TIP / 2 - KEY_WALL, 0, 0])
        cube([KEY_TIP + 2 * KEY_WALL, KEY_DEPTH + KEY_WALL, CAVITY_H + 1]);
}

// Socket, snap-ring groove and magnet pockets: everything cut from above.
module cell_top_cuts() {
    socket();
    translate([0, 0, SOCKET_H - EPS])
        linear_extrude(1) rounded_rect([GRID, GRID], SOCKET_R);

    inset = SOCKET_PROFILE[1][1] - GROOVE_DEPTH;
    translate([0, 0, GROOVE_Z - GROOVE_H / 2])
        linear_extrude(GROOVE_H)
            rounded_rect([GRID - 2 * inset, GRID - 2 * inset], SOCKET_R - inset);

    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * MAGNET_OFFSET, sy * MAGNET_OFFSET, -MAGNET_H])
            cylinder(d = MAGNET_D, h = MAGNET_H + EPS);
}

// Holes from below: the four pin holes through the floor, the blind pilot hole for the
// row board's screw, and the wall-screw hole.
module cell_through_cuts() {
    translate([0, 0, -UNDER_H - EPS]) {
        for (r = PIN_R) translate([r, 0, 0]) cylinder(d = PIN_HOLE_D, h = UNDER_H + 2 * EPS);
        translate([SCREW_POS.x, SCREW_POS.y, 0]) cylinder(d = SCREW_D, h = UNDER_H + 2 * EPS);
    }
    translate([CELL_SCREW_X, 0, CELL_BOARD_Z - EPS]) cylinder(d = CELL_PILOT_D, h = -CELL_BOARD_Z - 0.6);
}

// ---- Stand-ins for fit checks and pictures -------------------------------------------
// All are drawn in the frame of the tile; none is printed.
function row_cells(j, nx, ny, power) = (power && j == ny - 1) ? nx - 1 : nx;
function board_bottom() = CELL_BOARD_Z - CELL_BOARD_T;

module pins_ghost(n) {
    for (k = [0 : n - 1], r = PIN_R) translate([k * GRID + r, 0, CELL_BOARD_Z]) cylinder(d = 2.0, h = PIN_ABOVE_BOARD);
    for (k = [0 : n - 1]) translate([k * GRID + CELL_SCREW_X, 0, board_bottom() - 1.6]) cylinder(d = 3.8, h = 1.6);
}
module link_socket_ghost(side) {   // side = 1: mouth toward +y, -1: toward -y
    translate([LINK_X - LINK_SOCKET.x / 2, side > 0 ? TAB_Y - LINK_SOCKET.y : -TAB_Y, board_bottom() - LINK_SOCKET.z])
        cube(LINK_SOCKET);
}
// Outline of the first row's board, cut to n cells.
module main_shape(n) {
    intersection() {
        polygon(MAIN_OUTLINE);
        translate([-50, -50]) square([50 + (n - 1) * GRID + STRIP_END, 200]);
    }
}
module main_board_ghost(nx, ny) {
    translate(base_cell(0, 0, nx, ny)) {
        translate([0, 0, board_bottom()]) linear_extrude(CELL_BOARD_T) main_shape(nx);
        // the room its parts take, on the face that looks down
        translate([0, 0, board_bottom() - MAIN_PARTS_H]) linear_extrude(MAIN_PARTS_H) intersection() {
            offset(delta = -0.5) polygon(MAIN_OUTLINE);
            translate([-50, -50]) square([50 + MAIN_BODY_X, 200]);
        }
        pins_ghost(nx);
        translate([MAIN_SCREW.x, MAIN_SCREW.y, board_bottom() - MAIN_PARTS_H - 0.01]) cylinder(d = 3.8, h = 1);
    }
}
// Strip of one further row, with its two cable sockets and the switch chip on the tabs.
module row_strip_shape(n) {
    translate([STRIP_X0, -CELL_BOARD_W / 2]) square([(n - 1) * GRID + STRIP_END - STRIP_X0, CELL_BOARD_W]);
    translate([TAB_X[0], -TAB_Y]) square([TAB_X[1] - TAB_X[0], 2 * TAB_Y]);
}
module row_strip_ghost(n) {
    translate([0, 0, board_bottom()]) linear_extrude(CELL_BOARD_T) row_strip_shape(n);
    for (s = [-1, 1]) link_socket_ghost(s);
    // the switch chip and its capacitor, anywhere on the tabs clear of the screw
    translate([0, 0, board_bottom() - 1.3]) linear_extrude(1.3) difference() {
        translate([TAB_X[0] + 0.5, -TAB_Y + 0.5]) square([TAB_X[1] - TAB_X[0] - 1, 2 * TAB_Y - 1]);
        translate([CELL_SCREW_X, 0]) circle(d = 4.4);
    }
    pins_ghost(n);
}
module row_strips_ghost(nx, ny, power = false) {
    for (j = [1 : ny - 1]) translate(base_cell(0, j, nx, ny)) row_strip_ghost(row_cells(j, nx, ny, power));
}
// Flat cables from each row to the next, between the socket mouths, with room to bow.
module link_cables_ghost(nx, ny) {
    for (j = [0 : ny - 2]) translate(base_cell(0, j, nx, ny))
        translate([LINK_X - LINK_CABLE_W / 2, TAB_Y + 0.05, board_bottom() - 1.8])
            cube([LINK_CABLE_W, GRID - 2 * TAB_Y - 0.1, 1.6]);
}
module feed_board_ghost(nx, ny) {
    translate(base_cell(nx - 1, ny - 1, nx, ny)) {
        translate([FEED_BOARD_X[0], -CELL_BOARD_W / 2, FEED_BOARD_Z - CELL_BOARD_T])
            cube([FEED_BOARD_X[1] - FEED_BOARD_X[0], CELL_BOARD_W, CELL_BOARD_T]);
        translate([0, 0, FEED_BOARD_Z - CELL_BOARD_T - 1.6]) cylinder(d = 3.8, h = 1.6);
        for (x = FEED_X) translate([x, 0, FEED_BOARD_Z]) cylinder(d = 2.0, h = PIN_ABOVE_BOARD);
    }
}
// Bodies of the magnetic edge connectors, one in every port.
module edge_connectors_ghost(nx, ny) {
    edge_cells(nx, ny) translate([-7.5, 0, -UNDER_H]) cube([15, 4.2, 5.5]);
}
// Everything that goes into the cavity.
module tile_fittings_ghost(nx, ny, power = false) {
    main_board_ghost(nx, ny); row_strips_ghost(nx, ny, power); link_cables_ghost(nx, ny);
    if (power) feed_board_ghost(nx, ny);
}

// Wiring cavity, leaving ribs, the pin boss and screw posts standing.
module cavity(nx, ny, power = false) {
    size = [nx * GRID, ny * GRID];
    translate([0, 0, -UNDER_H - EPS]) difference() {
        linear_extrude(CAVITY_H + EPS)
            rounded_rect(size - 2 * [SKIRT_T, SKIRT_T], SOCKET_R - SKIRT_T);

        // Short ribs at every cell corner; the middle of each cell edge stays open for wiring.
        // The cross at the first inner corner is left out: the first row's board lies there.
        for (i = [0 : nx], j = [0 : ny]) if (!(i == 1 && j == 1))
            translate([(i - nx / 2) * GRID, (j - ny / 2) * GRID, 0]) {
                translate([-RIB_LEN, -RIB_T / 2, 0]) cube([2 * RIB_LEN, RIB_T, CAVITY_H + 1]);
                translate([-RIB_T / 2, -RIB_LEN, 0]) cube([RIB_T, 2 * RIB_LEN, CAVITY_H + 1]);
            }

        // boss the row board lies against under every cell (from the floor down to CELL_BOARD_Z)
        for (i = [0 : nx - 1], j = [0 : ny - 1]) if (!(power && i == nx - 1 && j == ny - 1))
            translate(base_cell(i, j, nx, ny))
                translate([CELL_BOARD_X[0], -CELL_BOARD_W / 2, UNDER_H + CELL_BOARD_Z + EPS])
                    cube([CELL_BOARD_X[1] - CELL_BOARD_X[0], CELL_BOARD_W, -CELL_BOARD_Z]);
        grid_copies(nx, ny)
            translate([SCREW_POS.x, SCREW_POS.y, 0]) cylinder(d = SCREW_POST_D, h = CAVITY_H + 1);
        edge_cells(nx, ny) key_block();
        foot_places(nx, ny) cylinder(d = FOOT_PAD_D, h = CAVITY_H + 1);
        // boss the feed board lies against, in the power cell
        if (power) translate(base_cell(nx - 1, ny - 1, nx, ny))
            translate([FEED_BOARD_X[0], -CELL_BOARD_W / 2, UNDER_H + FEED_BOARD_Z + EPS])
                cube([FEED_BOARD_X[1] - FEED_BOARD_X[0], CELL_BOARD_W, -FEED_BOARD_Z]);
        translate(base_cell(0, 0, nx, ny))
            translate([MAIN_SCREW.x, MAIN_SCREW.y, UNDER_H + CELL_BOARD_Z + EPS]) cylinder(d = 6, h = -CELL_BOARD_Z);
    }
}

// Openings in the skirt at the middle of every outer cell edge: tile-to-tile connector.
module edge_ports(nx, ny) {
    edge_cells(nx, ny)
        translate([-PORT_W / 2, -SKIRT_T, -UNDER_H - EPS]) cube([PORT_W, 2 * SKIRT_T, PORT_H + EPS]);
}
