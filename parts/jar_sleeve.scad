// Clear sleeves that hold jars upright in a smart bin and carry the floor light up round
// each jar. Optional: print them as needed, in clear filament. Set the bin they go into
// and the jar diameter. One file holds one sleeve per compartment.
include <../lib/constants.scad>
include <../lib/smart.scad>
use <smart_bin.scad>

/* [Bin the sleeves go into] */
cells_x = 2;
cells_y = 2;
units_z = 5;
compartments_x = 2;
compartments_y = 2;

/* [Jar] */
jar_diameter = 25.1;   // 25.1 paint jar, 48.2 large bottle

color("white", 0.7)
    smart_bin_sleeve(cells_x, cells_y, units_z, compartments_x, compartments_y, jar_diameter);
