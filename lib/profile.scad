// Shared geometry: the foot and socket shapes every part is built from.
include <constants.scad>

// 2D rectangle of the given outer size with rounded corners, centred on the origin.
module rounded_rect(size, r) {
    offset(r = r) square([size.x - 2 * r, size.y - 2 * r], center = true);
}

// Solid whose outline shrinks with height according to `profile`,
// a bottom-to-top list of [z, inset from `size`]. Corner radius follows the inset.
module stepped_solid(size, r, profile) {
    for (i = [0 : len(profile) - 2]) {
        a = profile[i];
        b = profile[i + 1];
        hull() {
            translate([0, 0, a[0]])
                linear_extrude(EPS) rounded_rect(size - 2 * [a[1], a[1]], r - a[1]);
            translate([0, 0, b[0] - EPS])
                linear_extrude(EPS) rounded_rect(size - 2 * [b[1], b[1]], r - b[1]);
        }
    }
}

// One bin foot, sitting on z = 0, centred on its cell.
module foot() {
    stepped_solid([GRID - CLEARANCE, GRID - CLEARANCE], BIN_R, FOOT_PROFILE);
}

// Negative volume a foot drops into. `size` is the full grid area it spans.
// With through = true it is extended above and below so it cuts clean through a plate.
module socket(size = [GRID, GRID], through = false) {
    lo = SOCKET_PROFILE[0];
    hi = SOCKET_PROFILE[len(SOCKET_PROFILE) - 1];
    profile = through
        ? concat([[lo[0] - 1, lo[1]]], SOCKET_PROFILE, [[hi[0] + 1, hi[1]]])
        : SOCKET_PROFILE;
    stepped_solid(size, SOCKET_R, profile);
}

// Repeat children once per cell of an nx-by-ny grid centred on the origin.
module grid_copies(nx, ny) {
    for (i = [0 : nx - 1], j = [0 : ny - 1])
        translate([(i - (nx - 1) / 2) * GRID, (j - (ny - 1) / 2) * GRID, 0])
            children();
}
