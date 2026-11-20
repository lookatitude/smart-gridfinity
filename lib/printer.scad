// Printer limits and the logic for splitting large parts to fit the bed.
// Values are for a Bambu Lab P2S; change them here if the printer changes.
include <constants.scad>

BED        = [256, 256, 256];   // build volume, mm
BED_MARGIN = 5;                 // space kept free at each bed edge (5 -> 5x5 cells max, 2 -> 6x6)

// Largest number of whole grid cells that fit along one bed axis (0 = X, 1 = Y).
function max_cells(axis) = floor((BED[axis] - 2 * BED_MARGIN) / GRID);

// True when a part of the given [x, y, z] size fits the bed.
function fits_bed(size) =
    size.x <= BED.x - 2 * BED_MARGIN &&
    size.y <= BED.y - 2 * BED_MARGIN &&
    (len(size) < 3 || size.z <= BED.z);

// Split n cells into the fewest runs of at most `limit` cells, as evenly as possible.
// split_cells(13, 5) -> [5, 4, 4]
function split_cells(n, limit) =
    let (count = ceil(n / limit), base = floor(n / count), extra = n - base * count)
    [for (i = [0 : count - 1]) base + (i < extra ? 1 : 0)];

// Sum of the first `count` entries of a list.
function sum_first(v, count) = count <= 0 ? 0 : v[count - 1] + sum_first(v, count - 1);
