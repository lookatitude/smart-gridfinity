# Smart Gridfinity: materials list

Bins have no radio and no processor. Each bin foot holds a small passive board
with four contact rings and an ID chip. Each tile has one board under every row of cells,
with that row's spring pins already soldered on. The board of the first row also reads the
bins, drives their LEDs, makes 5 V and reports by radio. Power enters at 12-24 V through
a starter tile and a power bin. The boards and their records are in `pcb/`.

Nothing here has been bought or tested. Any brand is fine as long as the part meets the spec.
Sizes marked **measure first** vary between sellers: get the seller's drawing, or measure
the part when it arrives, and set the matching value in `lib/smart.scad` before printing.

## Custom boards

Ordered assembled and pre-flashed from a board maker. The electronic parts on each board are
listed in its `bom.csv`; you do not buy those separately.

| Board | Size | Layers | What is on it | Status |
|---|---|---|---|---|
| Bin board | Round, 28.6 mm | 2, gold (ENIG) finish on the rings | ID chip, diode, 2 capacitors, 2 resistors (`pcb/bin_board/bom.csv`) | Layout finished, rule check clean. Not reviewed by a person |
| Row board, first row | 153.5 mm long; 66 x 44.5 mm at the wide end, then a 6 mm strip | 4 | Spring pins for four cells, radio module, step-down converter, three switch chips, one flat-cable socket (`pcb/row_main/bom.csv`) | Drawn and routed (routing by an automatic router). KiCad rule checks: 0 errors, 0 open connections. Positions match the model. Converter, coil, socket and module checked against their data sheets on 19 Nov 2026. Not reviewed by a person |
| Row strip, further rows | 149 mm long; 22.5 x 20.5 mm at the first cell, then a 6 mm strip | 2 | Spring pins for four cells, one switch chip, two flat-cable sockets (`pcb/row_strip/bom.csv`) | Drawn and routed by script. KiCad rule checks: 0 errors, 0 open connections. Positions match the model. Not reviewed by a person; snapping untested |
| Feed board | 30 x 6 mm | 2 | Four spring pins, two wire pads (`pcb/feed_board/bom.csv`) | Layout finished, rule check clean. Copper narrows to 1.4 mm; 2.5 mm was the aim |
| Power board | 34 x 38 mm | 4 | Hub radio module, step-down converter, 3 A resettable fuse (`pcb/power_board/bom.csv`) | Draft. The feed path copper is too thin for 3 A |

Both row boards are made four cells long and have snap lines after the first, second and
third cell (the first-row board: after the second and third). Snap or cut a board to the
width of the tile it goes into. A starter tile's last row is one cell shorter, because its
last cell is the power cell.

**Spring pins are part of the board order**, not something you solder: 2.0 mm barrel,
5.5 mm free height above the board, solder tail, full stroke 1.2 mm or more, 2 A, 50 mOhm or
less (Mill-Max 0906 class). **Measure first:** barrel diameter -> `PIN_HOLE_D`, free height
-> `PIN_ABOVE_BOARD`.

A bin larger than one cell gets a second bin board in its far foot. Only its centre pad is
used, wired to the first board, so it can be ordered without parts.

Board makers usually have a minimum of five boards per design.

## Parts you buy separately

| # | Part | Buy | Why this spec | Price each |
|---|---|---|---|---|
| 1 | Flat cable | Flat flexible cable (FFC), **12 conductors, 0.5 mm pitch, 30 mm long, contacts on the same side at both ends** ("type A"), 0.3 mm thick at the ends | Joins each row board to the next. Stock item from several makers. A longer cable does not lie flat in the 21.5 mm gap | $0.30-2.50 |
| 2 | Board screw | **M2 x 6 self-tapping pan-head screw** for plastic | One under every cell, one more per tile, one for the feed board. **Measure first** -> `CELL_PILOT_D` | cents |
| 3 | Edge connector | Magnetic pogo connector pair, **3 pins, 2.54 mm pitch, wire-solder type, 2 A per pin, rated 24 V or more**, magnets polarised so it cannot mate reversed | Carries 12-24 V, ground and the neighbour pin between tiles. **Measure first:** body, about 15 x 4 x 5.5 mm -> `PORT_W`, `PORT_H`. Check on arrival that reversed halves repel | $3-6 per pair |
| 4 | LED | Single addressable RGB LED on a round board, **WS2812B-V5 or -V6 (or any type whose data input accepts 3.3 V logic at a 5 V supply)**, board 9.4-10 mm across, about 3 mm high | One per compartment | $0.10-0.30 |
| 5 | Magnet | Neodymium disc **6 x 2 mm**, N35 or stronger, nickel plated | Holding only | cents |
| 6 | Feed contacts | **M3 x 10 brass pan-head screws** and brass nuts, four per power bin | Their heads stand proud under the power bin and reach the feed pins. **Measure first:** head 5.6 x 2.4 mm -> `FEED_HEAD_D`, `FEED_HEAD_H` | cents |
| 7 | DC input socket | Panel-mount DC barrel socket, 5.5 x 2.1 mm, 24 V, 3 A or more | In the back wall of the power bin. **Measure first** -> `DC_JACK_D` | $1 |
| 8 | Power supply | **12-24 V DC, 2 A or more**, with a matching barrel plug | The full collection draws about 5 W in normal use and 25 W with every LED full white | |
| 9 | Rubber feet | **Stick-on rubber bumpers, 8 mm across, about 2 mm high**, four per tile | Optional. They sit in pockets under the four corner cells, 0.3 mm proud, and stop the grid sliding, for example when a drawer is pulled. Tiles with and without feet sit level with each other. **Measure first** -> `FOOT_D` | cents |
| 10 | Label tape | 9 mm label tape (12 mm is tight) | For bins printed with label tabs | |
| 11 | Wall screw | M3 pan-head screw and plug, one per cell you want to fix | Goes through the front-left magnet pocket of a cell, in place of that magnet | cents |
| 12 | Power wire | 0.5 mm2 (20 AWG) for the feed between the edge connectors, the feed board and the first-row board | | |
| 13 | Signal wire | Thin enamelled wire or 30 AWG | One per fitted edge connector to the first-row board; three from the bin board to the LED chain | |
| 14 | Glue, solder | Cyanoacrylate or epoxy for bin boards and magnets | | |

## Quantities

"Test set": one 2x2 tile, one 2x2 starter tile, a 2x1 bin with two compartments, two 1x1
bins, the power bin.
"Full collection": the 12 x 6 layout in `tests/grid_sim.py`: eight tiles (one of them a
starter tile), twelve paint bins, the bottle bin, the cleaner bin, the pen holder, the power bin.
"Drawer row": three 4x3 drawer units on three 4x3 tiles, a 2x3 starter tile and a power bin.

| Part | Test set | Full collection | Drawer row | How it is counted |
|---|---|---|---|---|
| Row boards, first row | 2 | 8 | 4 | 1 per tile |
| Row strips | 2 | 16 | 8 | 1 per further row of a tile |
| Flat cables | 2 | 16 | 8 | 1 per row strip |
| Feed board | 1 | 1 | 1 | 1 per starter tile |
| M2 screws | 10 | 80 | 46 | 1 per cell with pins, 1 more per tile, 1 per feed board |
| Bin boards with parts | 3 | 15 | 3 | 1 per bin and drawer unit |
| Bin boards without parts | 1 | 15 | 3 | 1 per bin larger than one cell |
| Power board | 1 | 1 | 1 | 1 per feed |
| Spring pins (on the boards) | 32 | 288 | 168 | 4 per cell with a socket for bins, plus 4 feed pins in the power cell. A row board always carries pins for four cells, so the board order holds more than this |
| Edge connector pairs | 1 | 10 | 3 | 1 per pair of touching tiles |
| LEDs | 4 | 58 | 18 | 1 per compartment |
| Magnets 6 x 2 | 52 | 548 | 316 | 4 per cell + 4 per foot |
| Rubber feet | 8 | 32 | 16 | 4 per tile |
| Brass M3 screws and nuts | 4 | 4 | 4 | power bin |
| DC socket, power supply | 1 | 1 | 1 | |

Add about 10 % spares for pins, magnets and LEDs.

**Magnets:** on a flat surface, feet without a bin board can go without. For the full
collection that is 412 instead of 548. Under drawer units and on a wall, fit them all.

**Cost:** not estimated. The custom boards dominate and have not been quoted; the spring
pins on them (roughly $0.10-0.50 each, 16 per row board) are a large share of their cost.
Of the parts you buy separately, the edge connectors are the largest item: roughly $30-60
for 10 pairs.

## Assembly notes

- **Nothing is soldered inside a tile.** The spring pins come soldered to the row boards.
  Push each board's pins up through the pin holes, fix it with its screws, and join the rows
  with the flat cables (lift the socket's latch, push the cable in with its contacts facing
  the board, close the latch).
- **Bench soldering that remains:** the wires from each edge connector (feed, ground,
  neighbour pin) and from the feed board go to pads on the first-row board. Solder them
  before the board goes into the tile. Build each LED chain on the bench too (bin board,
  wires, LEDs), then feed it up through the bin foot; the openings pass an LED board.
- **Bin board orientation:** turn the bin board so its three LED pads face the wider side of
  the pocket in the foot (toward the back of the bin) before gluing it in.
- **Magnet polarity:** fit every tile magnet with the same pole up, and every bin magnet
  with the opposite pole down. Check each one against a marked reference magnet before
  gluing. A reversed magnet pushes the bin off its pins instead of holding it on.
- **Tiles join without screws or tools:** push two tiles together until the magnetic edge
  connectors snap. A printed bow-tie key can lock the joint for a permanent or wall-mounted
  grid, but it is optional. The only screw is the optional wall screw.
- **Nozzle:** print the smart parts with a 0.4 mm nozzle. The latch beam (1.2 mm) and the
  wall between the bin board and the magnets (0.63 mm) are too fine for 0.6 mm.

## Sources

Dimensions and ratings for the separately bought parts came from web searches on 2026-11-18
and 2026-11-19.
Figures I could not confirm on a datasheet are marked "measure first" above.

- Spring pins: ccpcontactprobes.com (P2859SH01, 6.7 mm, solder cup), Mill-Max 0906 series via element14, lcsc.com, adafruit.com/products/394 (P75 length)
- Magnetic connectors: berrybase.de, electrokit.com, adafruit.com/product/5359, botland.store (Adafruit 5360 dimensions), pogopinsconnector.com (12-36 V rating)
- LEDs: WS2812B-V5 and WS2812B-V6 datasheets, learn.adafruit.com NeoPixel guide
- Magnets: first4magnets.com, jc-magnetics.com
- Flat cable, 12 conductors, 0.5 mm pitch, 30 mm: Molex Premo-Flex 15020-0117 (uk.rs-online.com), GCT 05-12-A-0030 (digikey), Adam Tech CA-DK05-12-30 (digikey). At 1.0 mm pitch the shortest stock length found was 50 mm, which is why the design uses 0.5 mm
