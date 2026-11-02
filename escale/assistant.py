"""What makes this agent Escale: its instructions, its tools and how it shows its work."""

from datetime import date
from pathlib import Path

from escale.mcp_client import McpUnavailableError, load_mcp_tools, mcp_url
from escale.toolbox import Tool, Toolbox
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


def remote_tools() -> list[Tool]:
    """Load the MCP tools. An unavailable server must not prevent the agent from working."""
    url = mcp_url()
    try:
        tools = load_mcp_tools(url)
    except McpUnavailableError as error:
        print(f"[mcp] Serveur injoignable ({url}), l'agent continue sans lui : {error}")
        return []
    print(f"[mcp] {url} : {', '.join(tool.name for tool in tools)}")
    return tools


def build_toolbox() -> Toolbox:
    """Gather the tools the agent can use, local and remote."""
    return Toolbox([weather_tool(), *file_tools(OUTPUT_DIR), *remote_tools()])


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
