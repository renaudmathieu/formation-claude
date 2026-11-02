"""Retrieval over the travel policy: index the documents once, then search them by meaning.

Build the index with `uv run python -m escale.rag`. There is no vector database here: with a few
dozen passages, a cosine similarity over a numpy matrix is enough, and everything stays visible.
"""

import json
import os
from pathlib import Path

import numpy as np
import voyageai
from dotenv import load_dotenv

from escale.toolbox import Tool, ToolError

DOCUMENTS_DIR = Path("data/politique-voyage")
INDEX_PATH = Path("data/index.json")
EMBEDDING_MODEL = "voyage-4-lite"
TOP_K = 3


def split_document(path: Path) -> list[dict]:
    """Cut a Markdown document into one passage per `##` section."""
    passages = []
    title = heading = None
    lines: list[str] = []

    def flush() -> None:
        body = " ".join(line for line in lines if line.strip())
        if heading and body:
            passages.append(
                {"source": f"{path.name}#{heading}", "text": f"{title}, {heading}. {body}"}
            )

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            heading = line[3:].strip()
            lines = []
        elif heading:
            lines.append(line)
    flush()
    return passages


def voyage_embedder(input_type: str):
    """Return a function that embeds texts with Voyage AI.

    Documents and queries use different `input_type` values: this improves retrieval.
    """

    def embed(texts: list[str]) -> list[list[float]]:
        # A shared key can hit rate limits during a course: retry instead of failing at once.
        client = voyageai.Client(max_retries=3)
        return client.embed(texts, model=EMBEDDING_MODEL, input_type=input_type).embeddings

    return embed


def build_index(documents_dir: Path, index_path: Path, embed) -> int:
    """Embed every passage and save the index. Return the number of passages."""
    passages = [p for path in sorted(documents_dir.glob("*.md")) for p in split_document(path)]
    if not passages:
        raise ValueError(f"Aucun passage trouvé dans {documents_dir}")
    vectors = embed([passage["text"] for passage in passages])
    index = {
        "model": EMBEDDING_MODEL,
        "passages": [{**p, "vector": v} for p, v in zip(passages, vectors, strict=True)],
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return len(passages)


def rank(query_vector: list[float], passages: list[dict], top_k: int = TOP_K) -> list[dict]:
    """Return the passages closest to the query, by cosine similarity."""
    matrix = np.array([passage["vector"] for passage in passages])
    query = np.array(query_vector)
    scores = matrix @ query / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(query))
    best = np.argsort(scores)[::-1][:top_k]
    return [
        {
            "source": passages[i]["source"],
            "text": passages[i]["text"],
            "score": round(float(scores[i]), 3),
        }
        for i in best
    ]


def rag_tool(index_path: Path = INDEX_PATH, embed=None) -> Tool:
    """Build the search tool. The index is read when the tool is used."""
    embed = embed or voyage_embedder("query")

    def search(tool_input: dict) -> str:
        if not index_path.exists():
            raise ToolError(
                "Index absent : lancer `uv run python -m escale.rag` pour le construire."
            )
        passages = json.loads(index_path.read_text(encoding="utf-8"))["passages"]
        try:
            query_vector = embed([tool_input["query"]])[0]
        except voyageai.error.VoyageError as error:
            raise ToolError(f"Recherche indisponible (Voyage AI) : {error}") from error
        return json.dumps(rank(query_vector, passages), ensure_ascii=False)

    return Tool(
        definition={
            "name": "search_travel_policy",
            "description": (
                "Cherche dans la politique de voyage de l'entreprise : plafonds d'hôtel et de "
                "repas, classe de train, avion, taxi, notes de frais. Cette politique est propre "
                "à l'entreprise : utilise cet outil avant de citer une règle ou un montant, et "
                "indique la source du passage utilisé."
            ),
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La question, par exemple : plafond d'hôtel à Lyon.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        handler=search,
        source="rag",
    )


def main() -> None:
    load_dotenv()
    if not os.environ.get("VOYAGE_API_KEY"):
        raise SystemExit("VOYAGE_API_KEY manquante : la renseigner dans .env.")
    count = build_index(DOCUMENTS_DIR, INDEX_PATH, voyage_embedder("document"))
    print(f"{count} passages indexés dans {INDEX_PATH}")


if __name__ == "__main__":
    main()
