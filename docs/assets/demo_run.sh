#!/usr/bin/env bash
# Orchestrator for the demo GIF — printed at human-paced speed so asciinema
# captures it as a realistic terminal session.

set -e

PS_PROMPT=$'\e[1;32mwarehouse_humanoid_tco\e[0m \e[1;34m$\e[0m '
TYPE_DELAY=0.025
PAUSE_AFTER=4

type_cmd() {
  printf '%s' "$PS_PROMPT"
  local text="$1"
  local i
  for ((i=0; i<${#text}; i++)); do
    printf '%s' "${text:$i:1}"
    sleep "$TYPE_DELAY"
  done
  printf '\n'
  sleep 0.3
}

section_header() {
  printf '\e[2J\e[H'                # clear
  printf '\e[1;36m# %s\e[0m\n\n' "$1"
  sleep 0.7
}

# --- 1. Clean version history -------------------------------------------------
section_header "warehouse_humanoid_tco — clean version history (6 thematic releases)"
type_cmd "git log --oneline --decorate"
git log --oneline --decorate
sleep "$PAUSE_AFTER"

# --- 2. Monte Carlo result ----------------------------------------------------
section_header "Monte Carlo sensitivity — 10,000 samples, 6 parameters"
type_cmd ".venv/bin/python docs/assets/demo_mc_summary.py"
.venv/bin/python docs/assets/demo_mc_summary.py
sleep "$PAUSE_AFTER"

# --- 3. Scenario ranking ------------------------------------------------------
section_header "Scenario ranking — S-hybrid-amr remains the lowest-NPV scenario"
type_cmd ".venv/bin/python docs/assets/demo_scenarios.py"
.venv/bin/python docs/assets/demo_scenarios.py
sleep "$PAUSE_AFTER"

# --- 4. Test suite ------------------------------------------------------------
section_header "Test suite — verifiable, reproducible"
type_cmd ".venv/bin/python -m pytest -q --no-header --no-cov 2>&1 | tail -3"
.venv/bin/python -m pytest -q --no-header --no-cov 2>&1 | tail -3
sleep 5

# Hold final frame
sleep 2
