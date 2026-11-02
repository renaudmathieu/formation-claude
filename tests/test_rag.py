import json
from pathlib import Path

import pytest

from escale import rag
from escale.agent import run_agent
from escale.toolbox import Toolbox
from tests.fakes import FakeClient, response, text, tool_use

# Fake embeddings: each keyword is one axis, so similarity is easy to predict.
KEYWORDS = ["hôtel", "train", "repas"]


def fake_embed(texts: list[str]) -> list[list[float]]:
    return [[1.0 + t.lower().count(word) * 10 for word in KEYWORDS] for t in texts]


@pytest.fixture
def index_path(tmp_path) -> Path:
    documents = tmp_path / "docs"
    documents.mkdir()
    (documents / "a.md").write_text(
        "# Hébergement\n\nIntroduction ignorée.\n\n## Plafonds\n\nHôtel à 140 € par nuit.\n\n"
        "## Choix\n\nUn hôtel proche.\n",
        encoding="utf-8",
    )
    (documents / "b.md").write_text("# Transport\n\n## Train\n\nTrain en seconde classe.\n")
    path = tmp_path / "index.json"
    assert rag.build_index(documents, path, fake_embed) == 3
    return path


def test_split_keeps_one_passage_per_section_with_its_source():
    passages = rag.split_document(rag.DOCUMENTS_DIR / "hebergement.md")

    assert [p["source"] for p in passages] == [
        "hebergement.md#Plafonds par nuit",
        "hebergement.md#Durée du séjour",
        "hebergement.md#Choix de l'hôtel",
    ]
    assert "140 €" in passages[0]["text"]
    assert passages[0]["text"].startswith("Hébergement, Plafonds par nuit.")


def test_whole_policy_can_be_split():
    passages = [p for f in rag.DOCUMENTS_DIR.glob("*.md") for p in rag.split_document(f)]

    assert len(passages) == 10


def test_empty_folder_is_an_error(tmp_path):
    with pytest.raises(ValueError):
        rag.build_index(tmp_path, tmp_path / "index.json", fake_embed)


def test_rank_puts_the_closest_passage_first():
    passages = [
        {"source": "x", "text": "x", "vector": [1.0, 0.0]},
        {"source": "y", "text": "y", "vector": [0.0, 1.0]},
    ]

    ranked = rag.rank([0.1, 0.9], passages, top_k=1)

    assert [p["source"] for p in ranked] == ["y"]


def test_search_tool_finds_the_right_passage_and_its_source(index_path):
    tool = rag.rag_tool(index_path, embed=fake_embed)

    results = json.loads(tool.handler({"query": "train"}))

    assert results[0]["source"] == "b.md#Train"
    assert "vector" not in results[0]


def test_missing_index_is_an_error_result_with_the_fix(tmp_path):
    tool = rag.rag_tool(tmp_path / "absent.json", embed=fake_embed)

    content, is_error = Toolbox([tool]).run("search_travel_policy", {"query": "hôtel"})

    assert is_error
    assert "escale.rag" in content


def test_voyage_failure_is_an_error_result(index_path):
    def failing(texts):
        raise rag.voyageai.error.RateLimitError("trop de requêtes")

    tool = rag.rag_tool(index_path, embed=failing)

    content, is_error = Toolbox([tool]).run("search_travel_policy", {"query": "hôtel"})

    assert is_error
    assert "trop de requêtes" in content


def test_agent_gets_the_policy_through_the_tool(index_path):
    client = FakeClient(
        response(tool_use("search_travel_policy", {"query": "hôtel"}), stop_reason="tool_use"),
        response(text("Plafond : 140 €")),
    )
    box = Toolbox([rag.rag_tool(index_path, embed=fake_embed)])

    result = run_agent(client, [{"role": "user", "content": "Plafond ?"}], box, system="s")

    assert result.text == "Plafond : 140 €"
    assert "140 €" in client.requests[1]["messages"][-1]["content"][0]["content"]
