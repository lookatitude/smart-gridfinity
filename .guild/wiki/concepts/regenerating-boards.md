---
importance: high
title: Regenerating and checking the boards
type: concept
owner: orchestrator
confidence: high
trust_tier: reviewed
source_refs: [regenerating-boards]
created_at: 2026-11-20
updated_at: 2026-11-20
expires_at: null
supersedes: null
sensitivity: public
recall_importance: 3
---

# Regenerating and checking the boards

## Summary

`boards.py` writes schematics; `layout_bin.py`, `layout_contact.py`, `layout_rows.py strip`, `layout_rows.py main --keep`, `layout_power.py place` then `route --keep` write layouts; `outputs.py` runs ERC and DRC and writes pictures, parts lists and fabrication files. Freerouting is not repeatable: keep the `.ses` files and use `--keep`.

## Key points

- `boards.py` writes schematics; `layout_bin.py`, `layout_contact.py`, `layout_rows.py strip`, `layout_rows.py main --keep`, `layout_power.py place` then `route --keep` write layouts; `outputs.py` runs ERC and DRC and writes pictures, parts lists and fabrication files.
- Freerouting is not repeatable: keep the `.ses` files and use `--keep`.

## Source

Learn run run-20261120-012744-learn, approved by the project owner. Repository files: pcb/README.md#regenerating, pcb/outputs.py. Raw capture: `.guild/knowledge/sources/regenerating-boards/`.
