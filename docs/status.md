# Status and open questions

**The project is at design stage.** Nothing has been printed, no board has been ordered,
no person has reviewed the boards, and there is no firmware or software.

What exists is a design whose parts agree with each other: the 3D models, the circuit
boards and the bought-part specifications are tied together by automatic checks. This page
says what those checks cover, and what they cannot.

## At a glance

| Area | State |
|---|---|
| 3D models | Complete for the parts listed in the [parts guide](parts-guide.md). Build without warnings. Not printed |
| Circuit boards | Five boards drawn and routed. Pass KiCad's rule checks. Not reviewed, not ordered |
| Bought parts | Specified, with quantities. Key parts checked against data sheets. Nothing bought |
| Firmware (tiles, hub) | Does not exist |
| Software (the map, "find the yellow") | Does not exist |
| Physical tests | None |

## What was checked

How to run these yourself: [`tests/README.md`](../tests/README.md) and [`pcb/README.md`](../pcb/README.md).

| Check | Result |
|---|---|
| Pins against rings, with the bin off-centre in any direction | Correct up to 1.6 mm off-centre; the socket allows only 1.05 mm |
| Board clears the magnets in the bin foot | 0.63 mm of plastic left |
| Schematics and layouts, KiCad rule checks | All five boards: 0 errors, 0 warnings, 0 open connections |
| Row boards against the printed tile | Outline, pins, holes and sockets match within 0.05 mm |
| Signals: ID line, light commands, neighbour pin, 5 V and 24 V faults | All within limits in simulation |
| Finding every tile and bin from what the hardware can report | All 8 tiles and 16 bins of the full collection placed correctly, with one connector pair per joint |
| Power, full collection at 12 V | 5.4 W, 0.45 A; furthest tile still gets 11.87 V |
| Collisions between parts (62 fit checks) | None, in eight tile variants, with bins, drawer unit and power bin |
| Power bin the wrong way round or on a normal cell | Does not seat, as intended |
| Cable socket, converter, radio module and coil against data sheets | Four corrections made (socket width, cable current limit, coil value, surge diode) |

## Limits the design already knows about

- **Light brightness per cable.** One flat cable carries 0.7 A at 5 V, so firmware must hold
  full white to 11 lights behind any one cable. Lit the way an item is shown, 16 lights draw
  0.32 A.
- **Tile size.** At most 4 cells each way, at least 2×2.
- **Bin height.** At least 3 units, because the false floor takes 4.6 mm.
- **Stacked smart bins** keep the upper bin's latches pressed in.

## What the design does not settle

### Needs a first print or a first board

- **Opening sizes.** Spring pins, edge connectors, the DC socket and screw heads vary between
  sellers. Their openings in the model are estimates.
- **Contact reliability.** Four pins per cell over 72 cells is 288 contacts that all have to work.
- **Latch strength on a wall.** The snap latch engages by about 0.5 mm. Whether that holds a
  loaded bin is unknown.
- **Glow around a jar.** The clear sleeve has to carry light up 23 to 44 mm. Brightness is untested.
- **Snapping a row strip shorter.** It cuts through 5 V and ground copper 0.7 mm apart, on a
  6 mm wide strip. A board maker has not been asked whether they will score it.
- **Cable socket latch.** It needs a fingertip between two rows 21.5 mm apart. Not tried by hand.
- **Room under the radio module.** At its tallest it ends 0.25 mm above the tile's underside.
- **Drawer units on a table.** Pulling a drawer drags the shell forward; the drawer has no end stop yet.
- **Printing.** Tiles need supports under the socket floor, and a 0.4 mm nozzle.

### Needs a person to review

- **Nobody has reviewed the boards.** Passing automatic checks does not make a board correct.
- **The first-row board was routed by an automatic router,** with tracks as close as 0.125 mm.
- **5 V copper is thin in places** on the first-row board: 0.8 mm at the cable socket, and on
  inner layers along the board.
- **Part values not yet checked against data sheets:** whether the ID chip tolerates 5 V on
  its data pin, the exact switch chip types, the LED timing limits, and the heights of the
  smaller parts.
- **The power bin's contacts** (brass screw heads on spring pins, up to 4 A) and its DC
  socket are a proposal.

### Needs firmware

- **A bin across two tiles** has one ID chip read by two tiles. They can talk over each
  other, so the firmware must retry.
- **Brightness cap** per cable, as above.
- **Everything about discovery and the map** is so far a simulation.

### Not designed yet

- **Edge-connector leads** are still a hand-soldered loom onto the first-row board: three
  leads per fitted connector, done on the bench.
- **Wall holders** for bottles: a bin on a wall faces outward, so paint bottles need a holder
  with the foot on its back.
- **Scoop fronts, drawer-plate padding, a second powered level on top of a drawer unit.**
- **Edge-connector keying** on cheap copies is unverified, and the connector carries up to 24 V.
- **Live pins in empty sockets.** A 5 V pin is exposed in every empty cell; each tile's
  converter limits the current.

## A sensible first build

The test set is sized to answer the most open questions with the least material: two 2×2
tiles (one a starter tile), a 2×1 bin, two 1×1 bins and the power bin. It exercises power
across a joint, tiles finding each other, a multi-cell bin, and both mounting orientations.
Quantities are in the [materials list](smart/parts.md).
