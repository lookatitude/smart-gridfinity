# History: ideas tried and decisions made

This file records how the design got to its current state. It is background only: the
current design is described in `docs/smart/design.html`, `docs/smart/parts.md` and
`pcb/README.md`. Nothing below was ever built; every design was dropped on paper, after a
calculation, a simulation or a fit check.

## Starting point

A plain Gridfinity set in OpenSCAD: baseplates, bins, and logic that splits large baseplates
into tiles for a 256 mm print bed. This is still in the repository and still works on its own.

The goal for the "smart" layer: bases that work flat or on a wall with magnets, bins that are
identified, and a light in each compartment so software can point at the item you asked for.

## Design 1: a radio board in every bin

- Each bin had its own small radio board, brass washers as contacts, and three pins per cell.
- A bin found its cell by measuring a voltage set by an address resistor under each cell.
- Power was 5 V from a USB socket in a "controller bin", passed through its foot.

Two ways to build it were compared: off-the-shelf modules wired by hand, or custom boards.
Off-the-shelf was tried first on paper.

**Why it was dropped:** the full collection needed 24 radios and drew about 2.2 A with the
radios on. The resistor addressing depended on measured voltages and contact resistance.

## Design 2: no radio in the bins

Decision: bins carry no radio and no processor. A passive round board in the bin foot has
four concentric contact rings and a 1-Wire ID chip. The tile reads the ID under each cell, so
nothing is measured, and a bin works at any quarter turn.

Other decisions made at this stage, all still in force:

- **Custom boards**, ordered assembled and pre-flashed, bought by specification, not brand.
- **Light under a clear false floor** in every compartment.
- **Four pins per cell:** ID, light data, 5 V, ground.
- **Radios in the full collection:** 9 (eight tiles and the hub).

## From 5 V to 12–24 V distribution

A model of the grid (`pcb/grid_limits.py`, `pcb/grid_power.py`) showed that 5 V distribution
reaches about 9 tiles in a row fed from one end, against 26 tiles at 12 V and 52 at 24 V.

Decision: edge connectors carry 12–24 V. Every tile makes its own 5 V with a step-down
converter. Power enters through a **starter tile** with one special power cell, whose feed
pins are recessed so a normal bin cannot touch them, and a **power bin** that carries the DC
input, the fuse and the hub radio. This replaced the USB controller bin.

## Tiles join without screws

An early tile design used screws between tiles. Decision: tiles join by their edge connectors
and an optional printed bow-tie key, so the grid stays modular and easy to rearrange. The only
screw left on the outside is the optional wall screw.

## Additions from the wider Gridfinity ecosystem

After a review of other Gridfinity parts: label tabs on bins and rubber-foot pockets under
tiles were added. Drawer units were added as plain-top units, 13 units high.

## Wiring inside the tile: three attempts

The hard part was getting four contacts under each of up to 16 cells to one processor
without soldering next to printed plastic.

1. **One tile board with 48 wire pads.** A T-shaped board, 66 × 18 mm with a tab, sat between
   two pin rows. Every spring pin was wired to it by hand, inside the printed tile.
   Dropped: too much soldering close to the print.
2. **Plug-in contact boards.** A small board under every cell carried the four pins and a
   4-pin socket; ready-made cables ran to six sockets on the tile board. The boards passed
   their electrical checks. Dropped after the fit check: the T-shaped board had room for only
   6 of 16 sockets, and every plug collided with a contact board.
3. **Row boards (current).** One long board under every row of cells with the pins already
   on it. The first row's board holds the processor and converter; further rows are strips
   joined by a short flat cable. Tiles are limited to 4 cells each way as a result.

Details settled along the way:

- The strips were first planned as passive. Each now carries one switch chip, because a
  passive strip would have needed more cable conductors than a stock cable has.
- The cable was first planned at 1.0 mm pitch. No stock cable shorter than 50 mm was found,
  and the gap between rows is 21.5 mm, so the design uses 0.5 mm pitch, 30 mm long.

## Corrections from data sheets

A check of the cable socket, converter, radio module and coil against their makers' data
sheets changed four things: the socket is 10.1 mm wide, not 9.4 mm; the cable limit is 0.7 A,
not 1.0 A, so firmware must cap full white; the converter's coil is 4.7 µH, not 6.8 µH; and
the surge diode was changed to a type that clamps below the converter's limit.

## Standing principles

- Validate by calculation, simulation and fit check before buying anything.
- Keep the system modular: every powered feature is optional, and plain parts keep working.
- No soldering near printed parts: solder on the bench, plug or press-fit at the print.
