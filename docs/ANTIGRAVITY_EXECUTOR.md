# Antigravity CLI executor (Stewart-SWE-AF)

`swe_af.runtime.antigravity_adapter.AntigravityAdapter` runs the local `agy`
executable as an isolated subprocess. It detects the executable with PATH lookup,
uses the CLI's pre-existing official authentication, feeds the prompt on stdin,
and requests `--output-format stream-json`. Its strict JSONL parser preserves
progress/tool/result events; callers can observe each event through `on_event`.
The asynchronous `harness()` method offloads subprocess work from the event loop.

Selection is opt-in: call `build_executor_dispatcher()` from
`swe_af.runtime.executor_backends` and set `SWE_HARNESS_BACKEND=antigravity`
(or `jules`). The factory preserves the canonical AgentField handler and does
not install a global registry. External
`tools` lists are rejected: the CLI owns its own tools, and this implementation
does not claim Stewart's `SafeToolExecutor` isolation for them. Workspace `cwd`
is explicit/resolved, execution has a timeout and per-adapter concurrency limit,
and no dangerous permission-bypass flags are used. Process cancellation and
output parse errors fail closed. CLI stderr is intentionally not surfaced.

The optional `conversation_id` currently maps to `--resume`; use only with CLI
versions whose official help documents that flag. No REST/private API,
credential extraction, automatic commit, or merge is performed. This adapter
reports CLI events and final result but does not assert workspace changes were
committed or create GitHub PRs. Validate `agy --help` against the installed
official CLI version before production use; no live CLI smoke test was run.

Jules remains a separate REST executor (`swe_af.runtime.jules_adapter`) because
its asynchronous remote session lifecycle and remote workspace differ from local
CLI execution. `build_executor_dispatcher()` exposes it explicitly alongside
Antigravity and AgentField. Jules now accepts `repository="owner/repo"` and an
optional `branch`, and `session_id` resumes observation without creating a new
session. The existing Jules consolidation branch was not merged or modified;
this worktree consolidates only through the dispatcher factory.

## Deterministic tests

`AGENTFIELD_SERVER=http://localhost:9999 python -m pytest -q tests/test_antigravity_adapter.py`

The tests mock subprocess execution; they do not validate live CLI syntax,
authentication, quotas, or permissions.
