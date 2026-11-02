"""What makes this agent Escale: its instructions, its tools and how it shows its work."""

from datetime import date
from pathlib import Path

from escale.toolbox import Toolbox
from escale.tools.files import file_tools
from escale.tools.weather import weather_tool

OUTPUT_DIR = Path("sortie")


def system_prompt(today: date) -> str:
    """Build the system prompt. Claude does not know today's date unless we tell it."""
    return (
        "Tu es Escale, l'assistant de déplacement professionnel d'une entreprise. "
        "Tu réponds en français, de façon concise et concrète. "
        f"Nous sommes le {today.isoformat()}.\n\n"
        "Quand on te demande de préparer un déplacement, travaille en autonomie : rassemble les "
        "informations avec tes outils, puis livre une feuille de route en Markdown avec "
        "write_file. Si une information manque ou qu'un outil échoue, dis-le dans le document "
        "au lieu de l'inventer."
    )


def build_toolbox() -> Toolbox:
    """Gather the tools the agent can use."""
    return Toolbox([weather_tool(), *file_tools(OUTPUT_DIR)])


def show_progress(event: dict) -> None:
    """Print what the agent is doing, so that the loop can be seen."""
    if event["type"] == "response":
        response = event["response"]
        for block in response.content:
            if block.type == "thinking" and block.thinking:
                print(f"[réflexion] {block.thinking}")
        print(f"[tour {event['iteration']}] stop_reason={response.stop_reason}")
    elif event["type"] == "tool_call":
        print(f"[tool] {event['name']} {_shorten(str(event['input']))}")
    elif event["type"] == "tool_result" and event["is_error"]:
        print(f"[tool] {event['name']} a échoué")


def _shorten(value: str, limit: int = 200) -> str:
    return value if len(value) <= limit else f"{value[:limit]}..."
