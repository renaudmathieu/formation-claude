# Escale : assistant de déplacement professionnel

## Commandes
- Installer : `uv sync`. Tests : `uv run pytest -q`. Lint : `uv run ruff check .`
- Lancer : `uv run python -m escale chat` ou `uv run python -m escale ask "question"`

## Architecture
- `escale/llm.py` est le seul fichier qui appelle la Messages API.
- `escale/chat.py` gère la conversation et l'envoi d'images.
- `escale/tools/` contient les tools, sans dépendance à l'API Claude.

## Règles de l'API (à vérifier, pas à deviner)
- L'API ne garde aucun état : chaque appel renvoie tout l'historique.
- On ajoute `response.content` entier à l'historique, blocs de thinking compris.
- On lit `stop_reason` avant d'utiliser la réponse.
- Claude ne connaît pas la date : elle est donnée dans le prompt système.
- Tous les `tool_result` d'une réponse repartent dans un seul message utilisateur.

## Conventions
- Les tests utilisent `tests/fakes.py` : jamais d'appel réseau ni de clé dans un test.
- Commentaires et docstrings en anglais, textes affichés en français.
- Lancer `uv run pytest -q` avant de proposer un commit.

## À ne pas faire
- Ne jamais lire ni afficher `.env`, ne jamais écrire une clé dans un fichier suivi.
- Ne pas faire de `git push`.
