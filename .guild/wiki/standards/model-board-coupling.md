---
importance: high
title: Models and boards must agree
type: standard
owner: orchestrator
confidence: high
trust_tier: reviewed
source_refs: [model-board-coupling]
created_at: 2026-11-20
updated_at: 2026-11-20
expires_at: null
supersedes: null
sensitivity: public
recall_importance: 4
---

# Models and boards must agree

## Summary

`lib/smart.scad` is the source for pin, hole, outline and socket positions. `pcb/layout_rows.py` repeats them for KiCad. After any change run `pcb/check_rows.py` (boards against model, 0.05 mm) and `tests/fit.sh` (no collisions in eight tile variants, over 10 minutes). Ghost modules in `parts/smart_base.scad` stand in for boards and cables in the fit checks.

## Key points

- `lib/smart.scad` is the source for pin, hole, outline and socket positions.
- `pcb/layout_rows.py` repeats them for KiCad.
- After any change run `pcb/check_rows.py` (boards against model, 0.05 mm) and `tests/fit.sh` (no collisions in eight tile variants, over 10 minutes).
- Ghost modules in `parts/smart_base.scad` stand in for boards and cables in the fit checks.

## Source

Learn run run-20261120-012744-learn, approved by the project owner. Repository files: lib/smart.scad, pcb/layout_rows.py, pcb/check_rows.py, tests/fit.scad. Raw capture: `.guild/knowledge/sources/model-board-coupling/`.
