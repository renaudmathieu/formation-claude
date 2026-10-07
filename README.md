# Salle42

Service de réservation de salles de réunion : une API FastAPI, une CLI et une base SQLite.
On réserve une salle sur un créneau, seul ou chaque semaine ; Salle42 refuse les conflits et les dépassements de capacité.

## Installer

Prérequis : Python 3.12+ et [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Lancer

```bash
uv run salle42 rooms
uv run salle42 book B 2026-09-14 10:00 11:00 --by renaud --attendees 3
uv run salle42 book B 2026-09-14 11:00 12:00 --by nico
uv run salle42 book A 2026-09-14 10:00 11:00 --by evan --weekly 4
uv run salle42 list --room B
uv run salle42 cancel <id>
```

Les heures se saisissent en heure de Paris. La base `salle42.db` est créée dans le dossier courant au premier lancement.

L'API, avec sa documentation interactive sur http://127.0.0.1:8000/docs :

```bash
uv run uvicorn salle42.api:app --reload
```

## Tester

```bash
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
```

## Architecture

- `models.py` : les dataclasses `Room` et `Booking`.
- `storage.py` : SQLite, seul accès à la base. Les dates sont stockées en UTC.
- `rules/` : les règles métier, en fonctions pures (`conflicts.py`, `capacity.py`, `slots.py`, `recurrence.py`).
- `services.py` : orchestre stockage et règles ; c'est le point d'entrée de la CLI et de l'API.
- `api.py`, `cli.py` : la présentation, sans aucune règle métier.

## Règles métier

- Deux réservations d'une salle sont en conflit si leurs créneaux se chevauchent **strictement** : 10:00–11:00 et 11:00–12:00 ne sont pas en conflit.
- Une réservation annulée libère son créneau.
- Le nombre de personnes est optionnel ; s'il est donné, il ne dépasse pas la capacité de la salle.
- `--weekly N` crée N réservations, une par semaine, tout ou rien : si un créneau est pris, rien n'est créé et l'erreur indique la première date en conflit. La récurrence garde la même heure de Paris au changement d'heure.

La source de vérité de ces règles est la section « Règles métier » du `CLAUDE.md` et le fichier `.claude/rules/metier.md`.
