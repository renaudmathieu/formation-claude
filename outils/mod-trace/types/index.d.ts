// One line of .escale/trace.jsonl, as written by escale/trace.py
export type TraceEvent = {
  time: string
  type: 'user_message' | 'api_call' | 'tool_call' | 'tool_result'
  text?: string
  iteration?: number
  model?: string
  stop_reason?: string
  input_tokens?: number
  output_tokens?: number
  duration_ms?: number
  name?: string
  source?: string
  input?: string
  is_error?: boolean
}

declare module 'claude-code' {
  interface PluginState {
    trace: { events: Shaped<TraceEvent[]> }
  }
}
