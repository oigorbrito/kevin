import asyncio
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


def test_async_harness_streams_progress_events(monkeypatch, tmp_path):
    output = b'{"type":"progress"}\n{"type":"result","result":"done"}\n'

    class Input:
        def write(self, data):
            assert data == b"task"

        async def drain(self):
            return None

        def close(self):
            return None

    class Process:
        def __init__(self):
            self.stdin = Input()
            self.stdout = asyncio.StreamReader()
            self.stderr = asyncio.StreamReader()
            self.stdout.feed_data(output)
            self.stdout.feed_eof()
            self.stderr.feed_eof()
            self.returncode = None
            self.pid = 123

        async def wait(self):
            self.returncode = 0
            return 0

        def terminate(self):
            self.returncode = -1

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr("swe_af.runtime.antigravity_adapter.shutil.which", lambda _: "agy")

    async def fake_create(*args, **kwargs):
        assert args == ("agy", "--output-format", "stream-json")
        assert kwargs["cwd"] == tmp_path
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
    received = []
    result = asyncio.run(
        AntigravityAdapter().harness("task", cwd=tmp_path, on_event=received.append)
    )
    assert [event["type"] for event in received] == ["progress", "result"]
    assert result.result == "done"


def test_async_cancellation_terminates_child(monkeypatch, tmp_path):
    progress_seen = asyncio.Event()
    terminated = []

    class Input:
        def write(self, data):
            return None

        async def drain(self):
            return None

        def close(self):
            return None

    class Process:
        def __init__(self):
            self.stdin = Input()
            self.stdout = asyncio.StreamReader()
            self.stderr = asyncio.StreamReader()
            self.stdout.feed_data(b'{"type":"progress"}\n')
            self.stderr.feed_eof()
            self.returncode = None
            self.pid = 456

        async def wait(self):
            while self.returncode is None:
                await asyncio.sleep(0.001)
            return self.returncode

        def terminate(self):
            terminated.append(True)
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr("swe_af.runtime.antigravity_adapter.shutil.which", lambda _: "agy")

    async def fake_create(*args, **kwargs):
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)

    async def scenario():
        adapter = AntigravityAdapter()
        async def on_event(_event):
            progress_seen.set()
        task = asyncio.create_task(
            adapter.harness("task", cwd=tmp_path, on_event=on_event)
        )
        await progress_seen.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert terminated


def test_missing_cli_fails_closed(monkeypatch):
    monkeypatch.setattr("swe_af.runtime.antigravity_adapter.shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="not found"):
        AntigravityAdapter().run("task")
