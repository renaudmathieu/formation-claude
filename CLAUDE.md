# Salle42 : réservation de salles

## Commandes
- Installer : `uv sync` · Tests : `uv run pytest -q` · Lint : `uv run ruff check . && uv run ruff format .`
- API : `uv run uvicorn salle42.api:app --reload` · CLI : `uv run salle42 --help`

## Architecture
- `models.py` (dataclasses) → `storage.py` (SQLite, seul accès à la base) → `services.py` (règles métier) → `api.py` / `cli.py` (présentation).
- La présentation ne contient aucune règle métier.
- Les dates sont stockées en UTC ; la CLI et l'affichage sont en heure de Paris.

## Règles métier (source de vérité : cette section)
- Deux réservations sont en conflit si leurs intervalles se chevauchent **strictement** : 10:00–11:00 et 11:00–12:00 ne sont PAS en conflit.
- Une réservation annulée ne bloque plus le créneau.
- `attendees` est optionnel ; s'il est fourni, il doit être ≤ capacité de la salle.
- Le détail et les cas limites sont dans `.claude/rules/metier.md`.

## Conventions
- Toute règle métier a un test dans `tests/`. Lancer `uv run pytest -q` avant de proposer un commit.
- Type hints partout, docstrings Google style sur les fonctions publiques.
- Ne jamais modifier `salle42.db` ni les fichiers sous `.claude/` sans demander.

## Git
- Une branche par tâche, messages de commit en français à l'impératif, jamais de `git push`.
