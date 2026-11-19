#!/usr/bin/env python3
"""
test_process_api_capture.py
Tests for ProcessApi's background output capture (_capture_output).
Author: Pito Salas
Open Source Under MIT license
"""

import io
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

from dome_control.commands.config_manager import ConfigManager
from dome_control.ros2_api.process_api import ProcessApi, ProcessInfo

CONFIG_FILE = str(Path.home() / ".dome" / "config" / "control.yaml")


def make_process_info(lines: list[str], log_file: str | None) -> ProcessInfo:
    process = Mock()
    process.stdout = io.StringIO("".join(f"{line}\n" for line in lines))
    process.poll.return_value = None
    return ProcessInfo(
        process=process,
        command="echo hi",
        output=[],
        is_running=True,
        pid=1234,
        start_time=time.time(),
        log_file=log_file,
    )


class TestCaptureOutput(unittest.TestCase):
    def setUp(self):
        self.process_api = ProcessApi(ConfigManager.create(CONFIG_FILE))

    def test_lines_recorded_and_logged_with_header_and_footer(self):
        log_path = Path(self.enterContext(tempfile.TemporaryDirectory())) / "proc.log"
        info = make_process_info(["one", "two"], str(log_path))

        self.process_api._capture_output("p1", info)

        self.assertEqual(info.output, ["one", "two"])
        log_text = log_path.read_text()
        self.assertIn("=== Process Log ===", log_text)
        self.assertIn("one\ntwo\n", log_text)
        self.assertIn("Process output capture complete.", log_text)
        self.assertTrue(info.process.stdout.closed)

    def test_without_log_file_still_records_and_closes_stdout(self):
        info = make_process_info(["only"], None)

        self.process_api._capture_output("p2", info)

        self.assertEqual(info.output, ["only"])
        self.assertTrue(info.process.stdout.closed)

    def test_footer_written_even_when_stream_fails(self):
        log_path = Path(self.enterContext(tempfile.TemporaryDirectory())) / "proc.log"
        info = make_process_info([], str(log_path))
        # Reading a closed pipe raises ValueError mid-stream.
        info.process.stdout = Mock(
            readline=Mock(side_effect=ValueError("closed")), close=Mock()
        )

        self.process_api._capture_output("p3", info)

        self.assertIn("Process output capture complete.", log_path.read_text())
        info.process.stdout.close.assert_called_once()
