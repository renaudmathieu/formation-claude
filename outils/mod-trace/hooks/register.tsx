// The "trace" mod: shows what the Escale agent is doing, in a pane beside the chat.
// The agent is a separate program, so the mod cannot see its calls directly. It reads the
// file the agent writes instead. It only observes: it refuses, approves and rewrites nothing.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { TraceEvent } from '../types'

const PANE = 'trace'
const TRACE_FILE = '.escale/trace.jsonl'
const POLL_MS = 1000
const MAX_EVENTS = 500

// Change the tag when the fields of an event change: it declines what an earlier version
// stored, which outlives a reload.
const events = atom({ plugin: 'trace', key: 'events' } as const, [], { shape: 'events-1' })

// Skip lines that are not valid JSON: the agent may be writing the last one right now.
function parseTrace(content: string): TraceEvent[] {
  const parsed: TraceEvent[] = []
  for (const line of content.split('\n')) {
    if (line.trim() === '') continue
    try {
      parsed.push(JSON.parse(line))
    } catch {
      continue
    }
  }
  return parsed.slice(-MAX_EVENTS)
}

// Read the file again, and write the state only when it changed, to avoid useless redraws.
async function refresh($: EngineInterface) {
  let content = ''
  if (await $.fs.exists(TRACE_FILE)) {
    try {
      const raw = await $.fs.read(TRACE_FILE)
      content = typeof raw === 'string' ? raw : ''
    } catch {
      return
    }
  }
  const next = parseTrace(content)
  const current = await read($, events)
  if (JSON.stringify(current) !== JSON.stringify(next)) {
    await update($, events, () => next)
  }
}

function summarize(list: TraceEvent[]) {
  const calls = list.filter(event => event.type === 'api_call')
  return {
    calls: calls.length,
    tools: list.filter(event => event.type === 'tool_call').length,
    errors: list.filter(event => event.type === 'tool_result' && event.is_error).length,
    inputTokens: calls.reduce((sum, event) => sum + (event.input_tokens ?? 0), 0),
    outputTokens: calls.reduce((sum, event) => sum + (event.output_tokens ?? 0), 0),
  }
}

function describe(event: TraceEvent): string {
  switch (event.type) {
    case 'user_message':
      return `vous : ${event.text ?? ''}`
    case 'api_call':
      return `API tour ${event.iteration} : ${event.stop_reason} (${event.input_tokens} > ${event.output_tokens} tokens, ${event.duration_ms} ms)`
    case 'tool_call':
      return `tool ${event.source}/${event.name} ${event.input ?? ''}`
    case 'tool_result':
      return `  ${event.is_error ? 'échec' : 'ok'} ${event.name} (${event.duration_ms} ms)`
  }
}

function colorOf(event: TraceEvent): string | undefined {
  if (event.type === 'tool_result' && event.is_error) return 'red'
  if (event.type === 'tool_call') return event.source === 'local' ? 'cyan' : 'magenta'
  if (event.type === 'api_call' && event.stop_reason !== 'tool_use') {
    return event.stop_reason === 'end_turn' ? 'green' : 'yellow'
  }
  return undefined
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'trace',
      description: "Montrer ce que fait l'agent Escale dans un panneau",
    })
    await refresh($)
    $.clock.every(POLL_MS, () => refresh($))
    return next(e)
  })

  on('command.run', { command: 'trace' }, async $ => {
    await refresh($)
    await $.ui.open({ id: PANE, title: 'Trace Escale' })
    return { text: 'Panneau de trace ouvert.' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const list = await read($, events)
    const total = summarize(list)
    const room = Math.max(1, (e.viewport?.rows ?? 24) - 5)

    return (
      <Box flexDirection="column">
        <Text bold>
          {total.calls} appels API, {total.tools} tools, {total.errors} échecs
        </Text>
        <Text dimColor>
          tokens : {total.inputTokens} en entrée, {total.outputTokens} en sortie
        </Text>
        {list.length === 0 && (
          <Text dimColor>Aucune trace : lancez l'agent dans un autre terminal.</Text>
        )}
        {list.slice(-room).map(event => (
          <Text color={colorOf(event)}>
            {event.time} {describe(event)}
          </Text>
        ))}
      </Box>
    )
  })
}
