# Circuit boards

Five boards, defined in Python and written out as KiCad 10 projects. All are drafts: they pass
KiCad's rule checks, but no person has reviewed them and none has been built.

| Board | Where it goes | Layers |
|---|---|---|
| `bin_board` | In the foot of each smart bin: four contact rings, ID chip, connector for the lights | 2 |
| `row_main` | Under the first row of a tile: spring pins for four cells, radio module, 5 V converter, switch chips, one flat-cable socket | 4 |
| `row_strip` | Under every further row: spring pins for four cells, one switch chip, two flat-cable sockets. Can be snapped shorter | 2 |
| `feed_board` | Under the power cell of a starter tile: four feed pins | 2 |
| `power_board` | Inside the power bin: DC input, fuse, hub radio | 4 |

## Contacts

Each cell has four spring pins in a line from the cell centre: ID at 0 mm, light data at
5.4 mm, 5 V at 9.2 mm, ground at 12.9 mm. The bin board has matching concentric rings, so a
bin works at any quarter turn.

Rows are joined by a flat cable: 12 conductors, 0.5 mm pitch, 30 mm long, contacts on the same
side at both ends. Positions 1–12: 5V, 5V, GND, GND, light data, GND, ID, select 0, select 1,
and three row-enable lines that shift by one on each strip.

## Regenerating

    python3 boards.py                 # schematics, parts lists, library tables
    python3 layout_bin.py             # bin_board layout
    python3 layout_contact.py         # feed_board layout
    python3 layout_rows.py strip      # row_strip layout
    python3 layout_rows.py main --keep   # row_main layout from the saved routing (row_main.ses)
    python3 layout_power.py place && python3 layout_power.py route --keep   # power_board
    python3 outputs.py                # rule checks, pictures, bom.csv, fab/ for every board

`row_main` and `power_board` are routed with Freerouting. Its results are not repeatable, so
the routing that passed is saved as a `.ses` file next to each board.

## Checks

`grid_limits.py` and `grid_power.py` model how far one power feed reaches across a grid.

    python3 check_rows.py    # row boards against the printed tile: outline, pins, holes, sockets
    python3 signals.py       # signal levels and timing through the switch chips

Each board folder holds `erc.rpt` and `drc.rpt` from the last run.

## Known limits

- The flat-cable sockets allow 0.7 A at 5 V per cable, so firmware must hold full white to
  11 lights behind any one cable.
- On `row_main` the 5 V copper narrows to 0.8 mm at the cable socket and runs on inner layers.
- `row_main` is checked at 0.125 mm track spacing, the other boards at 0.15 mm.
- Snapping a `row_strip` shorter cuts through 5 V and ground copper 0.7 mm apart. Untested.
