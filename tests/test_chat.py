from datetime import date

import pytest

from escale import chat
from escale.tools.weather import WeatherError
from tests.fakes import FakeClient, response, text, thinking, tool_use


def test_second_turn_sends_the_whole_history():
    client = FakeClient(response(text("Bonjour Camille")), response(text("Camille")))
    conversation = chat.Conversation(client)

    conversation.ask("Je m'appelle Camille")
    assert conversation.ask("Comment je m'appelle ?") == "Camille"

    roles = [message["role"] for message in client.requests[1]["messages"]]
    assert roles == ["user", "assistant", "user"]


def test_thinking_blocks_stay_in_the_history():
    client = FakeClient(response(thinking("hmm"), text("Oui")))
    conversation = chat.Conversation(client)

    assert conversation.ask("Ça va ?") == "Oui"

    assert [block.type for block in conversation.messages[1]["content"]] == ["thinking", "text"]


def test_image_is_sent_before_the_question():
    client = FakeClient(response(text("Un billet")))

    chat.Conversation(client).ask("Quoi ?", image_path="exemples/billet-fictif.png")

    image, question = client.requests[0]["messages"][0]["content"]
    assert image["source"]["media_type"] == "image/png"
    assert image["source"]["data"]
    assert question == {"type": "text", "text": "Quoi ?"}


def test_unsupported_image_format_is_rejected():
    with pytest.raises(ValueError):
        chat.image_block("README.md")


def test_refused_turn_leaves_the_history_clean():
    client = FakeClient(response(stop_reason="refusal"))
    conversation = chat.Conversation(client)

    assert conversation.ask("...") == chat.REFUSAL_MESSAGE
    assert conversation.messages == []


def test_truncated_answer_is_flagged():
    client = FakeClient(response(text("Début"), stop_reason="max_tokens"))

    assert chat.TRUNCATED_MESSAGE in chat.Conversation(client).ask("Longue réponse")


def test_system_prompt_gives_the_date():
    client = FakeClient(response(text("Oui")))

    chat.Conversation(client, today=date(2026, 11, 4)).ask("Quel jour ?")

    assert "2026-11-04" in client.requests[0]["system"]


def test_tool_call_goes_through_a_second_request(monkeypatch):
    monkeypatch.setattr(chat, "run_weather_tool", lambda tool_input: '{"max": 12}')
    call = tool_use("get_weather", {"city": "Lyon", "date": "2026-11-05"})
    client = FakeClient(
        response(thinking("il faut la météo"), call, stop_reason="tool_use"),
        response(text("12 degrés")),
    )

    assert chat.Conversation(client).ask("Quel temps demain ?") == "12 degrés"

    second = client.requests[1]
    assert second["tool_choice"] == {"type": "none"}
    assert [block.type for block in second["messages"][1]["content"]] == ["thinking", "tool_use"]
    assert second["messages"][2]["content"] == [
        {"type": "tool_result", "tool_use_id": "toolu_1", "content": '{"max": 12}'}
    ]


def test_parallel_calls_are_answered_in_one_message(monkeypatch):
    monkeypatch.setattr(chat, "run_weather_tool", lambda tool_input: tool_input["city"])
    client = FakeClient(
        response(
            tool_use("get_weather", {"city": "Lyon", "date": "d"}, "a"),
            tool_use("get_weather", {"city": "Nantes", "date": "d"}, "b"),
            stop_reason="tool_use",
        ),
        response(text("Comparaison")),
    )

    chat.Conversation(client).ask("Lyon ou Nantes ?")

    results = client.requests[1]["messages"][2]["content"]
    assert [(r["tool_use_id"], r["content"]) for r in results] == [("a", "Lyon"), ("b", "Nantes")]


def test_tool_failure_is_reported_to_claude(monkeypatch):
    def fail(tool_input):
        raise WeatherError("Service météo indisponible")

    monkeypatch.setattr(chat, "run_weather_tool", fail)
    client = FakeClient(
        response(tool_use("get_weather", {"city": "Lyon", "date": "d"}), stop_reason="tool_use"),
        response(text("Désolé")),
    )

    chat.Conversation(client).ask("Météo ?")

    result = client.requests[1]["messages"][2]["content"][0]
    assert result["is_error"] is True
    assert "indisponible" in result["content"]


def test_image_command_has_a_default_question():
    assert chat.parse_image_command("/image a.png")[0] == "a.png"
    assert chat.parse_image_command("/image a.png Quel train ?") == ("a.png", "Quel train ?")


def test_interrupted_turn_leaves_the_history_clean():
    client = FakeClient(response(text("Bonjour")), KeyboardInterrupt())
    chat_session = chat.Conversation(client)
    chat_session.ask("Bonjour")

    with pytest.raises(KeyboardInterrupt):
        chat_session.ask("Et ensuite ?")

    assert [message["role"] for message in chat_session.messages] == ["user", "assistant"]
