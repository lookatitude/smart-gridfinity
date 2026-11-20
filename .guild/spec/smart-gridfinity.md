---
title: Reverse spec, smart-gridfinity
derived_from: knowledge graph, run-20261120-012744-learn
status: candidate
---

# What the project guarantees (as built, from the graph)

| Claim | source_refs | confidence |
|---|---|---|
| Every dimension shared by models and boards is defined once in `lib/smart.scad` | `lib/smart.scad`, `pcb/check_rows.py` | high |
| Each cell has four spring pins on a line from the cell centre: ID 0 mm, light data 5.4 mm, 5 V 9.2 mm, ground 12.9 mm | `pcb/README.md#contacts`, `tests/contacts.py` | high |
| A bin works at any quarter turn, because the bin board has concentric rings | `pcb/README.md#contacts` | high |
| A tile is 2×2 to 4×4 cells; one board per row; rows joined by a 12-way 0.5 mm flat cable | `pcb/README.md#circuit-boards`, `docs/HISTORY.md#wiring-inside-the-tile-three-attempts` | high |
| Cable nets are assigned by position 1–12, and three row-enable lines shift by one per strip | `pcb/boards.py` (`ffc_nets`, `row_strip`, `row_main`) | high |
| Grid distribution is 12–24 V; each tile converts to 5 V | `docs/HISTORY.md#from-5-v-to-1224-v-distribution`, `pcb/grid_limits.py` | high |
| One flat cable carries at most 0.7 A at 5 V; firmware must cap full white at 11 lights behind a cable | `tests/power.py`, `pcb/README.md#known-limits` | high |
| All five boards pass KiCad ERC and DRC with 0 findings | `pcb/*/erc.rpt`, `pcb/*/drc.rpt` | high (as of the last `outputs.py` run) |
| Row-board positions match the model within 0.05 mm | `pcb/check_rows.py` | high |
| No part overlaps another in any of eight tile variants | `tests/fit.scad`, `tests/fit.sh` | high |
| Firmware behaviour (retry when a bin spans two tiles, brightness cap) | none: no firmware exists | low, stated intent only |
| Hardware behaviour of any part | none: nothing printed or built | low |

# Invariants a change must keep

- Change a pin, hole, outline or socket position in `lib/smart.scad` and `pcb/layout_rows.py` together; `check_rows.py` and `tests/fit.sh` must both pass.
- No soldering at the printed part: boards arrive assembled and plug or screw in.
- Powered features stay optional; plain parts keep working without them.
