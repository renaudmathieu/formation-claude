// Mod « harnais » : rend visible le harnais de Salle42.
// - Un bandeau au-dessus du prompt : dernier résultat de pytest, soupape
//   rouge-attendu, nombre d'appels d'outils du dernier tour.
// - Une commande /harnais : la carte du harnais du projet (guides, capteurs,
//   barrières), lue dans les fichiers du dépôt.
// Le mod observe seulement : il ne refuse, n'approuve et ne réécrit aucun appel.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Tests } from '../types'

const tests = atom({ plugin: 'harnais', key: 'tests' } as const, null)
const isSoupapeActive = atom({ plugin: 'harnais', key: 'isSoupapeActive' } as const, false)
const appels = atom({ plugin: 'harnais', key: 'appels' } as const, 0)

// Le fichier qui suspend le hook Stop du module 8
const SOUPAPE = '.claude/rouge-attendu'
// Une commande Bash qui lance pytest, sous uv ou non
const PYTEST = /\bpytest\b/

// Relit la soupape sur le disque et ne réécrit l'état que s'il a changé,
// pour ne pas redessiner le bandeau toutes les deux secondes
async function relireSoupape($: EngineInterface) {
  const isActive = await $.fs.exists(SOUPAPE)
  if ((await read($, isSoupapeActive)) !== isActive) {
    await update($, isSoupapeActive, () => isActive)
  }
}

// Extrait « 1 failed, 41 passed » de la sortie de pytest, ou un repli
function resumer(texte: string, isVert: boolean): string {
  const morceaux = ['failed', 'error', 'errors', 'passed', 'skipped']
    .map(mot => new RegExp('(\\d+) ' + mot + '\\b').exec(texte))
    .filter(trouve => trouve !== null)
    .map(trouve => trouve[0])
  if (morceaux.length > 0) return morceaux.join(', ')
  return isVert ? 'sortie sans résumé' : 'échec sans résumé'
}

// Compte des fichiers d'un dossier, 0 s'il n'existe pas
async function compter($: EngineInterface, dossier: string, isDossier: boolean) {
  if (!(await $.fs.exists(dossier))) return 0
  const entrees = await $.fs.list(dossier)
  return entrees.filter(entree => (isDossier ? entree.kind === 'dir' : entree.name.endsWith('.md'))).length
}

// La carte du harnais de Salle42, lue dans les fichiers du dépôt
async function carteDuHarnais($: EngineInterface): Promise<string> {
  const claudeMd = (await $.fs.exists('CLAUDE.md')) ? await $.fs.read('CLAUDE.md') : ''
  const lignes = typeof claudeMd === 'string' && claudeMd !== '' ? claudeMd.replace(/\n$/, '').split('\n').length : 0
  const regles = await compter($, '.claude/rules', false)
  const skills = await compter($, '.claude/skills', true)

  let reglages: {
    permissions?: { deny?: unknown[]; ask?: unknown[] }
    hooks?: { Stop?: unknown[] }
  } = {}
  if (await $.fs.exists('.claude/settings.json')) {
    const brut = await $.fs.read('.claude/settings.json')
    try {
      reglages = JSON.parse(typeof brut === 'string' ? brut : '{}')
    } catch {
      reglages = {}
    }
  }
  const deny = reglages.permissions?.deny?.length ?? 0
  const ask = reglages.permissions?.ask?.length ?? 0
  const hasHookStop = (reglages.hooks?.Stop?.length ?? 0) > 0

  const derniers = await read($, tests)
  const soupape = await read($, isSoupapeActive)

  return [
    'Carte du harnais de Salle42',
    '  Guides    : CLAUDE.md (' + (lignes === 0 ? 'absent' : lignes + ' lignes') + '), ' + regles + ' règle(s) dans .claude/rules, ' + skills + ' skill(s) projet',
    '  Capteurs  : hook Stop ' + (hasHookStop ? 'en place' : 'absent') + (soupape ? ' mais suspendu par la soupape rouge-attendu' : '') + ', dernier pytest ' + (derniers === null ? 'jamais vu dans cette session' : (derniers.isVert ? 'vert' : 'rouge') + ' (' + derniers.resume + ')'),
    '  Barrières : ' + deny + ' règle(s) deny, ' + ask + ' règle(s) ask',
  ].join('\n')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'harnais',
      description: 'Affiche la carte du harnais de Salle42 : guides, capteurs, barrières',
    })
    await relireSoupape($)
    // La soupape se pose à la main (!touch), hors des appels d'outils : on la relit
    $.clock.every(2000, () => relireSoupape($))
    return next(e)
  })

  // Un nouveau prompt ouvre un nouveau tour : on remet le compteur à zéro
  on('prompt.submit', async ($, e, next) => {
    await update($, appels, () => 0)
    return next(e)
  })

  // Chaque appel d'outil, quel qu'il soit, est compté puis passe tel quel
  on('tool.call', async ($, e, next) => {
    await update($, appels, n => n + 1)
    return next(e)
  })

  // Un appel Bash qui lance pytest : on laisse passer, puis on lit le résultat
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (!PYTEST.test(e.command)) return next(e)
    const ran = await next(e)
    // Une commande refusée n'a pas tourné : rien à lire
    if (ran.deny !== undefined) return ran
    const isVert = ran.isError !== true
    const resultat: Tests = { isVert, resume: resumer(ran.text ?? '', isVert) }
    await update($, tests, () => resultat)
    // On rend le résultat tel quel : Claude lit exactement ce que pytest a dit
    return ran
  })

  on('turn.complete', async ($, e, next) => {
    await relireSoupape($)
    return next(e)
  })

  on('command.run', { command: 'harnais' }, async $ => {
    return { text: await carteDuHarnais($) }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    // Un sondage occupe le bandeau : on lui laisse la place
    if (e.props.hasSurvey) return next(e)
    const derniers = await read($, tests)
    const soupape = await read($, isSoupapeActive)
    const n = await read($, appels)
    const { Box, Text } = $.ui.resolve(e)

    // Les clés vont sur les Box : un Text n'en porte pas
    const etat =
      derniers === null
        ? <Text dimColor>aucun pytest vu dans cette session</Text>
        : derniers.isVert
          ? <Text color="green">✓ verts ({derniers.resume})</Text>
          : <Text color="red">✗ rouges ({derniers.resume})</Text>

    return (
      <Box flexDirection="column">
        <Box flexDirection="row" columnGap={1}>
          <Text bold>Harnais</Text>
          <Text dimColor>· Tests :</Text>
          <Box key="tests">{etat}</Box>
          <Box key="appels">
            <Text dimColor>· {n} appel(s) d'outils au dernier tour</Text>
          </Box>
        </Box>
        {soupape && (
          <Box key="soupape">
            <Text color="yellow">
              ⚠ Soupape rouge-attendu active : le hook Stop ne vérifie plus les tests.
            </Text>
          </Box>
        )}
      </Box>
    )
  })
}
