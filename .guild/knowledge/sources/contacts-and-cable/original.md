---
title: Cell contacts and row cable
category: concept
source_refs: [pcb/README.md#contacts, pcb/boards.py, tests/contacts.py]
confidence: high
---
Four spring pins per cell on a line from the cell centre: ID at 0, light data at 5.4, 5 V at 9.2, ground at 12.9 mm. The bin board has matching concentric rings, so any quarter turn works. Rows are joined by a 12-conductor 0.5 mm pitch flat cable, 30 mm, same-side contacts. Positions 1–12: 5V, 5V, GND, GND, light data, GND, ID, select 0, select 1, three row enables that shift by one per strip. Nets are defined by position because IN and OUT sockets face opposite ways.
