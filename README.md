# Escale

Assistant de déplacement professionnel, construit pas à pas avec Claude Code pendant la formation « Maîtriser Claude Code en 2 jours ».

## Installation

```bash
uv sync
cp .env.example .env   # puis renseigner les clés données par le formateur
uv run pytest -q
```

Les tests n'appellent ni l'API ni le réseau : ils passent sans clé.

Si le service météo ne répond pas, ajouter `ESCALE_METEO=simule` dans `.env`.
