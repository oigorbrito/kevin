import asyncio
import json
from unittest.mock import MagicMock, patch

from swe_af.runtime.jules_adapter import JulesHarnessAgent


def _response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    context = MagicMock()
    context.__enter__.return_value = response
    context.__exit__.return_value = None
    return context


def test_create_session_uses_requested_repository_branch_and_approval(monkeypatch, tmp_path):
    monkeypatch.setenv("JULES_API_KEY", "mock-key")
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            _response({"id": "session-1", "state": "QUEUED"}),
            _response({"id": "session-1", "state": "COMPLETED"}),
            _response({"activities": []}),
        ],
    ) as request:
        result = asyncio.run(
            JulesHarnessAgent(audit_path=tmp_path / "audit.jsonl").harness(
                "do task", repository="acme/project", branch="feature/task",
                require_plan_approval=True,
            )
        )
    payload = json.loads(request.call_args_list[0].args[0].data)
    assert payload["sourceContext"] == {
        "source": {"githubRepo": {"owner": "acme", "repo": "project"}},
        "startingBranch": "feature/task",
    }
    assert payload["requirePlanApproval"] is True
    assert result.session_id == "session-1"


def test_resume_existing_session_does_not_create_duplicate(monkeypatch, tmp_path):
    monkeypatch.setenv("JULES_API_KEY", "mock-key")
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            _response({"id": "saved-session", "state": "COMPLETED"}),
            _response({"activities": []}),
        ],
    ) as request:
        result = asyncio.run(
            JulesHarnessAgent(audit_path=tmp_path / "audit.jsonl").harness(
                "continue", session_id="saved-session"
            )
        )
    assert request.call_count == 2
    assert request.call_args_list[0].args[0].get_method() == "GET"
    assert result.session_id == "saved-session"
    assert result.parsed["complete"] is True
