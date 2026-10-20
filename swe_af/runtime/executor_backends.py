"""Opt-in dispatcher composition for remote and local executor backends.

The default AgentField dispatcher remains untouched. Applications choosing an
alternative must explicitly construct this dispatcher and select its backend.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from swe_af.runtime.antigravity_adapter import AntigravityAdapter, antigravity_registration
from swe_af.runtime.harness_dispatch import (
    DEFAULT_HARNESS_BACKEND,
    HarnessBackendRegistration,
    HarnessDispatcher,
    agentfield_registration,
)
from swe_af.runtime.jules_adapter import JulesHarnessAgent


def build_executor_dispatcher(
    *,
    antigravity: AntigravityAdapter | None = None,
    jules_audit_path: Path | None = None,
) -> HarnessDispatcher:
    """Create an explicit AgentField/Jules/Antigravity dispatcher registry.

    This does not install the registry globally. Jules and Antigravity do not
    accept Stewart's external SafeToolExecutor requests; their native execution
    environments remain responsible for their own tools and safety controls.
    """
    async def jules_handler(_agent: Any, request: Any, _executor: Any) -> Any:
        if request.options.get("tools"):
            raise ValueError("Jules remote sessions do not accept external tool lists")
        remote = JulesHarnessAgent(audit_path=jules_audit_path)
        return await remote.harness(request.prompt, **dict(request.options))

    return HarnessDispatcher(
        {
            DEFAULT_HARNESS_BACKEND: agentfield_registration(),
            "jules": HarnessBackendRegistration(handler=jules_handler),
            "antigravity": antigravity_registration(antigravity),
        }
    )

