import { expect, mock, test } from 'claude-code/testing'

// Le bandeau au-dessus du prompt, tel que le moteur le demande
const BAND = {
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 10,
    bodyColumns: 100,
    scroll: { offset: 0, bodyRows: 10 },
    view: {},
  },
} as const

const SURFACES = ['terminal', 'desktop'] as const

// Le moteur résout les chemins depuis le dossier de travail : on compare par la fin
const fichier = (chemin: string) =>
  Object.keys(DEPOT).find(nom => chemin === nom || chemin.endsWith('/' + nom))

// Les fichiers de Salle42 au checkpoint etape/09-skill, en mémoire
const DEPOT: Record<string, string> = {
  'CLAUDE.md': '# Salle42\n\n## Commandes\n- Tests : `uv run pytest -q`\n',
  '.claude/settings.json': JSON.stringify({
    permissions: {
      allow: ['Bash(uv run pytest *)'],
      ask: ['Bash(rm *)', 'Bash(uv add *)'],
      deny: ['Bash(git push *)', 'Bash(git reset --hard *)', 'Read(./.env)'],
    },
    hooks: { Stop: [{ hooks: [{ type: 'command', command: 'tests-verts.sh' }] }] },
  }),
}

test('sans pytest, le bandeau le dit', async ($, on) => {
  mock.clock(on)
  on('fs.exists', () => ({ value: false }))
  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ plugin: 'harnais', surface, ...BAND })
    expect((await ui.find({ key: 'tests' }))?.text).toContain('aucun pytest vu')
    expect(await ui.find({ key: 'soupape' })).toBeUndefined()
    await ui.unmount()
  }
})

test('un pytest rouge passe le bandeau au rouge, sans changer ce que Claude lit', async ($, on) => {
  mock.clock(on)
  on('fs.exists', () => ({ value: false }))
  // Le test répond à la place de Bash : pytest échoue
  on('tool.call', () => ({
    result: { stdout: '1 failed, 41 passed in 0.42s', stderr: '', interrupted: false },
    text: 'FAILED tests/test_smoke.py::test_book_without_attendees\n1 failed, 41 passed in 0.42s',
    isError: true,
  }))
  const ran = await $.tool.call({ tool: 'Bash', command: 'uv run pytest -q' })
  // Le mod observe : le résultat revient tel quel
  expect(ran.isError).toBe(true)
  expect(ran.text).toContain('1 failed, 41 passed')
  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ plugin: 'harnais', surface, ...BAND })
    expect((await ui.find({ key: 'tests' }))?.text).toContain('rouges (1 failed, 41 passed)')
    expect((await ui.find({ key: 'appels' }))?.text).toContain('1 appel')
    await ui.unmount()
  }
})

test('un pytest vert passe le bandeau au vert', async ($, on) => {
  mock.clock(on)
  on('fs.exists', () => ({ value: false }))
  on('tool.call', () => ({
    result: { stdout: '42 passed in 0.40s', stderr: '', interrupted: false },
    text: '42 passed in 0.40s',
  }))
  await $.tool.call({ tool: 'Bash', command: 'uv run pytest -q' })
  const ui = await $.ui.mount({ plugin: 'harnais', surface: 'terminal', ...BAND })
  expect((await ui.find({ key: 'tests' }))?.text).toContain('verts (42 passed)')
  await ui.unmount()
})

test("une autre commande Bash ne touche pas à l'état des tests", async ($, on) => {
  mock.clock(on)
  on('fs.exists', () => ({ value: false }))
  on('tool.call', () => ({ result: { stdout: 'README.md', stderr: '', interrupted: false }, text: 'README.md' }))
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  const ui = await $.ui.mount({ plugin: 'harnais', surface: 'terminal', ...BAND })
  expect((await ui.find({ key: 'tests' }))?.text).toContain('aucun pytest vu')
  expect((await ui.find({ key: 'appels' }))?.text).toContain('1 appel')
  await ui.unmount()
})

test('la soupape posée à la main apparaît dans les deux secondes', async ($, on) => {
  const clock = mock.clock(on)
  let isPosee = false
  on('fs.exists', ($, e) => ({ value: isPosee && e.path.endsWith('.claude/rouge-attendu') }))
  // session.start ne part pas tout seul dans un test : c'est lui qui lance le timer
  on('session.start', () => ({ cwd: '/salle42' }))
  on('command.register', () => ({ value: { command: 'harnais' } }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/salle42' })
  const ui = await $.ui.mount({ plugin: 'harnais', surface: 'terminal', ...BAND })
  expect(await ui.find({ key: 'soupape' })).toBeUndefined()
  // Le stagiaire tape !touch .claude/rouge-attendu
  isPosee = true
  await clock.advance(2000)
  expect((await ui.find({ key: 'soupape' }))?.text).toContain('Soupape rouge-attendu active')
  // Puis !rm .claude/rouge-attendu
  isPosee = false
  await clock.advance(2000)
  expect(await ui.find({ key: 'soupape' })).toBeUndefined()
  await ui.unmount()
})

test('/harnais dresse la carte du harnais depuis les fichiers du dépôt', async ($, on) => {
  mock.clock(on)
  on('fs.exists', ($, e) => ({ value: fichier(e.path) !== undefined }))
  on('fs.read', ($, e) => ({ value: DEPOT[fichier(e.path) ?? ''] ?? '' }))
  on('fs.list', () => ({ value: [] }))
  const reponse = await $.command.run({
    command: 'harnais',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 100 },
  })
  expect(reponse.text).toContain('CLAUDE.md (4 lignes)')
  expect(reponse.text).toContain('hook Stop en place')
  expect(reponse.text).toContain('3 règle(s) deny, 2 règle(s) ask')
})
