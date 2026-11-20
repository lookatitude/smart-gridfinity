---
importance: high
title: Architecture map (stub)
status: reviewed
derived_from: cheap scan, run-20261120-011815-init (no commit yet)
recall_importance: 3
---

# Architecture map (stub)

Smart Gridfinity: an OpenSCAD Gridfinity storage system with an optional powered layer
(bins identified and lit per compartment). Design stage: nothing printed, no firmware.

| Area | What it holds | Confidence | Source |
|---|---|---|---|
| `lib/` | Shared OpenSCAD constants and profiles; `smart.scad` holds every dimension the boards must match | high | `lib/constants.scad`, `lib/smart.scad` |
| `parts/` | One OpenSCAD file per printable part (tiles, bins, power bin, drawer unit, keys, sleeves) | high | `parts/*.scad` |
| `assembly*.scad` | Assembled views that produce the pictures in `docs/` | high | `assembly_smart.scad` |
| `build.sh`, `build_smart.sh` | Export printable STL files into `build/` (not tracked) | high | the scripts |
| `pcb/` | Five KiCad boards generated from Python: `boards.py` (circuits), `layout_*.py` (layouts), `outputs.py` (rule checks, parts lists, fabrication files) | high | `pcb/README.md` |
| `pcb/check_rows.py` | Checks row-board positions against the printed tile | high | the script |
| `tests/` | Design checks: fit by intersection volume, contacts, power budget, grid simulation | high | `tests/run_all.sh` |
| `docs/smart/` | Design page and materials list | high | `docs/smart/design.html`, `docs/smart/parts.md` |

## Coupling to watch

- Board outlines, pin, hole and socket positions are fixed by `lib/smart.scad`; `pcb/layout_rows.py`
  repeats them and `pcb/check_rows.py` compares. Confidence: high.
- `pcb/layout_rows.py` builds on the `Layout` class in `pcb/layout_contact.py`; `pcb/layout_power.py` uses the shared steps in `pcb/layout_kit.py`. Confidence: high.

## Not mapped yet

The deep knowledge graph and onboarding tour are deferred (run `/guild:learn`).
