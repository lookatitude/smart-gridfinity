# Glossary

The words this project uses, in plain terms. Gridfinity's own terms come first.

## Gridfinity

| Term | Meaning |
|---|---|
| Gridfinity | An open, modular storage standard: baseplates with a 42 mm grid of sockets, and bins that drop into them. See [gridfinity.xyz](https://gridfinity.xyz/) |
| Pitch | The grid spacing: 42 mm |
| Unit (of height) | 7 mm. A "3-unit" bin is 21 mm high |
| Baseplate | The plate with sockets that bins sit in |
| Foot | The shaped underside of a bin that fits a socket. A bin has one foot per cell it covers |
| Stacking lip | The rim at the top of a bin that lets another bin sit on it |

## The base

| Term | Meaning |
|---|---|
| Tile | One printed piece of the smart base, 2×2 to 4×4 cells, with its own electronics |
| Cell | One 42 mm socket in a tile, with four spring pins and four magnets |
| Starter tile | A tile with one power cell. Power enters the grid through it |
| Power cell | The special cell of a starter tile (back-right corner). Its feed pins are recessed so only the power bin can reach them |
| Grid | All the tiles joined together |
| Edge connector | A 3-pin magnetic connector in a tile's outer wall. It carries power, ground and a neighbour pin to the next tile |
| Port | One edge-connector position on a tile |
| Neighbour pin | The edge-connector pin over which two touching tiles identify each other |
| Bow-tie key | An optional printed piece that locks two tiles together from below |
| Cavity | The open space under a tile's socket floor, where the boards lie |

## The bins

| Term | Meaning |
|---|---|
| Smart bin | A bin with a bin board in its foot and a light under each compartment |
| Compartment | One walled space inside a bin, with its own light |
| False floor | The clear plate at the bottom of a compartment. The LED sits under it |
| Jar sleeve | An optional clear insert that holds a jar and carries light up around it |
| Label tab | An optional strip along the top of a compartment's back wall, for label tape |
| Power bin | The bin that brings 12–24 V into the grid and holds the hub radio |
| Drawer unit | A smart shell with a plain sliding drawer inside |
| Snap latch | A sprung tab on a bin foot that holds the bin in its socket on a wall |

## Electronics

| Term | Meaning |
|---|---|
| Spring pin | A sprung contact that stands up through the socket floor and touches the bin board |
| Bin board | The round board in a bin foot: a centre pad and three rings, an ID chip, pads for the LED chain |
| Rings | The concentric contacts on the bin board: ID (centre), light commands, 5 V, ground |
| ID chip | A small memory chip with a factory-set unique number. This is how a bin is recognised |
| Row board | A long board under one row of cells, carrying that row's spring pins |
| First-row board (`row_main`) | The row board with the tile's radio module and 5 V converter |
| Row strip (`row_strip`) | The row board under each further row, with one switch chip |
| Flat cable | The 12-conductor ribbon that joins one row board to the next |
| Feed board | The small board under the power cell with four feed pins |
| Power board | The board inside the power bin: DC input, fuse, hub radio |
| Hub | The radio in the power bin. It collects reports from the tiles, keeps the map and talks to your software |
| Converter | The part on each tile that turns 12–24 V into 5 V |
| Switch chip | A chip that connects one cell at a time to the shared ID and light-command lines |
| Light commands | The data signal that tells addressable LEDs what colour to show |
| Feed | The 12–24 V supply that runs through the grid |

## Design and checks

| Term | Meaning |
|---|---|
| Fit check | A test that two parts do not occupy the same space, done by intersecting their models |
| Ghost | A solid stand-in for a board, cable or connector in the model. Used by fit checks, never printed |
| Rule check | KiCad's automatic checks of a schematic (ERC) and a board layout (DRC) |
| Test set | The smallest build: two 2×2 tiles, three bins, the power bin |
| Full collection | The larger scenario used to test the plan: eight tiles, 16 bins, 72 cells |
| Guild | The AI-assisted development tool this repository is set up for. Its files are in `.guild/` and are not needed to use the design |
