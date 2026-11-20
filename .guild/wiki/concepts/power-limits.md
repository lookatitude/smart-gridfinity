---
importance: high
title: Power limits
type: concept
owner: orchestrator
confidence: high
trust_tier: reviewed
source_refs: [power-limits]
created_at: 2026-11-20
updated_at: 2026-11-20
expires_at: null
supersedes: null
sensitivity: public
recall_importance: 3
---

# Power limits

## Summary

Spring pin 2 A; two feed pins per pole. Tile converter 2 A at 5 V. Flat cable 0.7 A at 5 V (two contacts of 0.5 A at the 70 % the socket maker asks for), so full white is capped at 11 lights behind one cable. Full collection at 12 V: about 5.4 W. One 24 V feed reaches about 52 tiles in a row fed from one end (model, not measured).

## Key points

- Spring pin 2 A; two feed pins per pole.
- Tile converter 2 A at 5 V.
- Flat cable 0.7 A at 5 V (two contacts of 0.5 A at the 70 % the socket maker asks for), so full white is capped at 11 lights behind one cable.
- Full collection at 12 V: about 5.4 W.
- One 24 V feed reaches about 52 tiles in a row fed from one end (model, not measured).

## Source

Learn run run-20261120-012744-learn, approved by the project owner. Repository files: tests/power.py, pcb/grid_limits.py, pcb/README.md#known-limits. Raw capture: `.guild/knowledge/sources/power-limits/`.
