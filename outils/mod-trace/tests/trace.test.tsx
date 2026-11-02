import { expect, mock, test } from 'claude-code/testing'

const PANE = {
  plugin: 'trace',
  component: 'Pane',
  requestId: 'trace',
  props: {
    title: 'Trace Escale',
    isFocused: false,
    bodyColumns: 80,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

const line = (event: object) => JSON.stringify({ time: '10:00:00', ...event })

const TRACE = [
  line({ type: 'user_message', text: 'Prépare mon voyage' }),
  line({
    type: 'api_call',
    iteration: 1,
    stop_reason: 'tool_use',
    input_tokens: 100,
    output_tokens: 20,
    duration_ms: 900,
  }),
  line({ type: 'tool_call', name: 'search_hotels', source: 'mcp', input: '{"city": "Lyon"}' }),
  line({ type: 'tool_result', name: 'search_hotels', is_error: true, duration_ms: 12 }),
  line({
    type: 'api_call',
    iteration: 2,
    stop_reason: 'end_turn',
    input_tokens: 150,
    output_tokens: 30,
    duration_ms: 800,
  }),
].join('\n')

// Answer `session.start` and the command registration, as the engine would.
function startSession(on: Parameters<Parameters<typeof test>[1]>[1], content: () => string | null) {
  on('session.start', () => ({ cwd: '/escale' }))
  on('command.register', () => ({ value: { command: 'trace' } }))
  on('fs.exists', () => ({ value: content() !== null }))
  on('fs.read', () => ({ value: content() ?? '' }))
}

const START = { surface: 'terminal', isInteractive: true, cwd: '/escale' } as const

test('the pane says when there is no trace yet', async ($, on) => {
  mock.clock(on)
  startSession(on, () => null)
  await $.session.start(START)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })

  expect(await ui.find({ type: 'Text', text: /Aucune trace/ })).toBeDefined()
  await ui.unmount()
})

test('the pane adds up calls, tools, failures and tokens', async ($, on) => {
  mock.clock(on)
  startSession(on, () => TRACE)
  await $.session.start(START)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })

  expect((await ui.find({ type: 'Text', text: /appels API/ }))?.text).toContain(
    '2 appels API, 1 tools, 1 échecs',
  )
  expect((await ui.find({ type: 'Text', text: /tokens :/ }))?.text).toContain(
    '250 en entrée, 50 en sortie',
  )
  expect((await ui.find({ type: 'Text', text: /mcp\/search_hotels/ }))?.text).toContain('Lyon')
  await ui.unmount()
})

test('new lines appear within a second', async ($, on) => {
  const clock = mock.clock(on)
  let content: string | null = line({ type: 'user_message', text: 'Bonjour' })
  startSession(on, () => content)
  await $.session.start(START)
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /end_turn/ })).toBeUndefined()

  content = TRACE
  await clock.advance(1000)

  expect(await ui.find({ type: 'Text', text: /end_turn/ })).toBeDefined()
  await ui.unmount()
})

test('a line being written does not break the pane', async ($, on) => {
  mock.clock(on)
  startSession(on, () => `${line({ type: 'user_message', text: 'Bonjour' })}\n{"time": "10:0`)
  await $.session.start(START)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })

  expect(await ui.find({ type: 'Text', text: /Bonjour/ })).toBeDefined()
  await ui.unmount()
})

test('the command opens the pane', async ($, on) => {
  mock.clock(on)
  startSession(on, () => null)
  const opened: string[] = []
  on('ui.open', ($, e) => {
    opened.push(e.id)
    return { value: { isPlaced: true } }
  })
  await $.session.start(START)

  await $.command.run({ command: 'trace' })

  expect(opened).toEqual(['trace'])
})
