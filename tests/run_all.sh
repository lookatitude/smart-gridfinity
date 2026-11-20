#!/usr/bin/env bash
# Run every design check for the smart system. Exits non-zero if any fails.
#   contacts.py  pins land on the right rings; the bin board clears the magnets
#   power.py     current for the test set, the full collection and the drawer row
#   grid_sim.py  layouts, position discovery, voltage at every tile; writes docs/smart/layout.svg
# The electrical checks of the boards themselves are in pcb/ (KiCad rule check, signals.py).
#   fit.sh       parts do not collide (OpenSCAD intersections)
set -e
cd "$(dirname "$0")"
python3 contacts.py
python3 power.py
python3 grid_sim.py
./fit.sh
echo "ALL CHECKS PASSED"
