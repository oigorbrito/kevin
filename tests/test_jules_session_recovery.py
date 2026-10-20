import asyncio
import json
import urllib.error
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


def test_operation_id_recovers_persisted_session_instead_of_recreating(monkeypatch, tmp_path):
    monkeypatch.setenv("JULES_API_KEY", "mock-key")
    journal = tmp_path / "audit.jsonl"
    agent = JulesHarnessAgent(audit_path=journal)
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            _response({"id": "once", "state": "COMPLETED"}),
            _response({"activities": []}),
            _response({"id": "once", "state": "COMPLETED"}),
            _response({"activities": []}),
        ],
    ) as request:
        first = asyncio.run(agent.harness("same task", operation_id="task-123"))
        second = asyncio.run(agent.harness("same task", operation_id="task-123"))
    methods = [call.args[0].get_method() for call in request.call_args_list]
    assert methods == ["POST", "GET", "GET", "GET", "GET"]
    assert first.session_id == second.session_id == "once"


def test_ambiguous_create_failure_blocks_duplicate_retry(monkeypatch, tmp_path):
    monkeypatch.setenv("JULES_API_KEY", "mock-key")
    agent = JulesHarnessAgent(audit_path=tmp_path / "audit.jsonl")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")) as request:
        try:
            asyncio.run(agent.harness("task", operation_id="ambiguous"))
        except RuntimeError:
            pass
        else:
            raise AssertionError("failed API call did not propagate")
        try:
            asyncio.run(agent.harness("task", operation_id="ambiguous"))
        except RuntimeError as error:
            assert "unresolved create attempt" in str(error)
        else:
            raise AssertionError("ambiguous operation was retried")
    assert request.call_count == 1


def test_operation_id_cannot_be_reused_for_different_prompt(monkeypatch, tmp_path):
    monkeypatch.setenv("JULES_API_KEY", "mock-key")
    agent = JulesHarnessAgent(audit_path=tmp_path / "audit.jsonl")
    with patch(
        "urllib.request.urlopen",
        side_effect=[_response({"id": "once", "state": "COMPLETED"}), _response({"activities": []})],
    ):
        asyncio.run(agent.harness("original", operation_id="stable-id"))
    try:
        asyncio.run(agent.harness("different", operation_id="stable-id"))
    except ValueError as error:
        assert "different Jules prompt" in str(error)
    else:
        raise AssertionError("operation ID mismatch was not rejected")
