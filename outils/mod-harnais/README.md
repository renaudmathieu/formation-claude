# Mod `harnais`

Le mod du module 11 : il rend visible le harnais de Salle42 dans Claude Code.

- **Un bandeau au-dessus du prompt** : résultat du dernier `pytest` lancé par Claude dans la session (vert ou rouge, avec son résumé), nombre d'appels d'outils du dernier tour, et un avertissement jaune quand la soupape `.claude/rouge-attendu` est posée.
- **Une commande `/harnais`** : la carte du harnais lue dans le dépôt (lignes du `CLAUDE.md`, règles, skills, hook `Stop`, règles `deny` et `ask`).

Le mod **observe seulement** : il ne refuse, n'approuve ni ne réécrit aucun appel, et ne lance aucun processus.

## Utiliser

Claude Code **2.1.287 ou plus récent** (2.1.286 dans l'onglet Code de l'app Desktop), lancé depuis la racine de Salle42 :

```bash
claude --plugin-dir ./outils/mod-harnais
```

Puis `/plugin` (onglet **Installed**) pour vérifier qu'il est chargé, et `/harnais`. Le bandeau ne s'affiche que dans un terminal ou l'app Desktop, pas dans le panneau de chat de VS Code, ni en `claude -p`, ni en session cloud.

## Vérifier

```bash
claude plugin validate outils/mod-harnais
claude plugin test outils/mod-harnais
```

Une fois le mod chargé, Claude Code écrit les types de sa version dans `.claude-plugin/types/` (ignoré par Git) et un `tsconfig.json` ; `npx -p typescript tsc -p outils/mod-harnais` vérifie alors les types.

Testé le 7 octobre 2026 sur Claude Code 2.1.292 : validation passée, 6 tests verts. L'API des mods est en accès anticipé : relancer ces deux commandes après chaque mise à jour de Claude Code.
