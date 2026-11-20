# Documentation

Start with **[How it works](how-it-works.md)**. It explains the whole system with pictures
in about ten minutes. Everything else goes deeper on one topic.

## Pick by what you want to do

| I want to… | Read |
|---|---|
| Understand the idea and how the pieces fit together | [How it works](how-it-works.md) |
| Look up a word (tile, cell, row board, power cell…) | [Glossary](glossary.md) |
| See every printed part and board, and which file makes it | [Parts guide](parts-guide.md) |
| Print something | [Parts guide: printing](parts-guide.md#printing), and the [releases](https://github.com/lookatitude/smart-gridfinity/releases) for ready-made STL files |
| Know what to buy, by specification | [Materials list](smart/parts.md) |
| Know what has been verified and what is still open | [Status and open questions](status.md) |
| Run the design checks myself | [`tests/README.md`](../tests/README.md) |
| Work on the circuit boards | [`pcb/README.md`](../pcb/README.md) |
| Change a model | [Parts guide: changing a model](parts-guide.md#changing-a-model) |

## All documents

| Document | What it is |
|---|---|
| [how-it-works.md](how-it-works.md) | The system explained: tracking, signalling, power, tiles, bins |
| [parts-guide.md](parts-guide.md) | Catalogue of printed parts and boards, source files, printing notes |
| [glossary.md](glossary.md) | The project's vocabulary |
| [status.md](status.md) | What was checked, with results, and what the design does not settle |
| [smart/parts.md](smart/parts.md) | Materials list with specifications, quantities and sources |
| [Design page](https://lookatitude.github.io/smart-gridfinity/smart/design.html) | The full illustrated design page, with diagrams (source: `smart/design.html`) |
| [`../pcb/README.md`](../pcb/README.md) | The five boards, the contact and cable order, how to regenerate them |
| [`../tests/README.md`](../tests/README.md) | Each design check, what it proves, how to run it |

## Where things are in the repository

```
lib/        shared OpenSCAD dimensions (smart.scad is the one the boards must match)
parts/      one OpenSCAD file per printable part
pcb/        circuit boards: Python scripts that write KiCad files, and the results
tests/      design checks
docs/       this folder; pictures are in docs/ and docs/smart/
tools/      helper scripts
build.sh, build_smart.sh    export printable STL files into build/
assembly.scad, assembly_smart.scad    assembled views that produce the pictures
```
