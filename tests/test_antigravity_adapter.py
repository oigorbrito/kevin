import subprocess

import pytest

from swe_af.runtime.antigravity_adapter import AntigravityAdapter, parse_stream_json


def test_parse_stream_json_progress_tools_result():
    events = parse_stream_json(
        '{"type":"progress","message":"working"}\n'
        '{"type":"tool_use","name":"read_file"}\n'
        '{"type":"result","result":"done","session_id":"s-1"}\n'
    )
    assert [event["type"] for event in events] == ["progress", "tool_use", "result"]


def test_parse_stream_json_rejects_malformed_and_non_object():
    with pytest.raises(ValueError, match="invalid Antigravity"):
        parse_stream_json("not-json")
    with pytest.raises(ValueError, match="must be an object"):
        parse_stream_json('["not", "an", "event"]')


def test_cli_result_and_progress_callback(monkeypatch, tmp_path):
    output = '{"type":"progress"}\n{"type":"result","result":"finished","session_id":"abc"}\n'

    class FakeProcess:
        returncode = 0

        def communicate(self, prompt, timeout):
            assert prompt == "task"
            return output, ""

        def poll(self):
            return 0

    def fake_popen(command, **kwargs):
        assert command == ["agy", "--output-format", "stream-json"]
        assert kwargs["shell"] is False
        assert "--dangerously-skip-permissions" not in command
        return FakeProcess()

    monkeypatch.setattr("swe_af.runtime.antigravity_adapter.shutil.which", lambda _: "agy")
    monkeypatch.setattr("swe_af.runtime.antigravity_adapter.subprocess.Popen", fake_popen)
    seen = []
    result = AntigravityAdapter().run("task", cwd=tmp_path, on_event=seen.append)
    assert result.result == "finished"
    assert result.session_id == "abc"
    assert [event["type"] for event in seen] == ["progress", "result"]


def test_missing_cli_fails_closed(monkeypatch):
    monkeypatch.setattr("swe_af.runtime.antigravity_adapter.shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="not found"):
        AntigravityAdapter().run("task")
