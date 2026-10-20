import asyncio

import pytest

from swe_af.runtime.antigravity_adapter import AntigravityResult
from swe_af.runtime.executor_backends import build_executor_dispatcher
from swe_af.runtime.harness_dispatch import (
    HarnessExecutionRequest,
    HarnessToolExecutorUnavailable,
    dispatch_harness,
)


class StubAgent:
    async def harness(self, prompt, **options):
        return prompt, options


class StubAntigravity:
    async def harness(self, prompt, **options):
        return AntigravityResult(
            result=prompt, parsed={}, is_error=False, error_message=None,
            failure_type="none", cost_usd=0, num_turns=1, duration_ms=0,
            session_id="stub",
        )


def test_executor_backends_are_explicit_and_agentfield_remains_default(monkeypatch):
    monkeypatch.delenv("SWE_HARNESS_BACKEND", raising=False)
    dispatcher = build_executor_dispatcher(antigravity=StubAntigravity())
    agent = StubAgent()
    default = asyncio.run(dispatch_harness(agent, "original"))
    assert default == ("original", {})

    monkeypatch.setenv("SWE_HARNESS_BACKEND", "antigravity")
    outcome = asyncio.run(
        dispatch_harness(agent, "task", harness_dispatcher=dispatcher)
    )
    assert outcome.result == "task"


def test_remote_backends_reject_external_tools():
    dispatcher = build_executor_dispatcher(antigravity=StubAntigravity())

    async def invoke():
        return await dispatcher.dispatch(
            StubAgent(),
            HarnessExecutionRequest.create("task", {"tools": ["bash"]}),
            backend_name="antigravity",
        )

    with pytest.raises(HarnessToolExecutorUnavailable, match="no SafeToolExecutor"):
        asyncio.run(invoke())
