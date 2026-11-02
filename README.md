# Escale

Assistant de déplacement professionnel, construit pas à pas avec Claude Code pendant la formation « Maîtriser Claude Code en 2 jours ». On lui demande de préparer un voyage : il consulte la météo, cherche des trains et des hôtels sur un serveur distant, vérifie la politique de voyage de l'entreprise (fictive) et livre une feuille de route.

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

## Utilisation

```bash
# Dans un premier terminal : le serveur MCP (trains et hôtels fictifs)
uv run python -m escale.transport_server

# Dans un deuxième terminal : l'index de la politique de voyage, une seule fois
uv run python -m escale.rag

# Puis l'agent, sur une tâche...
uv run python -m escale agent "Prépare mes 2 jours à Lyon, départ de Paris mardi prochain"

# ... ou en conversation (et /image exemples/billet-fictif.png pour lire un billet)
uv run python -m escale chat
```

La feuille de route est écrite dans `sortie/`. Chaque exécution consomme du crédit API.

Pour voir l'agent travailler : `claude --plugin-dir ./outils/mod-trace`, puis `/trace` (voir `outils/mod-trace/README.md`).

## Comment ça marche

| Fichier | Rôle |
| --- | --- |
| `escale/llm.py` | Le seul appel à la Messages API |
| `escale/agent.py` | La boucle : `stop_reason` décide de la suite |
| `escale/toolbox.py` | Les tools et leur gestion d'erreur |
| `escale/tools/` | Météo et fichiers (limités à `sortie/`) |
| `escale/mcp_client.py`, `escale/transport_server.py` | Les tools distants |
| `escale/rag.py` | La recherche dans la politique de voyage (Voyage AI) |
| `escale/trace.py`, `outils/mod-trace/` | La trace et le mod qui l'affiche |
| `escale/assistant.py` | Le prompt système et la liste des tools |

## En cas de panne

| Symptôme | Solution |
| --- | --- |
| Service météo indisponible | `ESCALE_METEO=simule` dans `.env` |
| `[mcp] Serveur injoignable` | Lancer `uv run python -m escale.transport_server`, ou vérifier `ESCALE_MCP_URL` |
| `Index absent` | Lancer `uv run python -m escale.rag` |
| Clé API refusée | Vérifier `.env`, sans jamais le coller dans Claude Code |
