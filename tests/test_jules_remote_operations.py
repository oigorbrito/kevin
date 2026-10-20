import asyncio
import json
from unittest.mock import MagicMock, patch

from swe_af.runtime.jules_adapter import JulesAdapter, JulesHarnessAgent


def _response(data):
    response = MagicMock()
    response.read.return_value = json.dumps(data).encode()
    context = MagicMock()
    context.__enter__.return_value = response
    context.__exit__.return_value = None
    return context


def test_authorized_repository_discovery_paginates(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "test-key")
    adapter = JulesAdapter()
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            _response({"sources": [{"name": "repos/a"}], "nextPageToken": "next/1"}),
            _response({"sources": [{"name": "repos/b"}]}),
        ],
    ) as request:
        result = adapter.list_repositories(page_size=1)
    assert [source["name"] for source in result["sources"]] == ["repos/a", "repos/b"]
    assert "pageToken=next%2F1" in request.call_args_list[1].args[0].full_url
    assert request.call_args_list[0].args[0].get_method() == "GET"


def test_message_and_plan_approval_use_explicit_session_actions(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "test-key")
    with patch("urllib.request.urlopen", side_effect=[_response({}), _response({})]) as request:
        adapter = JulesAdapter()
        adapter.send_message("session-1", "Please continue")
        adapter.approve_plan("session-1")
    first, second = [call.args[0] for call in request.call_args_list]
    assert first.full_url.endswith("/sessions/session-1:sendMessage")
    assert json.loads(first.data) == {"prompt": "Please continue"}
    assert second.full_url.endswith("/sessions/session-1:approvePlan")


def test_harness_sends_only_explicit_continuation_and_approval(monkeypatch, tmp_path):
    monkeypatch.setenv("JULES_API_KEY", "test-key")
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            _response({}),
            _response({}),
            _response({"state": "COMPLETED"}),
            _response({"activities": [{"artifact": {"url": "https://github.com/org/repo/pull/12", "patch": "diff --git"}}]}),
        ],
    ) as request:
        result = asyncio.run(
            JulesHarnessAgent(audit_path=tmp_path / "audit.jsonl").harness(
                "resume", session_id="session-1", continue_message="next step",
                approve_plan=True,
            )
        )
    assert [call.args[0].get_method() for call in request.call_args_list] == ["POST", "POST", "GET", "GET"]
    assert result.pull_request_urls == ["https://github.com/org/repo/pull/12"]
    assert result.patches == ["diff --git"]
    assert result.parsed["complete"] is True
