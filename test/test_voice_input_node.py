#!/usr/bin/env python3
import json
from unittest.mock import MagicMock, patch

from control.announcement_contract import PRIORITY_QUERY_REPLY


def _make_voice_node():
    with patch("rclpy.node.Node.__init__", return_value=None):
        import control.nodes.voice_input_node as vin

        node = vin.VoiceInputNode.__new__(vin.VoiceInputNode)
        node.intent_pub = MagicMock()
        node.state_pub = MagicMock()
        node.announcement_pub = MagicMock()
        node.get_logger = MagicMock(return_value=MagicMock())
        return vin, node


def test_publish_intent():
    _, node = _make_voice_node()
    from control.nodes.voice_input_node import VoiceInputNode
    VoiceInputNode.publish_intent(node, {"name": "stop", "source": "voice", "slots": {}})
    node.intent_pub.publish.assert_called_once()
    msg = node.intent_pub.publish.call_args[0][0]
    assert json.loads(msg.data) == {"name": "stop", "source": "voice", "slots": {}}


def test_publish_state():
    _, node = _make_voice_node()
    from control.nodes.voice_input_node import VoiceInputNode
    VoiceInputNode.publish_state(node, "LISTENING")
    node.state_pub.publish.assert_called_once()
    msg = node.state_pub.publish.call_args[0][0]
    assert msg.data == "LISTENING"


def test_publish_announcement():
    _, node = _make_voice_node()
    from control.nodes.voice_input_node import VoiceInputNode
    VoiceInputNode.publish_announcement(node, "I didn't catch that")
    node.announcement_pub.publish.assert_called_once()
    msg = node.announcement_pub.publish.call_args[0][0]
    assert msg.text == "I didn't catch that"
    assert msg.priority == PRIORITY_QUERY_REPLY
    assert msg.source == "voice_input"


def test_process_transcript_known_intent():
    _, node = _make_voice_node()
    from control.nodes.voice_input_node import VoiceInputNode

    node.intent_mapper = MagicMock()
    node.intent_mapper.map_intent.return_value = {
        "name": "describe_scene", "source": "voice", "slots": {}
    }
    node.publish_state = MagicMock()
    node.publish_intent = MagicMock()
    node.publish_announcement = MagicMock()

    with patch("control.nodes.voice_input_node.beep") as mock_beep:
        VoiceInputNode.process_transcript(node, "what do you see", device_index=2)

    node.publish_state.assert_any_call("PROCESSING")
    node.publish_state.assert_any_call("SPEAKING")
    node.publish_intent.assert_called_once()
    node.publish_announcement.assert_not_called()
    mock_beep.assert_called_once_with(frequency=330, duration=0.02, device_index=2)


def test_process_transcript_unknown_intent():
    _, node = _make_voice_node()
    from control.nodes.voice_input_node import VoiceInputNode

    node.intent_mapper = MagicMock()
    node.intent_mapper.map_intent.return_value = None
    node.publish_state = MagicMock()
    node.publish_intent = MagicMock()
    node.publish_announcement = MagicMock()

    with patch("control.nodes.voice_input_node.speak") as mock_speak:
        VoiceInputNode.process_transcript(node, "blah blah")

    node.publish_state.assert_any_call("PROCESSING")
    node.publish_state.assert_any_call("SPEAKING")
    node.publish_intent.assert_not_called()
    node.publish_announcement.assert_called_once_with("I didn't catch that")
    mock_speak.assert_called_once_with("say again")


def test_process_turn_transcript_path():
    _, node = _make_voice_node()
    from control.voice.runtime import VoiceTurn
    from control.nodes.voice_input_node import VoiceInputNode

    node.process_transcript = MagicMock()
    turn = VoiceTurn(text="stop", raw_text="stop", empty=False)

    VoiceInputNode.process_turn(node, turn, device_index=1)

    node.process_transcript.assert_called_once_with("stop", device_index=1)


def test_process_turn_empty_announces_failure():
    _, node = _make_voice_node()
    from control.voice.runtime import VoiceTurn
    from control.nodes.voice_input_node import VoiceInputNode

    node.publish_state = MagicMock()
    node.publish_announcement = MagicMock()

    with patch("control.nodes.voice_input_node.speak") as mock_speak:
        VoiceInputNode.process_turn(node, VoiceTurn(empty=True))

    node.publish_state.assert_called_once_with("SPEAKING")
    node.publish_announcement.assert_called_once_with("I didn't catch that")
    mock_speak.assert_called_once_with("say again")
