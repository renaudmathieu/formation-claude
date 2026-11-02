# Mod `trace`

Le mod du module 11 : un panneau qui montre en direct ce que fait l'agent Escale (appels à l'API, `stop_reason`, tools locaux et distants, tokens).

L'agent est un programme séparé : le mod ne voit pas ses appels. L'agent écrit donc `.escale/trace.jsonl`, et le mod relit ce fichier chaque seconde.

Le mod **observe seulement** : il ne refuse, n'approuve ni ne réécrit aucun appel, et ne lance aucun processus.

## Utiliser

Depuis la racine d'Escale, dans un terminal :

```bash
claude --plugin-dir ./outils/mod-trace
```

Dans Claude Code, taper `/trace`. Dans un autre terminal, lancer l'agent :

```bash
uv run python -m escale agent "Prépare mes 2 jours à Lyon"
```

Le panneau ne s'affiche ni dans le panneau de chat de VS Code, ni en `claude -p`. Utiliser le terminal intégré de l'IDE.

## Vérifier

```bash
claude plugin validate outils/mod-trace
claude plugin test outils/mod-trace
```

Testé avec Claude Code 2.1.316. L'API des mods évolue : les types écrits par Claude Code dans `.claude-plugin/types/` font foi.
