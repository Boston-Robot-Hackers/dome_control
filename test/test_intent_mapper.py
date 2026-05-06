#!/usr/bin/env python3
from control.voice.intent_mapper import IntentMapper, map_intent


def test_describe_scene():
    assert map_intent("what do you see")["name"] == "describe_scene"
    assert map_intent("describe the scene")["name"] == "describe_scene"


def test_stop():
    assert map_intent("stop")["name"] == "stop"
    assert map_intent("halt")["name"] == "stop"


def test_tuned_motion_phrases():
    assert map_intent("go forward")["name"] == "move_forward"
    assert map_intent("go backward")["name"] == "move_backward"
    assert map_intent("turn left")["name"] == "turn_left"
    assert map_intent("turn right")["name"] == "turn_right"


def test_return_home_words_are_not_voice_intents():
    assert map_intent("go home") is None
    assert map_intent("come back") is None
    assert map_intent("home") is None


def test_explore():
    assert map_intent("start exploring")["name"] == "start_exploring"
    assert map_intent("explore")["name"] == "start_exploring"


def test_follow_words_are_not_voice_intents():
    assert map_intent("follow me") is None
    assert map_intent("follow") is None


def test_count_objects_with_slot():
    result = map_intent("how many cans do you see")
    assert result["name"] == "count_objects"
    assert result["slots"]["object_type"] == "can"


def test_count_objects_no_slot():
    result = map_intent("how many")
    assert result["name"] == "count_objects"
    assert result["slots"] == {}


def test_get_battery():
    assert map_intent("battery level")["name"] == "get_battery"


def test_get_location():
    assert map_intent("where are you")["name"] == "get_location"


def test_sleep_words_are_not_voice_intents():
    assert map_intent("go to sleep") is None
    assert map_intent("sleep") is None


def test_wake_words_are_not_voice_intents():
    assert map_intent("wake up") is None


def test_unknown_returns_none():
    assert map_intent("") is None
    assert map_intent("[unk]") is None
    assert map_intent("blah blah blah") is None


def test_source_is_voice():
    result = map_intent("stop")
    assert result["source"] == "voice"


def test_intent_mapper_class_api():
    mapper = IntentMapper()
    assert mapper.map_intent("stop")["name"] == "stop"
    assert mapper.map_intent("nonsense phrase") is None
