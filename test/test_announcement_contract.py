#!/usr/bin/env python3
import json

from control.announcement_contract import (
    Announcement,
    AnnouncementMsg,
    PRIORITY_DISCOVERY,
    PRIORITY_QUERY_REPLY,
    PRIORITY_SAFETY,
    make_announcement_msg,
)


def test_announcement_msg_constants_match_contract():
    assert AnnouncementMsg.PRIORITY_SAFETY == PRIORITY_SAFETY
    assert AnnouncementMsg.PRIORITY_QUERY_REPLY == PRIORITY_QUERY_REPLY
    assert AnnouncementMsg.PRIORITY_DISCOVERY == PRIORITY_DISCOVERY


def test_announcement_round_trips_through_typed_msg():
    original = Announcement(
        text="I see a can",
        priority=PRIORITY_DISCOVERY,
        source="behavior_manager",
        dedup_key="scene-can",
    )

    parsed = Announcement.from_msg(original.to_msg())

    assert parsed.text == original.text
    assert parsed.priority == original.priority
    assert parsed.source == original.source
    assert parsed.dedup_key == original.dedup_key


def test_make_announcement_msg_populates_required_fields():
    msg = make_announcement_msg(
        "battery low",
        priority=PRIORITY_SAFETY,
        source="battery_monitor",
        dedup_key="battery-low",
    )

    assert msg.text == "battery low"
    assert msg.priority == PRIORITY_SAFETY
    assert msg.source == "battery_monitor"
    assert msg.dedup_key == "battery-low"
    assert hasattr(msg, "stamp")


def test_legacy_payload_compatibility_remains_available():
    payload = json.dumps(
        {
            "text": "hello",
            "priority": str(PRIORITY_QUERY_REPLY),
            "source": "legacy",
            "dedup_key": "legacy-hello",
        }
    )

    parsed = Announcement.from_payload(payload)

    assert parsed.text == "hello"
    assert parsed.priority == PRIORITY_QUERY_REPLY
    assert parsed.source == "legacy"
    assert parsed.dedup_key == "legacy-hello"
