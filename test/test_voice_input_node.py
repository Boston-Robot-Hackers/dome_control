#!/usr/bin/env python3
import json
from unittest.mock import MagicMock, patch


def _make_voice_node():
    with patch("rclpy.node.Node.__init__", return_value=None):
        import control.voice_input_node as vin

        node = vin.VoiceInputNode.__new__(vin.VoiceInputNode)
        node.intent_pub = MagicMock()
        node.state_pub = MagicMock()
        node.announcement_pub = MagicMock()
        node.get_logger = MagicMock(return_value=MagicMock())
        return vin, node


def test_publish_intent():
    _, node = _make_voice_node()
    from control.voice_input_node import VoiceInputNode
    VoiceInputNode.publish_intent(node, {"name": "stop", "source": "voice", "slots": {}})
    node.intent_pub.publish.assert_called_once()
    msg = node.intent_pub.publish.call_args[0][0]
    assert json.loads(msg.data) == {"name": "stop", "source": "voice", "slots": {}}


def test_publish_state():
    _, node = _make_voice_node()
    from control.voice_input_node import VoiceInputNode
    VoiceInputNode.publish_state(node, "LISTENING")
    node.state_pub.publish.assert_called_once()
    msg = node.state_pub.publish.call_args[0][0]
    assert msg.data == "LISTENING"


def test_publish_announcement():
    _, node = _make_voice_node()
    from control.voice_input_node import VoiceInputNode
    VoiceInputNode.publish_announcement(node, "I didn't catch that")
    node.announcement_pub.publish.assert_called_once()
    msg = node.announcement_pub.publish.call_args[0][0]
    assert msg.data == "I didn't catch that"
