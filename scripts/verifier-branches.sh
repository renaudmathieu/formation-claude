#!/bin/bash
# Check every Escale checkpoint: tests, lint, and the mod from tp/5-mod onwards.
# Usage: from a full clone, on the formateur branch: scripts/verifier-branches.sh
set -u
ATTENDU=(
  "tp/0-depart|2 passed, 1 skipped"
  "tp/1-chat|11 passed, 1 skipped"
  "tp/2-tool|18 passed"
  "tp/3-agent|39 passed"
  "tp/4-mcp|46 passed"
  "tp/5-mod|51 passed"
  "tp/6-rag|59 passed"
)
depart=$(git branch --show-current)
echec=0
for ligne in "${ATTENDU[@]}"; do
  branche=${ligne%%|*}; attendu=${ligne#*|}
  git switch -q "$branche" || { echo "✗ $branche introuvable"; echec=1; continue; }
  uv sync -q
  resultat=$(uv run pytest -q 2>&1 | tail -n 1)
  if [[ "$resultat" == "$attendu in "* ]] && uv run ruff check -q . >/dev/null; then
    echo "✓ $branche : $resultat"
  else
    echo "✗ $branche : $resultat (attendu : $attendu, ou lint en échec)"; echec=1
  fi
  if [ -f outils/mod-trace/.claude-plugin/plugin.json ] && command -v claude >/dev/null; then
    claude plugin validate outils/mod-trace >/dev/null 2>&1 && claude plugin test outils/mod-trace >/dev/null 2>&1 \
      && echo "✓ mod trace : validate et test" || { echo "✗ mod trace"; echec=1; }
  fi
done
git switch -q "$depart"
exit $echec
