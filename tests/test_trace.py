import json

from escale.agent import run_agent
from escale.toolbox import Tool, Toolbox
from escale.trace import Tracer, fan_out
from tests.fakes import FakeClient, response, text, tool_use


def records(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_a_run_is_fully_traced(tmp_path):
    path = tmp_path / "trace.jsonl"
    tool = Tool(definition={"name": "echo"}, handler=lambda tool_input: "ok", source="mcp")
    client = FakeClient(
        response(tool_use("echo", {"value": 1}), stop_reason="tool_use"),
        response(text("Fini")),
    )

    run_agent(
        client,
        [{"role": "user", "content": "q"}],
        Toolbox([tool]),
        system="s",
        on_event=Tracer(path),
    )

    lines = records(path)
    assert [line["type"] for line in lines] == [
        "api_call",
        "tool_call",
        "tool_result",
        "api_call",
    ]
    assert lines[0]["stop_reason"] == "tool_use"
    assert lines[0]["input_tokens"] == 10
    assert lines[1]["source"] == "mcp"
    assert lines[2]["is_error"] is False
    assert lines[3]["stop_reason"] == "end_turn"


def test_long_inputs_are_shortened(tmp_path):
    path = tmp_path / "trace.jsonl"
    tracer = Tracer(path)

    tracer({"type": "tool_call", "name": "write_file", "source": "local", "input": {"c": "x" * 999}})

    assert len(records(path)[0]["input"]) < 320


def test_each_run_starts_a_new_file(tmp_path):
    path = tmp_path / "trace.jsonl"
    Tracer(path)({"type": "user_message", "text": "ancien"})

    Tracer(path)({"type": "user_message", "text": "nouveau"})

    assert [line["text"] for line in records(path)] == ["nouveau"]


def test_unwritable_trace_does_not_stop_the_agent(tmp_path, capsys):
    blocker = tmp_path / "fichier"
    blocker.write_text("")
    tracer = Tracer(blocker / "trace.jsonl")

    tracer({"type": "user_message", "text": "q"})

    assert "Écriture impossible" in capsys.readouterr().out


def test_fan_out_reaches_every_listener():
    seen = []

    fan_out(seen.append, seen.append)({"type": "x"})

    assert len(seen) == 2
