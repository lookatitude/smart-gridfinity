// Bow-tie key that locks two smart tiles together. Press one into each pair of facing
// pockets from the underside. Print flat, as modelled.
include <../lib/constants.scad>
include <../lib/smart.scad>
use <smart_base.scad>

tile_key();

module tile_key() {
    linear_extrude(KEY_H - 0.4) {
        key_half();
        mirror([0, 1, 0]) key_half();
    }
}
