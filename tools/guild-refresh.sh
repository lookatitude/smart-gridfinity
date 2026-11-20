#!/usr/bin/env bash
# Rebuild Guild's knowledge graph for this project in the order that keeps the code
# structure, and set the project's name in the result.
#
# Why this exists (Guild 3.2.0): the knowledge finalize step keeps file and function nodes
# only when the graph on disk is still the structural (v1) one, and it labels the project
# "guild". Running the stages by hand in another order silently drops the code structure.
#
#   tools/guild-refresh.sh structure <run-id>   scan, structural graph, candidate files
#   (write or update the k1, k2, k4 and k5 judgment files for that run)
#   tools/guild-refresh.sh finalize <run-id>    structural graph again, then knowledge tier
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
STEP="${1:?usage: tools/guild-refresh.sh structure|finalize <run-id>}"
RUN="${2:?run id, as printed by run-trace start}"
PLUGIN="${GUILD_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(ls -d "$HOME"/.claude/plugins/cache/guild/guild/*/ 2>/dev/null | sort -V | tail -1)}}"
[ -f "$PLUGIN/runtime/scripts/learn-scan.js" ] || { echo "Guild plugin not found; set GUILD_PLUGIN_ROOT" >&2; exit 1; }
stage() { local s="$1"; shift; node "$PLUGIN/runtime/scripts/$s.js" --cwd "$ROOT" "$@"; }
KDIR=".guild/runs/$RUN/knowledge"

structural() {
    stage learn-scan 2>&1 | grep '^\['
    stage analyze-structural 2>&1 | grep '^\['
    stage validate-graph --force 2>&1 | grep '^\[validate\] OK'    # --force: replace a finished graph on purpose
    stage assign-layers 2>&1 | grep '^\['
    stage derive-domain --run-id "$RUN" 2>&1 | grep '^\['
    stage build-tour 2>&1 | grep '^\['
}

case "$STEP" in
structure)
    structural
    stage knowledge-orchestrator --phase=round1 --run-id "$RUN" > /dev/null
    echo "candidates written to $KDIR. Write k1-, k2- and k4-judgments.json, then run: finalize $RUN"
    ;;
finalize)
    for k in k1 k2 k4; do [ -f "$KDIR/$k-judgments.json" ] || { echo "missing $KDIR/$k-judgments.json" >&2; exit 1; }; done
    structural
    stage knowledge-orchestrator --phase=round1 --run-id "$RUN" > /dev/null
    stage knowledge-orchestrator --phase=round2 --run-id "$RUN" > /dev/null
    if [ ! -f "$KDIR/k5-judgments.json" ]; then
        echo "cross-link candidates written to $KDIR/k5-candidates.json. Write k5-judgments.json, then run finalize again." >&2; exit 2
    fi
    stage knowledge-orchestrator --phase=finalize --run-id "$RUN" | grep Count
    python3 - <<'PY'
import json, collections
p = ".guild/indexes/knowledge-graph.json"
g = json.load(open(p))
g["project"] = {"name": "smart-gridfinity", "description": "An OpenSCAD Gridfinity storage system with an optional powered layer: bins carry an ID chip and a light per compartment, read and driven by boards under each tile row. Models, KiCad boards generated from Python, and design checks that keep the two in agreement."}
json.dump(g, open(p, "w"), indent=2)
kinds = collections.Counter(n["type"] for n in g["nodes"])
assert kinds["file"] > 0 and kinds["function"] > 0, "the code structure is missing from the graph"
print("graph:", dict(kinds))
PY
    stage k-stage-staleness --baseline | tail -1
    ;;
*) echo "unknown step: $STEP" >&2; exit 1 ;;
esac
