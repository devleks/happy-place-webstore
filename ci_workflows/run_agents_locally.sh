#!/bin/bash
# Runs all automation agents sequentially on the local machine
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

agents=(
  "agent_lintguard.sh"
  "agent_schemasage.sh"
  "agent_perfsmith.sh"
  "agent_shieldprobe.sh"
  "agent_atlasreporter.sh"
)

for agent in "${agents[@]}"; do
  echo "============================================================"
  echo "Executing ${agent}"
  echo "============================================================"
  bash "$SCRIPT_DIR/$agent"
done
