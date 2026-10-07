---
description: Revue d'un diff Salle42 contre les règles métier (conflits stricts, annulation, capacité) et les conventions du projet. Utiliser avant un commit, quand on demande une relecture, ou quand le diff touche salle42/services.py ou salle42/rules/.
allowed-tools: Bash(git diff *) Bash(git status *) Bash(uv run pytest *)
argument-hint: [ref-git]
arguments: [ref]
---

## Diff à relire
!`git diff $ref`

## Règles métier de référence
Voir la section « Règles métier » du CLAUDE.md. Elles priment sur le code existant.

## Instructions
1. Pour chaque règle métier, dire si le diff la respecte, la casse, ou ne la concerne pas. Citer le fichier et la ligne.
2. Vérifier qu'aucune règle métier n'apparaît dans api.py ou cli.py.
3. Vérifier que chaque règle touchée a un test dans tests/. Sinon, proposer le test manquant (code complet).
4. Lancer `uv run pytest -q` et rapporter le résultat.
5. Conclure par : « À commiter », « À corriger d'abord » ou « À discuter », avec une phrase de justification.
Ne modifie aucun fichier.
