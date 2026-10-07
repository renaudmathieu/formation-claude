#!/bin/bash
# Vérifie chaque checkpoint de Salle42 : tests, lint, et le mod sur etape/11-mod.
# Usage : depuis un clone complet, sur la branche formateur : scripts/verifier-branches.sh
set -u
ATTENDU=(
  "etape/00-legacy|1 passed, 1 skipped"
  "etape/04-claude-md|1 passed, 1 skipped"
  "etape/05-premier-bug|3 passed"
  "etape/08-permissions|3 passed"
  "etape/09-skill|3 passed"
  "etape/10-feature|19 passed"
  "etape/11-mod|19 passed"
)
depart=$(git branch --show-current)
echec=0
for ligne in "${ATTENDU[@]}"; do
  branche=${ligne%%|*}; attendu=${ligne#*|}
  git switch -q "$branche" || { echo "✗ $branche introuvable"; echec=1; continue; }
  uv sync -q
  resultat=$(uv run pytest -q 2>&1 | tail -n 1)
  if [[ "$resultat" == "$attendu"* ]] && uv run ruff check -q . >/dev/null; then
    echo "✓ $branche : $resultat"
  else
    echo "✗ $branche : $resultat (attendu : $attendu, ou lint en échec)"; echec=1
  fi
  if [ "$branche" = "etape/11-mod" ] && command -v claude >/dev/null; then
    claude plugin validate outils/mod-harnais >/dev/null 2>&1 && claude plugin test outils/mod-harnais >/dev/null 2>&1 \
      && echo "✓ mod harnais : validate et test" || { echo "✗ mod harnais"; echec=1; }
  fi
done
git switch -q "$depart"
exit $echec
