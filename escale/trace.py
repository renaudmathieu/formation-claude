"""Write what the agent does to a JSONL file, one event per line, for outside tools to read.

The `outils/mod-trace` mod reads this file. The trace is a side channel: if it cannot be
written, the agent keeps working.
"""

import json
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

TRACE_PATH = Path(".escale/trace.jsonl")
MAX_TEXT_CHARS = 300


def _shorten(value: str) -> str:
    return value if len(value) <= MAX_TEXT_CHARS else f"{value[:MAX_TEXT_CHARS]}..."


class Tracer:
    """Listen to the agent's events. Each run starts a new file, which keeps it small."""

    def __init__(self, path: Path = TRACE_PATH):
        self.path = path
        self.tool_started_at = 0.0
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("", encoding="utf-8")
        except OSError as error:
            print(f"[trace] Écriture impossible, trace désactivée : {error}")

    def __call__(self, event: dict) -> None:
        kind = event["type"]
        if kind == "user_message":
            self._write({"type": "user_message", "text": _shorten(event["text"])})
        elif kind == "response":
            response = event["response"]
            self._write(
                {
                    "type": "api_call",
                    "iteration": event["iteration"],
                    "model": response.model,
                    "stop_reason": response.stop_reason,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "duration_ms": event["duration_ms"],
                }
            )
        elif kind == "tool_call":
            self.tool_started_at = time.monotonic()
            self._write(
                {
                    "type": "tool_call",
                    "name": event["name"],
                    "source": event["source"],
                    "input": _shorten(json.dumps(event["input"], ensure_ascii=False)),
                }
            )
        elif kind == "tool_result":
            self._write(
                {
                    "type": "tool_result",
                    "name": event["name"],
                    "is_error": event["is_error"],
                    "duration_ms": round((time.monotonic() - self.tool_started_at) * 1000),
                }
            )

    def _write(self, record: dict) -> None:
        line = json.dumps(
            {"time": datetime.now().strftime("%H:%M:%S"), **record}, ensure_ascii=False
        )
        try:
            with self.path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
        except OSError as error:
            print(f"[trace] Écriture impossible : {error}")


def fan_out(*listeners: Callable[[dict], None]) -> Callable[[dict], None]:
    """Send each event to several listeners."""

    def listen(event: dict) -> None:
        for listener in listeners:
            listener(event)

    return listen
