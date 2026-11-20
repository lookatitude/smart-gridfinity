---
title: Models and boards must agree
category: standard
source_refs: [lib/smart.scad, pcb/layout_rows.py, pcb/check_rows.py, tests/fit.scad]
confidence: high
---
`lib/smart.scad` is the source for pin, hole, outline and socket positions. `pcb/layout_rows.py` repeats them for KiCad. After any change run `pcb/check_rows.py` (boards against model, 0.05 mm) and `tests/fit.sh` (no collisions in eight tile variants, over 10 minutes). Ghost modules in `parts/smart_base.scad` stand in for boards and cables in the fit checks.
