"""Isolated adapter for the documented Antigravity CLI stream-json interface.

The CLI's existing authentication is used; this adapter never reads or forwards
credentials. It invokes only ``agy --output-format stream-json`` and sends the
task over stdin. No permission-bypass flags are enabled.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass
class AntigravityResult:
    result: str
    parsed: Any
    is_error: bool
    error_message: str | None
    failure_type: str
    cost_usd: float
    num_turns: int
    duration_ms: int
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    total_tokens: int = 0
    model: str = "antigravity"
    events: list[dict[str, Any]] = field(default_factory=list)


def parse_stream_json(data: str) -> list[dict[str, Any]]:
    """Parse JSONL events strictly; blank lines are ignored, malformed data fails."""
    events: list[dict[str, Any]] = []
    for number, line in enumerate(data.splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid Antigravity stream-json event on line {number}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"Antigravity stream-json event on line {number} must be an object")
        events.append(item)
    return events


class AntigravityAdapter:
    def __init__(self, executable: str = "agy", timeout: float = 900, max_concurrency: int = 1):
        if timeout <= 0 or max_concurrency < 1:
            raise ValueError("timeout and max_concurrency must be positive")
        self.executable = executable
        self.timeout = timeout
        self._semaphore = threading.BoundedSemaphore(max_concurrency)

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def run(
        self,
        prompt: str,
        *,
        cwd: str | os.PathLike[str] | None = None,
        timeout: float | None = None,
        on_event: Callable[[Mapping[str, Any]], None] | None = None,
        conversation_id: str | None = None,
    ) -> AntigravityResult:
        if not self.available():
            raise RuntimeError(f"Antigravity CLI executable not found: {self.executable}")
        workspace = Path(cwd or os.getcwd()).resolve()
        if not workspace.is_dir():
            raise ValueError("Antigravity workspace must be an existing directory")
        command = [self.executable, "--output-format", "stream-json"]
        # Conversation continuation is passed only when the caller explicitly
        # requests a previously documented CLI conversation identifier.
        if conversation_id:
            command.extend(["--resume", conversation_id])
        started = time.monotonic()
        if not self._semaphore.acquire(timeout=timeout or self.timeout):
            raise TimeoutError("timed out waiting for an Antigravity concurrency slot")
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=workspace,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                start_new_session=(os.name != "nt"),
            )
            try:
                stdout, stderr = process.communicate(prompt, timeout=timeout or self.timeout)
            except subprocess.TimeoutExpired as exc:
                self._terminate(process)
                raise TimeoutError("Antigravity CLI timed out") from exc
            if process.returncode:
                # Do not echo stderr: CLI diagnostics may contain sensitive context.
                raise RuntimeError(f"Antigravity CLI exited with status {process.returncode}")
            events = parse_stream_json(stdout)
            if not events:
                raise ValueError("Antigravity CLI returned no stream-json events")
            for event in events:
                if on_event:
                    on_event(event)
            result_event = next((e for e in reversed(events) if e.get("type") in {"result", "final_result"}), None)
            result_text = ""
            if result_event:
                result_text = str(result_event.get("result", result_event.get("text", "")))
            return AntigravityResult(
                result=result_text, parsed=result_event or {"events": events},
                is_error=bool(result_event and result_event.get("is_error")),
                error_message=None, failure_type="none", cost_usd=0.0,
                num_turns=1, duration_ms=int((time.monotonic() - started) * 1000),
                session_id=str(result_event.get("session_id", "")) if result_event else "",
                messages=[{"role": "user", "content": prompt}], events=events,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError("could not run Antigravity CLI") from exc
        finally:
            if process is not None and process.poll() is None:
                self._terminate(process)
            self._semaphore.release()

    @staticmethod
    def _terminate(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass

    async def harness(self, prompt: str, **options: Any) -> AntigravityResult:
        # Keep subprocess execution and its blocking pipe reads off the event loop.
        return await asyncio.to_thread(
            self.run, prompt, cwd=options.get("cwd") or options.get("project_dir"),
            timeout=options.get("timeout_seconds"),
            on_event=options.get("on_event"),
            conversation_id=options.get("conversation_id"),
        )


def antigravity_registration(adapter: AntigravityAdapter | None = None) -> Any:
    """Build an explicit dispatcher registration; never modifies global routing."""
    from swe_af.runtime.harness_dispatch import HarnessBackendRegistration

    selected = adapter or AntigravityAdapter()

    async def handler(_agent: Any, request: Any, _executor: Any) -> AntigravityResult:
        if request.options.get("tools"):
            raise ValueError("Antigravity CLI manages tools internally; external tool lists are unsupported")
        return await selected.harness(request.prompt, **dict(request.options))

    return HarnessBackendRegistration(handler=handler)
