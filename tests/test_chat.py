from datetime import date

import pytest

from escale import chat
from escale.toolbox import Tool, Toolbox
from tests.fakes import FakeClient, response, text, thinking, tool_use


def conversation(client, today=None) -> chat.Conversation:
    weather = Tool(definition={"name": "get_weather"}, handler=lambda tool_input: '{"max": 12}')
    return chat.Conversation(client, Toolbox([weather]), today=today, on_event=lambda event: None)


def test_second_turn_sends_the_whole_history():
    client = FakeClient(response(text("Bonjour Camille")), response(text("Camille")))
    chat_session = conversation(client)

    chat_session.ask("Je m'appelle Camille")
    assert chat_session.ask("Comment je m'appelle ?") == "Camille"

    roles = [message["role"] for message in client.requests[1]["messages"]]
    assert roles == ["user", "assistant", "user"]


def test_thinking_blocks_stay_in_the_history():
    client = FakeClient(response(thinking("hmm"), text("Oui")))
    chat_session = conversation(client)

    assert chat_session.ask("Ça va ?") == "Oui"

    assert [block.type for block in chat_session.messages[1]["content"]] == ["thinking", "text"]


def test_image_is_sent_before_the_question():
    client = FakeClient(response(text("Un billet")))

    conversation(client).ask("Quoi ?", image_path="exemples/billet-fictif.png")

    image, question = client.requests[0]["messages"][0]["content"]
    assert image["source"]["media_type"] == "image/png"
    assert image["source"]["data"]
    assert question == {"type": "text", "text": "Quoi ?"}


def test_unsupported_image_format_is_rejected():
    with pytest.raises(ValueError):
        chat.image_block("README.md")


def test_refused_turn_leaves_the_history_clean():
    client = FakeClient(response(stop_reason="refusal"))
    chat_session = conversation(client)

    assert chat_session.ask("...") == chat.REFUSAL_MESSAGE
    assert chat_session.messages == []


def test_truncated_answer_is_flagged():
    client = FakeClient(response(text("Début"), stop_reason="max_tokens"))

    assert chat.TRUNCATED_MESSAGE in conversation(client).ask("Longue réponse")


def test_system_prompt_gives_the_date():
    client = FakeClient(response(text("Oui")))

    conversation(client, today=date(2026, 11, 4)).ask("Quel jour ?")

    assert "2026-11-04" in client.requests[0]["system"]


def test_a_turn_can_use_a_tool_then_answer():
    client = FakeClient(
        response(tool_use("get_weather", {"city": "Lyon"}), stop_reason="tool_use"),
        response(text("12 degrés")),
    )

    assert conversation(client).ask("Quel temps demain ?") == "12 degrés"
    tool_result = client.requests[1]["messages"][-1]["content"][0]
    assert tool_result["content"] == '{"max": 12}'


def test_image_command_has_a_default_question():
    assert chat.parse_image_command("/image a.png")[0] == "a.png"
    assert chat.parse_image_command("/image a.png Quel train ?") == ("a.png", "Quel train ?")


def test_interrupted_turn_leaves_the_history_clean():
    client = FakeClient(response(text("Bonjour")), KeyboardInterrupt())
    chat_session = conversation(client)
    chat_session.ask("Bonjour")

    with pytest.raises(KeyboardInterrupt):
        chat_session.ask("Et ensuite ?")

    assert [message["role"] for message in chat_session.messages] == ["user", "assistant"]
