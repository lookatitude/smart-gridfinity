# Design checks

Nothing in this project has been built yet, so these checks are what stands behind the
design. They are calculations, simulations and collision tests on the 3D models. They do
not replace a physical test.

Run everything (needs Python 3 with numpy, and OpenSCAD):

    tests/run_all.sh

It stops at the first failure and prints `ALL CHECKS PASSED` at the end. The fit checks
take over ten minutes; the other three take seconds.

## The checks

| Script | Question it answers | How | Time |
|---|---|---|---|
| `contacts.py` | Does every spring pin stay on its own ring if the bin sits off-centre? Does the bin board clear the magnets? | Geometry calculation | seconds |
| `power.py` | Is any pin, converter or cable overloaded in the test set, the full collection, or a drawer row? | Current budget from part ratings | seconds |
| `grid_sim.py` | Can the hub place every tile and bin using only what the hardware can report? What voltage reaches the furthest tile? | Simulated layout and discovery; also writes `docs/smart/layout.svg` | seconds |
| `fit.sh` | Do any two parts collide? | Intersects pairs of models in OpenSCAD and measures the overlap | over 10 min |

### `contacts.py`

Sweeps the bin foot off-centre in every direction and reports where a pin first leaves its
ring or touches the next one. Current result: correct up to 1.6 mm off-centre, while the
socket only allows 1.05 mm of play.

### `power.py`

Prints one block per scenario: feed current at 12 V and 24 V, the busiest tile at full
white, and the current through a flat cable. A line ending in `firmware must cap` is a
limit the future firmware has to respect, not a failure.

### `grid_sim.py`

Lays out the full collection on eight tiles of three sizes, then runs the position
discovery the firmware would run. It is given only two kinds of report: "my port P touches
port Q of tile T" and "my cell N reads ID X". The discovered map must equal the true layout.

### `fit.sh` and `fit.scad`

Each test in `fit.scad` is the intersection of two things that must not share space. `fit.sh`
exports each one and measures its volume with `stlvol.py`. A check passes when the overlap
is under 0.05 mm³. There are 62 checks:

- **Bins and base:** a foot in a socket, a bin turned a quarter, a bin across two tiles, a
  false floor going in past the lip and past a label tab, bins stacked, sleeves in bins.
- **Power bin:** seated, seated half a turn round, and blocked a quarter turn round or on a
  normal cell.
- **Tiles:** side by side, and with a key in their pockets.
- **Inside the tile:** boards, cables, feed board and edge connectors in eight tile variants,
  each against the tile and against each other.
- **Drawer unit:** closed, open, on a tile, and with a bin on top.

Four checks **must** overlap: `control_overlap` and every check whose name ends in
`_blocked` (a strip shifted 1 mm, and the power bin a quarter turn round or on a normal
cell). They prove the method can detect a collision.

A small overlap is expected in `bin_on_bin`, `bin_on_label_bin` and `bin_on_drawer_unit`
(allowed up to 3 mm³): the sprung latch of the upper bin is pressed in by the lip below it,
and the model does not bend.

Run a single check:

    cd tests
    openscad -o /tmp/t.stl -D 'test="foot_in_socket"' fit.scad
    python3 -c "import stlvol; print(stlvol.measure('/tmp/t.stl')[0], 'mm3')"

An empty result ("top level object is empty") means no overlap at all.

## Checks that live elsewhere

The circuit boards have their own checks in `pcb/`: KiCad's rule checks, `check_rows.py`
(board positions against the model) and `signals.py` (signal levels and timing). See
[`pcb/README.md`](../pcb/README.md).

## Adding a fit check

1. Add an `if (test == "my_check") intersection() { partA(); partB(); }` line to `fit.scad`.
2. Add `my_check` to the list in `fit.sh`.
3. If the parts are meant to collide, end the name in `_blocked`: `fit.sh` then requires an
   overlap of more than 1 mm³.
