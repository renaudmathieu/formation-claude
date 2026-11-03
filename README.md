# Escale

Assistant de déplacement professionnel, construit pas à pas avec Claude Code pendant la formation « Maîtriser Claude Code en 2 jours ».

## Installation

```bash
uv sync
cp .env.example .env   # puis renseigner les clés données par le formateur
uv run pytest -q
```

Les tests n'appellent ni l'API ni le réseau : ils passent sans clé.

Sous Windows PowerShell ou en invite de commandes, `cp` peut être remplacé par `copy`.

Pour installer `uv`, suivre [sa documentation](https://docs.astral.sh/uv/getting-started/installation/). Il télécharge lui-même Python si besoin.

Jamais fait de Python ? Lire [docs/python-express.md](docs/python-express.md), 5 minutes suffisent.

Si le service météo ne répond pas, ajouter `ESCALE_METEO=simule` dans `.env`.
