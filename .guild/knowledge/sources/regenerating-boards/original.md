---
title: Regenerating and checking the boards
category: recipe
source_refs: [pcb/README.md#regenerating, pcb/outputs.py]
confidence: high
---
`boards.py` writes schematics; `layout_bin.py`, `layout_contact.py`, `layout_rows.py strip`, `layout_rows.py main --keep`, `layout_power.py place` then `route --keep` write layouts; `outputs.py` runs ERC and DRC and writes pictures, parts lists and fabrication files. Freerouting is not repeatable: keep the `.ses` files and use `--keep`.
