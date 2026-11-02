# Formation « Maîtriser Claude Code en 2 jours » : dépôt solution

Ce dépôt est **réservé au formateur**. Il contient le projet fil rouge **Escale** dans son état de départ et une branche solution par TP. Cette branche `formateur` ne contient que cette notice et un script de vérification ; le code est sur les autres branches.

Les supports (modules, guides formateur, kit J-7) sont dans Notion, page « Maîtriser Claude Code en 2 jours ».

## Les branches

| Branche | TP et module | Ce qu'elle contient | Tests attendus |
| --- | --- | --- | --- |
| `main` = `tp/0-depart` | Départ, M3 | Dépendances, helper météo avec un bug planté, politique de voyage fictive, billet fictif | 2 passed, 1 skipped |
| `tp/1-chat` | TP 1, M4 | Appel à la Messages API, image, conversation tour à tour, `CLAUDE.md` | 11 passed, 1 skipped |
| `tp/2-tool` | TP 2, M5 à M7 | Tool `get_weather`, `stop_reason` affiché, un seul aller-retour, bug corrigé et test réactivé | 18 passed |
| `tp/3-agent` | TP 3, M8 | Boucle d'agent, tools de fichiers limités à `sortie/`, `.claude/settings.json`, hook `Stop` | 39 passed |
| `tp/4-mcp` | TP 4, M9 et M10 | Client et serveur MCP, skill `/ajouter-tool` | 46 passed |
| `tp/5-mod` | TP 5, M11 | Trace JSONL et mod `outils/mod-trace/` | 51 passed, et 5 tests du mod |
| `tp/6-rag` | TP 6, M10 | RAG Voyage AI, README complet | 59 passed, et 5 tests du mod |

Chaque checkpoint est un commit au message explicite : `git log --oneline main..tp/6-rag` est le « chemin parcouru » du module 12.

## Le bug planté (ne pas révéler)

| Symptôme | Cause | Corrigé sur |
| --- | --- | --- |
| La météo de « demain » est celle d'après-demain, et le test est ignoré avec un `TODO` | `pick_day` calcule `(target - first_day).days + 1` | `tp/2-tool` |

## Préparer la session

1. **Le dépôt des stagiaires** ne doit contenir que `main` (l'état de départ). Pour le créer depuis ce dépôt :
   ```bash
   git clone --single-branch --branch main git@github.com:renaudmathieu/formation-claude.git escale
   cd escale && git remote set-url origin <url-du-depot-stagiaires> && git push -u origin main
   ```
   Donner un accès en lecture à chaque stagiaire (ou un fork par stagiaire).
2. **Les clés** : créer une clé Anthropic dans un workspace dédié de la Console, avec une limite de dépense, et une clé Voyage AI. Les révoquer après la session. Vérifier que les limites de débit de Voyage tiennent pour le groupe sur une clé partagée.
3. **Le réseau**, avant le J1 : `api.anthropic.com`, `api.voyageai.com`, `api.open-meteo.com`, `geocoding-api.open-meteo.com`, PyPI, et le serveur MCP s'il est partagé.
4. **La veille**, sur ce dépôt : `scripts/verifier-branches.sh` (depuis la branche `formateur`, dans un clone complet). Il passe chaque branche, lance `uv run pytest -q` et `uv run ruff check .`, et vérifie le mod si `claude` est installé.
5. **Versions** : Claude Code 2.1.287 ou plus récent (mods, testé sur 2.1.316), Python 3.12 à 3.14, `uv`.

## Rattraper un retard : le dépôt de secours

Le dépôt des stagiaires ne contient que `main`. Les solutions sont dans le dépôt privé `renaudmathieu/escale-secours`, qui contient les branches `tp/*`. Il reste fermé par défaut : ne l'ouvrir qu'à un stagiaire bloqué, en lecture.

```bash
git remote add secours git@github.com:renaudmathieu/escale-secours.git
git fetch secours tp/3-agent
git switch -c reprise secours/tp/3-agent
```

Après une modification des branches `tp/*` sur ce dépôt : `git push --force-with-lease git@github.com:renaudmathieu/escale-secours.git tp/0-depart tp/1-chat tp/2-tool tp/3-agent tp/4-mcp tp/5-mod tp/6-rag`.

## Serveur MCP partagé (TP 4)

Sur le poste du formateur :

```bash
git switch tp/4-mcp
uv run python -m escale.transport_server --host 0.0.0.0
```

Les stagiaires renseignent `ESCALE_MCP_URL=http://<ip-du-formateur>:8765/mcp` dans `.env`. Ce serveur n'a ni authentification ni chiffrement : uniquement sur un réseau de confiance et le temps du TP. Plan B : chacun lance le serveur en local, sans `--host`.

## Plans de secours

| Panne | Solution |
| --- | --- |
| Open-Meteo surchargé ou bloqué | `ESCALE_METEO=simule` dans `.env` |
| Serveur MCP partagé injoignable | Serveur local : l'agent indique l'erreur et continue sans ces tools |
| Voyage AI bloqué ou limité | Le formateur montre le TP 6 en démonstration |
| Pas de clé Anthropic pour un stagiaire | Binôme : le code et les tests fonctionnent sans clé, seule l'exécution réelle en demande une |
