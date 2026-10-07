# Formation « Maîtriser Claude Code en 2 jours » : dépôt solution

Ce dépôt est **réservé au formateur**. Il contient le projet fil rouge **Salle42** dans son état de départ et une branche solution par checkpoint. Cette branche `formateur` ne contient que cette notice et un script de vérification ; le code est sur les autres branches.

Les supports (modules, guides formateur, kit J-7) sont dans Notion, page « Maîtriser Claude Code en 2 jours ».

## Les branches

| Branche | Module | Ce qu'elle contient | Tests attendus |
| --- | --- | --- | --- |
| `main` = `etape/00-legacy` | 3 | Le projet hérité : pas de README, pas de `CLAUDE.md`, `salle42.db` commitée, un `services.py` qui mélange tout, 2 tests dont un ignoré, 3 bugs plantés | 1 passed, 1 skipped |
| `etape/04-claude-md` | 4 | `CLAUDE.md` court (règles écrites d'après la spécification), `.claude/rules/metier.md` scopée sur `salle42/**/*.py`, `.gitignore` corrigé, base retirée du suivi | 1 passed, 1 skipped |
| `etape/05-premier-bug` | 5 | B1 corrigé, test réactivé, test de dépassement de capacité | 3 passed |
| `etape/08-permissions` | 8 | `.claude/settings.json` d'équipe et hook `Stop` `.claude/hooks/tests-verts.sh` (exécutable) | 3 passed |
| `etape/09-skill` | 9 | Skill projet `.claude/skills/revue-salle42/SKILL.md` | 3 passed |
| `etape/10-feature` | 10 | F1 (`--weekly N`), B2 et B3 corrigés avec tests, `rules/` extrait, README, docstrings, rétro harnais dans `CLAUDE.md` | 19 passed |
| `etape/11-mod` | 11 | Le mod `outils/mod-harnais/` (bandeau et `/harnais`) | 19 passed, et 6 tests du mod |

Chaque checkpoint est un commit (ou une suite de commits) au message explicite : `git log --oneline etape/00-legacy..etape/11-mod` est le « chemin parcouru » du module 12.

## Les bugs plantés (ne pas révéler)

| Bug | Symptôme | Cause | Corrigé sur |
| --- | --- | --- | --- |
| B1 · crash | `book` sans `--attendees` plante en `TypeError` | `services.check_capacity` compare `None > room.capacity` | `etape/05-premier-bug` |
| B2 · logique | 10:00–11:00 puis 11:00–12:00 refusés comme « en conflit » | `overlaps()` utilise `<=` au lieu de `<` | `etape/10-feature` |
| B3 · données | Après `cancel`, le créneau reste bloqué | `find_conflicts` ne filtre pas `status == "cancelled"` | `etape/10-feature` |

Note : sur `main`, B1 masque B3 en CLI tant qu'on réserve sans `--attendees` ; pour montrer B3 avant le module 5, réserver avec `--attendees 2`.

## Préparer la session

1. **Le dépôt des stagiaires** ne doit contenir que `main` (l'état de départ). Pour le créer depuis ce dépôt :
   ```bash
   git clone --single-branch --branch main git@github.com:renaudmathieu/formation-claude.git salle42
   cd salle42 && git remote set-url origin <url-du-depot-stagiaires> && git push -u origin main
   ```
   Donner un accès en lecture à chaque stagiaire (ou un fork par stagiaire).
2. **La veille**, sur ce dépôt : `scripts/verifier-branches.sh` (depuis la branche `formateur`, dans un clone complet). Il passe chaque branche, lance `uv run pytest -q` et `uv run ruff check .`, et vérifie le mod sur `etape/11-mod` si `claude` est installé.
3. **Versions** : Claude Code 2.1.287 ou plus récent (mods), Python 3.12+, `uv`.

## Ce qui n'est pas encore dans ce dépôt

Le **parcours avancé** (modules A1 à A6) part de `etape/10-feature` avec une branche `etape/a0-depart` et six branches solution : ses spécifications sont sur la page Notion « Dépôt du parcours : la branche etape/a0-depart ». Le code de `etape/10-feature` respecte déjà son contrat d'architecture (`rules/` n'importe pas `storage`) et stocke les dates en UTC, ce qui permet d'y planter B4 et l'import interdit.
