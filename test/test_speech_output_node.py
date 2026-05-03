#!/usr/bin/env python3
import json
from unittest.mock import MagicMock, patch

from std_msgs.msg import String

from control.announcement_contract import (
    Announcement,
    PRIORITY_CHITCHAT,
    PRIORITY_QUERY_REPLY,
)
from control.speech_output_node import (
    play_wav,
    synthesize_to_wav,
)


def _make_node():
    with patch("rclpy.node.Node.__init__", return_value=None):
        from control.speech_output_node import SpeechOutputNode

        node = SpeechOutputNode.__new__(SpeechOutputNode)
        node.get_logger = MagicMock(return_value=MagicMock())
        node.piper_bin = "piper"
        node.piper_model_path = "/tmp/model.onnx"
        node.alsa_device = "hw:1,0"
        node.speak_text = MagicMock()
        return SpeechOutputNode, node


def test_parse_announcement_payload_json():
    payload = json.dumps(
        {
            "text": "I see a can",
            "priority": PRIORITY_QUERY_REPLY,
            "source": "behavior_manager",
        }
    )
    parsed = Announcement.from_payload(payload)
    assert parsed == Announcement(
        text="I see a can",
        priority=PRIORITY_QUERY_REPLY,
        source="behavior_manager",
    )


def test_parse_announcement_payload_plain_text():
    parsed = Announcement.from_payload("hello robot")
    assert parsed == Announcement(
        text="hello robot",
        priority=PRIORITY_CHITCHAT,
        source="unknown",
    )


def test_parse_announcement_payload_empty_text():
    parsed = Announcement.from_payload("   ")
    assert parsed.text == ""


def test_on_announcement_calls_speak_text():
    SpeechOutputNode, node = _make_node()
    msg = String()
    msg.data = "hello there"
    SpeechOutputNode.on_announcement(node, msg)
    node.speak_text.assert_called_once_with("hello there")


def test_on_announcement_ignores_empty():
    SpeechOutputNode, node = _make_node()
    msg = String()
    msg.data = "   "
    SpeechOutputNode.on_announcement(node, msg)
    node.speak_text.assert_not_called()


@patch("control.speech_output_node.subprocess.run")
def test_synthesize_to_wav_invokes_piper(mock_run):
    synthesize_to_wav(
        text="test speech",
        wav_path="/tmp/out.wav",
        piper_bin="piper",
        model_path="/tmp/model.onnx",
    )
    mock_run.assert_called_once()
    cmd = mock_run.call_args.args[0]
    assert cmd[:2] == ["piper", "--model"]
    assert "/tmp/model.onnx" in cmd
    assert "--output_file" in cmd
    assert "/tmp/out.wav" in cmd


@patch("control.speech_output_node.subprocess.run")
def test_play_wav_invokes_aplay(mock_run):
    play_wav("/tmp/out.wav", alsa_device="hw:1,0")
    mock_run.assert_called_once_with(
        ["aplay", "-D", "hw:1,0", "/tmp/out.wav"],
        check=True,
        capture_output=True,
    )
