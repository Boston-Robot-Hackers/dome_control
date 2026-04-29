#!/usr/bin/env python3
import json
from unittest.mock import MagicMock, patch


def _make_voice_node():
    with patch("rclpy.node.Node.__init__", return_value=None):
        import control.voice_input_node as vin

        node = vin.VoiceInputNode.__new__(vin.VoiceInputNode)
        node.intent_pub = MagicMock()
        node.get_logger = MagicMock(return_value=MagicMock())
        return vin, node


def test_publish_describe_scene_intent_uses_voice_source():
    vin, node = _make_voice_node()

    vin.VoiceInputNode.publish_describe_scene_intent(node)

    node.intent_pub.publish.assert_called_once()
    msg = node.intent_pub.publish.call_args[0][0]
    assert json.loads(msg.data) == {
        "name": "describe_scene",
        "source": "voice",
        "slots": {},
    }


def test_run_porcupine_loop_publishes_on_detection():
    import control.voice_input_node as vin

    on_wake = MagicMock()
    porcupine = MagicMock(frame_length=512)
    porcupine.process.side_effect = [-1, 0]
    recorder = MagicMock()
    recorder.read.return_value = [0] * 512

    with patch.object(vin, "_load_picovoice") as load, patch(
        "control.voice_input_node.rclpy.ok", side_effect=[True, True, False]
    ):
        pvporcupine = MagicMock()
        pvporcupine.create.return_value = porcupine
        recorder_cls = MagicMock(return_value=recorder)
        load.return_value = pvporcupine, recorder_cls

        vin.run_porcupine_loop(on_wake, access_key="key")

    on_wake.assert_called_once_with()
    pvporcupine.create.assert_called_once_with(
        access_key="key", keywords=["jarvis"]
    )
    recorder_cls.assert_called_once_with(device_index=-1, frame_length=512)
    recorder.stop.assert_called_once_with()
    recorder.delete.assert_called_once_with()
    porcupine.delete.assert_called_once_with()
