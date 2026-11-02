"""Turn-by-turn conversation with the agent, in the terminal."""

import base64
import mimetypes
from datetime import date
from pathlib import Path

import anthropic

from escale.agent import AgentResult, run_agent
from escale.assistant import build_toolbox, show_progress, system_prompt
from escale.toolbox import Toolbox
from escale.trace import Tracer, fan_out

SUPPORTED_IMAGES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
HELP = "Commandes : /image <chemin> [question], /quitter"
REFUSAL_MESSAGE = "Je ne peux pas répondre à cette demande."
TRUNCATED_MESSAGE = "\n[Réponse coupée : limite de tokens atteinte.]"
LIMIT_MESSAGE = "\n[Arrêt : limite de tours atteinte, le travail est peut-être incomplet.]"


def image_block(path: str) -> dict:
    """Build the content block that sends a local image to Claude."""
    media_type, _ = mimetypes.guess_type(path)
    if media_type not in SUPPORTED_IMAGES:
        raise ValueError(f"Format d'image non pris en charge : {path}")
    data = base64.standard_b64encode(Path(path).read_bytes()).decode("ascii")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }


def describe(result: AgentResult) -> str:
    """Turn the way a run ended into what the user reads."""
    if result.stop_reason == "refusal":
        return REFUSAL_MESSAGE
    if result.stop_reason == "max_tokens":
        return result.text + TRUNCATED_MESSAGE
    if result.stop_reason == "iteration_limit":
        return result.text + LIMIT_MESSAGE
    return result.text


class Conversation:
    """Keep the history of a conversation, since the API does not remember anything."""

    def __init__(self, client, toolbox: Toolbox, today: date | None = None, on_event=show_progress):
        self.client = client
        self.toolbox = toolbox
        self.system = system_prompt(today or date.today())
        self.on_event = on_event
        self.messages: list[dict] = []

    def ask(self, text: str, image_path: str | None = None) -> str:
        """Send one user turn, let the agent work, and return what the user should read."""
        turn_start = len(self.messages)
        content = []
        if image_path:
            content.append(image_block(image_path))
        content.append({"type": "text", "text": text})
        self.messages.append({"role": "user", "content": content})
        self.on_event({"type": "user_message", "text": text})

        try:
            result = run_agent(
                self.client,
                self.messages,
                self.toolbox,
                system=self.system,
                effort="low",
                on_event=self.on_event,
            )
        except BaseException:
            # Keep the history usable: a tool_use without its result would be rejected next time.
            del self.messages[turn_start:]
            raise
        if result.stop_reason == "refusal":
            # Keep the history usable: the refused turn is not part of the conversation.
            del self.messages[turn_start:]
        return describe(result)


def parse_image_command(line: str) -> tuple[str, str]:
    """Split `/image <path> [question]` into a path and a question."""
    parts = line.split(maxsplit=2)
    if len(parts) < 2:
        raise ValueError("Usage : /image <chemin> [question]")
    question = parts[2] if len(parts) == 3 else "Que vois-tu sur cette image ?"
    return parts[1], question


def run_chat(client) -> None:
    """Run the conversation loop until the user leaves."""
    conversation = Conversation(client, build_toolbox(), on_event=fan_out(show_progress, Tracer()))
    print(f"Escale est prêt. {HELP}")
    while True:
        try:
            line = input("\nvous> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        if line == "/quitter":
            return
        try:
            if line.startswith("/image"):
                path, question = parse_image_command(line)
                answer = conversation.ask(question, image_path=path)
            else:
                answer = conversation.ask(line)
        except (OSError, ValueError) as error:
            print(f"Erreur : {error}")
            continue
        except anthropic.APIError as error:
            print(f"Erreur de l'API, le tour est annulé : {error.message}")
            continue
        except KeyboardInterrupt:
            print("\n[Tour interrompu.]")
            continue
        print(f"\nescale> {answer}")


def run_task(client, task: str) -> AgentResult:
    """Give the agent one task and let it work until it has finished."""
    on_event = fan_out(show_progress, Tracer())
    on_event({"type": "user_message", "text": task})
    return run_agent(
        client,
        [{"role": "user", "content": task}],
        build_toolbox(),
        system=system_prompt(date.today()),
        effort="high",
        on_event=on_event,
    )
