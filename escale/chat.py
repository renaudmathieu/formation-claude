"""Turn-by-turn conversation with Claude, in the terminal."""

import base64
import mimetypes
from datetime import date
from pathlib import Path

import anthropic

from escale.llm import send, text_of
from escale.tools.weather import WEATHER_TOOL, WeatherError, run_weather_tool

SUPPORTED_IMAGES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
HELP = "Commandes : /image <chemin> [question], /quitter"
REFUSAL_MESSAGE = "Je ne peux pas répondre à cette demande."
TRUNCATED_MESSAGE = "\n[Réponse coupée : limite de tokens atteinte.]"


def system_prompt(today: date) -> str:
    """Build the system prompt. Claude does not know today's date unless we tell it."""
    return (
        "Tu es Escale, l'assistant de déplacement professionnel d'une entreprise. "
        "Tu réponds en français, de façon concise et concrète. "
        f"Nous sommes le {today.isoformat()}."
    )


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


def run_tool_calls(response) -> list[dict]:
    """Execute every tool call of a response and return one `tool_result` for each."""
    results = []
    for block in response.content:
        if block.type != "tool_use":
            continue
        print(f"[tool] {block.name} {block.input}")
        result = {"type": "tool_result", "tool_use_id": block.id}
        try:
            result["content"] = run_weather_tool(block.input)
        except WeatherError as error:
            # Claude reads the error and can explain it instead of inventing a forecast.
            result["content"] = str(error)
            result["is_error"] = True
        results.append(result)
    return results


class Conversation:
    """Keep the history of a conversation, since the API does not remember anything."""

    def __init__(self, client, today: date | None = None):
        self.client = client
        self.system = system_prompt(today or date.today())
        self.messages: list[dict] = []

    def ask(self, text: str, image_path: str | None = None) -> str:
        """Send one user turn and return the text of Claude's answer."""
        turn_start = len(self.messages)
        content = []
        if image_path:
            content.append(image_block(image_path))
        content.append({"type": "text", "text": text})
        self.messages.append({"role": "user", "content": content})

        try:
            response = self._send()
            if response.stop_reason == "tool_use":
                # All the results go back in a single user message.
                self.messages.append({"role": "assistant", "content": response.content})
                self.messages.append({"role": "user", "content": run_tool_calls(response)})
                # One round trip only: a second tool call is not possible yet, hence "none".
                # This limit is what TP3 removes, by turning this `if` into a loop.
                response = self._send(tool_choice={"type": "none"})
        except (anthropic.APIError, KeyboardInterrupt):
            # Keep the history usable: the failed turn is not part of the conversation.
            del self.messages[turn_start:]
            raise

        if response.stop_reason == "refusal":
            # Keep the history usable: the refused turn is not part of the conversation.
            del self.messages[turn_start:]
            return REFUSAL_MESSAGE
        # Append the whole content, not only the text: thinking blocks must be sent back.
        self.messages.append({"role": "assistant", "content": response.content})
        answer = text_of(response)
        if response.stop_reason == "max_tokens":
            answer += TRUNCATED_MESSAGE
        return answer

    def _send(self, tool_choice: dict | None = None):
        """Call Claude and show why it stopped, which is what drives the program."""
        response = send(
            self.client,
            self.messages,
            system=self.system,
            tools=[WEATHER_TOOL],
            tool_choice=tool_choice,
        )
        print(f"[stop_reason={response.stop_reason}]")
        return response


def parse_image_command(line: str) -> tuple[str, str]:
    """Split `/image <path> [question]` into a path and a question."""
    parts = line.split(maxsplit=2)
    if len(parts) < 2:
        raise ValueError("Usage : /image <chemin> [question]")
    question = parts[2] if len(parts) == 3 else "Que vois-tu sur cette image ?"
    return parts[1], question


def run_chat(client) -> None:
    """Run the conversation loop until the user leaves."""
    conversation = Conversation(client)
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
