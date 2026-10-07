#!/bin/bash
# .claude/hooks/tests-verts.sh : hook Stop de Salle42
# Claude ne conclut pas sur des tests rouges.
# Une seule relance, puis la main revient à l'humain.
INPUT=$(cat)
cd "$CLAUDE_PROJECT_DIR" || exit 0

# Rouge voulu par l'humain (phase « tests d'abord », module 10) : on laisse passer
[ -f .claude/rouge-attendu ] && exit 0

# Rien de modifié dans le code ni dans les tests : rien à vérifier
[ -z "$(git status --porcelain -- salle42 tests)" ] && exit 0

# Tests verts : Claude peut s'arrêter
OUT=$(uv run pytest -q 2>&1) && exit 0

# Déjà relancé une fois par ce hook : on rend la main à l'humain
if echo "$INPUT" | grep -q '"stop_hook_active": *true'; then
  echo '{"systemMessage": "Tests toujours rouges après une relance : reprenez la main."}'
  exit 0
fi

# Tests rouges : on bloque l'arrêt et on renvoie la preuve à Claude
echo "Les tests sont rouges, ne conclus pas. Sortie de pytest :" >&2
echo "$OUT" | tail -n 30 >&2
exit 2
