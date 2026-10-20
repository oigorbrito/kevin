"""Jules remote agent adapter for Stewart-SWE-AF.
Uses JULES_API_KEY from env only; never logs it.
No calls during import/init.
"""
import os, json, re, urllib.request, urllib.error, hashlib
from typing import Any, Dict, Optional


_SECRET_PATTERNS = [
    re.compile(r"Bearer\s+['\"]?[A-Za-z0-9_\-\.+/=~]+['\"]?", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|token|secret|password|auth|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.+/=~]+['\"]?", re.IGNORECASE),
    re.compile(r"AIza[A-Za-z0-9_\-]{30,}"),
    re.compile(r"(?:sk-[A-Za-z0-9_\-]{20,}|gh[pousr]_[A-Za-z0-9_\-]{20,})"),
]
_URL_USERINFO_PATTERN = re.compile(r"(://)[^/\s@]+@")
_USERINFO_CRED_PATTERN = re.compile(r"(?<![a-zA-Z0-9_\-\.])([a-zA-Z0-9_\-\.]+:[^/\s@:]+)@")


def _scrub_text(text: Any, api_key: Optional[str] = None) -> str:
    if text is None:
        return ""
    scrubbed = str(text)
    # Short credentials cannot be safely distinguished from ordinary words.
    # Fail closed rather than reflecting any untrusted error text.
    if api_key and len(api_key.strip()) < 4:
        return "[REDACTED]"
    if api_key and api_key.strip():
        scrubbed = scrubbed.replace(api_key.strip(), "[REDACTED]")
    scrubbed = _URL_USERINFO_PATTERN.sub(r"\1[REDACTED]@", scrubbed)
    scrubbed = _USERINFO_CRED_PATTERN.sub(r"[REDACTED]@", scrubbed)
    for pattern in _SECRET_PATTERNS:
        scrubbed = pattern.sub("[REDACTED]", scrubbed)
    # Collapse newlines, carriage returns, and tabs to prevent log injection
    scrubbed = re.sub(r"[\r\n\t]+", " ", scrubbed).strip()
    if len(scrubbed) > 512:
        scrubbed = scrubbed[:509] + "..."
    return scrubbed


class JulesAdapter:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key or os.environ.get("JULES_API_KEY")
        self.timeout = timeout
        self.base = "https://jules.googleapis.com/v1alpha"

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("JULES_API_KEY missing")
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _sanitize_error(
        self,
        exc: Exception,
        method: str = "REQUEST",
        path: str = "",
    ) -> RuntimeError:
        """Sanitize network and HTTP errors, logging method, relative path, and API message without secrets."""
        rel_path = path
        if self.base in rel_path:
            rel_path = rel_path.split(self.base, 1)[-1]
        rel_path = rel_path.split("?")[0]  # strip any query string
        rel_path = _scrub_text(rel_path, self.api_key)

        if isinstance(exc, urllib.error.HTTPError):
            reason_val = getattr(exc, "reason", None) or getattr(exc, "msg", "")
            reason_str = _scrub_text(reason_val, self.api_key)
            detail_msg = None
            try:
                raw_body = exc.read(8192).decode("utf-8", errors="ignore")
                if raw_body:
                    body_json = json.loads(raw_body)
                    if isinstance(body_json, dict) and "error" in body_json:
                        err_obj = body_json["error"]
                        if isinstance(err_obj, dict):
                            detail_msg = err_obj.get("message")
                        elif isinstance(err_obj, str):
                            detail_msg = err_obj
            except Exception:
                detail_msg = None

            if detail_msg:
                clean_detail = _scrub_text(detail_msg, self.api_key)
                if clean_detail:
                    return RuntimeError(
                        f"Jules API {method} {rel_path} HTTP error {exc.code} ({reason_str}): {clean_detail}"
                    )
            return RuntimeError(
                f"Jules API {method} {rel_path} HTTP error {exc.code}: {reason_str}"
            )
        if isinstance(exc, urllib.error.URLError):
            reason_str = _scrub_text(getattr(exc, "reason", str(exc)), self.api_key)
            return RuntimeError(f"Jules API {method} {rel_path} connection error: {reason_str}")
        return RuntimeError(f"Jules API {method} {rel_path} error: {type(exc).__name__}")

    def create_session(
        self,
        prompt: str,
        require_plan_approval: bool = True,
        **extra_options: Any,
    ) -> Dict[str, Any]:
        """Creates a Jules session with isolated single invocation and optional requirePlanApproval."""
        if not self.api_key:
            raise RuntimeError("JULES_API_KEY missing")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "requirePlanApproval": require_plan_approval,
        }
        for k, v in extra_options.items():
            if v is not None:
                payload[k] = v

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}/sessions",
            data=data,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise self._sanitize_error(exc, method="POST", path="/sessions") from None
        except Exception as exc:
            raise self._sanitize_error(exc, method="POST", path="/sessions") from None

    def get_status(self, session_id: str) -> Dict[str, Any]:
        """Retrieves session status/state via official GET /sessions/{session_id}."""
        if not self.api_key:
            raise RuntimeError("JULES_API_KEY missing")
        name = session_id if session_id.startswith("sessions/") else f"sessions/{session_id}"
        req_path = f"/{name}"
        req = urllib.request.Request(
            f"{self.base}{req_path}",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise self._sanitize_error(exc, method="GET", path=req_path) from None
        except Exception as exc:
            raise self._sanitize_error(exc, method="GET", path=req_path) from None

    def list_repositories(self, page_size: int = 100) -> Dict[str, Any]:
        """List repositories authorized as Jules sources using official GET /sources."""
        if not self.api_key:
            raise RuntimeError("JULES_API_KEY missing")
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000")
        sources: list[Dict[str, Any]] = []
        page_token: Optional[str] = None
        while True:
            query = f"?pageSize={page_size}"
            if page_token:
                from urllib.parse import quote
                query += "&pageToken=" + quote(page_token, safe="")
            path = "/sources" + query
            req = urllib.request.Request(
                f"{self.base}{path}", headers=self._headers(), method="GET"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    page = json.loads(resp.read().decode("utf-8"))
            except (urllib.error.HTTPError, urllib.error.URLError) as exc:
                raise self._sanitize_error(exc, method="GET", path=path) from None
            except Exception as exc:
                raise self._sanitize_error(exc, method="GET", path=path) from None
            if not isinstance(page, dict) or not isinstance(page.get("sources", []), list):
                raise RuntimeError("Jules API returned an invalid sources response")
            sources.extend(source for source in page.get("sources", []) if isinstance(source, dict))
            page_token = page.get("nextPageToken")
            if not page_token:
                return {"sources": sources}

    def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send an explicit continuation message to a Jules session."""
        if not message.strip():
            raise ValueError("message must not be empty")
        return self._session_action(session_id, "sendMessage", {"prompt": message})

    def approve_plan(self, session_id: str) -> Dict[str, Any]:
        """Approve the pending Jules plan only on explicit caller request."""
        return self._session_action(session_id, "approvePlan", {})

    def _session_action(self, session_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("JULES_API_KEY missing")
        name = session_id if session_id.startswith("sessions/") else f"sessions/{session_id}"
        path = f"/{name}:{action}"
        req = urllib.request.Request(
            f"{self.base}{path}", data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(), method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise self._sanitize_error(exc, method="POST", path=path) from None
        except Exception as exc:
            raise self._sanitize_error(exc, method="POST", path=path) from None

    def get_result(self, session_id: str) -> Dict[str, Any]:
        """Retrieves session activities/results via official GET /sessions/{session_id}/activities."""
        if not self.api_key:
            raise RuntimeError("JULES_API_KEY missing")
        name = session_id if session_id.startswith("sessions/") else f"sessions/{session_id}"
        req_path = f"/{name}/activities"
        req = urllib.request.Request(
            f"{self.base}{req_path}",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise self._sanitize_error(exc, method="GET", path=req_path) from None
        except Exception as exc:
            raise self._sanitize_error(exc, method="GET", path=req_path) from None


# Harness integration: register Jules backend locally
from .application_harness import register_backend, HarnessAgent, HarnessRequest
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import threading
from types import SimpleNamespace


_AUDIT_LOCK = threading.Lock()
AUDIT_LOG_PATH = Path("logs") / "jules_operational_audit.jsonl"


def _persist_session_audit(
    session_id: Optional[str],
    outcome: str = "created",
    log_path: Optional[Path] = None,
    operation_id: Optional[str] = None,
    request_fingerprint: Optional[str] = None,
) -> None:
    """Safely persist minimal operational metadata for a created session.

    Logs ONLY UTC timestamp, session identifier, outcome, and schema version.
    Never logs prompts, API keys, headers, or full response bodies.
    """
    path = log_path or AUDIT_LOG_PATH
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "event": "session_creation_started" if outcome == "creating" else "session_created",
        "outcome": outcome,
        "version": "1.0",
    }
    if operation_id is not None:
        record["operation_id"] = operation_id
        record["request_fingerprint"] = request_fingerprint
    line = json.dumps(record, separators=(",", ":")) + "\n"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _AUDIT_LOCK:
            # Create file with restricted user-only permissions if supported
            if not path.exists():
                path.touch(mode=0o600, exist_ok=True)
            try:
                os.chmod(path, 0o600)
            except (OSError, NotImplementedError):
                pass
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
    except Exception as exc:
        raise RuntimeError(
            "Jules operation could not be durably journaled; inspect remote state before retrying"
        ) from exc


TERMINAL_SUCCESS_STATES = {"COMPLETED", "SUCCEEDED"}
TERMINAL_FAILURE_STATES = {"FAILED", "CANCELLED", "CANCELED"}
TERMINAL_STATES = TERMINAL_SUCCESS_STATES | TERMINAL_FAILURE_STATES


def _claim_operation(operation_id: str, log_path: Optional[Path] = None) -> None:
    """Atomically claim a fresh stable operation key before remote creation."""
    journal = log_path or AUDIT_LOG_PATH
    claims = journal.parent / (journal.name + ".claims")
    claims.mkdir(parents=True, exist_ok=True)
    claim = claims / (hashlib.sha256(operation_id.encode("utf-8")).hexdigest() + ".claim")
    try:
        descriptor = os.open(str(claim), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write("claimed\\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise RuntimeError(
            "Jules operation key is already claimed without a recoverable session; inspect remote state"
        ) from exc
    except OSError as exc:
        raise RuntimeError("could not safely claim Jules operation key") from exc


def _find_operation_session(
    operation_id: str, request_fingerprint: str, log_path: Optional[Path] = None
) -> Optional[str]:
    """Recover a previously journaled session, rejecting operation-id reuse."""
    path = log_path or AUDIT_LOG_PATH
    if not path.is_file():
        return None
    found: Optional[str] = None
    matched = False
    try:
        with path.open(encoding="utf-8") as records:
            for line in records:
                record = json.loads(line)
                if record.get("operation_id") != operation_id:
                    continue
                matched = True
                if record.get("request_fingerprint") != request_fingerprint:
                    raise ValueError("operation_id was previously used for a different Jules prompt")
                found = record.get("session_id")
        if found is None:
            # A previous process may have reached Jules before it could journal
            # the returned ID. Refuse to blindly submit the same operation again.
            if matched:
                raise RuntimeError(
                    "Jules operation has an unresolved create attempt; inspect the remote session before retrying"
                )
    except ValueError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Jules session journal is unreadable; refusing duplicate submission") from exc
    return found


class JulesHarnessAgent:
    def __init__(self, audit_path: Optional[Path] = None):
        self.audit_path = audit_path

    async def harness(self, prompt: str, **options: Any) -> Any:
        import time

        adapter = JulesAdapter()
        require_plan_approval = options.get("require_plan_approval", True)
        # Explicit IDs or a previously journaled operation resume observation;
        # they must never create a second remote session after caller restart.
        operation_id = options.get("operation_id")
        fingerprint = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        recovered_id = None
        if operation_id and not options.get("session_id"):
            recovered_id = _find_operation_session(
                str(operation_id), fingerprint, self.audit_path
            )
        session_id = options.get("session_id") or recovered_id
        if session_id:
            session = {"id": str(session_id), "name": str(session_id)}
        else:
            create_options: Dict[str, Any] = {}
            repository = options.get("repository")
            branch = options.get("branch")
            if repository:
                owner, separator, repo = str(repository).partition("/")
                if not separator or not owner or not repo or "/" in repo:
                    raise ValueError("repository must use owner/repo format")
                github_repo: Dict[str, Any] = {"owner": owner, "repo": repo}
                create_options["sourceContext"] = {
                    "source": {"githubRepo": github_repo}
                }
            if branch:
                if not repository:
                    raise ValueError("repository is required when branch is specified")
                create_options["sourceContext"]["startingBranch"] = str(branch)
            if operation_id:
                # Atomic local claim + durable intent before POST: concurrent or
                # interrupted retries fail closed instead of duplicating remotely.
                _claim_operation(str(operation_id), self.audit_path)
                _persist_session_audit(
                    None, outcome="creating", log_path=self.audit_path,
                    operation_id=str(operation_id), request_fingerprint=fingerprint,
                )
            session = await asyncio.to_thread(
                adapter.create_session, prompt,
                require_plan_approval=require_plan_approval,
                **create_options,
            )
            session_id = session.get("id") or session.get("name")

        # Step 1: Guarantee persistence of session identifier immediately after creation
        audit_error = None
        if session_id:
            try:
                _persist_session_audit(
                    str(session_id),
                    outcome=("resumed" if options.get("session_id") else
                             "recovered" if recovered_id else "created"),
                    log_path=self.audit_path,
                    operation_id=str(operation_id) if operation_id else None,
                    request_fingerprint=fingerprint if operation_id else None,
                )
            except Exception as exc:
                audit_error = str(exc)

        # Continuation and approval are explicit operations; neither is inferred
        # from a retry or from the current remote status.
        if session_id and not audit_error and options.get("continue_message"):
            await asyncio.to_thread(
                adapter.send_message, str(session_id), str(options["continue_message"])
            )
        if session_id and not audit_error and options.get("approve_plan") is True:
            await asyncio.to_thread(adapter.approve_plan, str(session_id))

        # Step 2: Query follow-up status and activities only if audit succeeded and not skipped
        skip_queries = options.get("skip_status_and_result", False) or bool(audit_error)
        wait_for_completion = options.get("wait_for_completion", True)
        poll_interval = float(options.get("poll_interval", os.environ.get("JULES_POLL_INTERVAL", "1.0")))
        poll_timeout = float(
            options.get("timeout_seconds")
            or options.get("poll_timeout", os.environ.get("JULES_POLL_TIMEOUT", "300.0"))
        )

        status: Dict[str, Any] = {}
        result: Dict[str, Any] = {}
        timed_out = False
        start_time = time.monotonic()
        deadline = start_time + poll_timeout

        if not skip_queries and session_id:
            while True:
                try:
                    # Non-blocking async status query
                    status = await asyncio.to_thread(adapter.get_status, session_id)
                except Exception as exc:
                    status = {"unconfirmed": True, "error": str(exc), "state": "UNCONFIRMED"}

                state_str = str(
                    status.get("state")
                    or session.get("state")
                    or session.get("status")
                    or "UNKNOWN"
                ).upper()

                if state_str in TERMINAL_STATES:
                    break

                if not wait_for_completion:
                    break

                if status.get("unconfirmed"):
                    # Immediately interrupt remote flow when status query fails
                    break

                now = time.monotonic()
                if now >= deadline:
                    timed_out = True
                    break

                remaining = deadline - now
                sleep_dur = min(poll_interval, remaining)
                if sleep_dur > 0:
                    await asyncio.sleep(sleep_dur)
                else:
                    timed_out = True
                    break

            # Fetch activities / results once terminal or requested
            # Halts without calling the remote activities endpoint if status query failed
            if status.get("unconfirmed"):
                result = {"unconfirmed": True, "activities": []}
            elif state_str in TERMINAL_STATES or not wait_for_completion:
                try:
                    # Non-blocking async result query
                    result = await asyncio.to_thread(adapter.get_result, session_id)
                except Exception as exc:
                    result = {"unconfirmed": True, "error": str(exc), "activities": []}
            elif timed_out:
                result = {"timeout": True, "activities": []}
            else:
                result = {"activities": [], "in_progress": True}
        else:
            if audit_error:
                status = {"state": "AUDIT_FAILED", "queried": False, "audit_failure": True}
                result = {"queried": False, "activities": []}
            else:
                status = {"state": session.get("state") or session.get("status") or "QUEUED", "queried": False}
                result = {"queried": False}

        state_str = str(
            status.get("state")
            or session.get("state")
            or session.get("status")
            or "QUEUED"
        ).upper()

        # Step 3: Determine outcome, errors, and terminal completion
        error_message: Optional[str] = None
        failure_type = "none"

        if audit_error:
            error_message = audit_error
            failure_type = "audit_persistence_failure"
        elif timed_out:
            error_message = f"Jules session {session_id} timed out after {poll_timeout}s in state {state_str}"
            failure_type = "timeout"
        elif state_str in TERMINAL_FAILURE_STATES:
            error_message = f"Jules session {session_id} ended with state {state_str}"
            failure_type = "session_failed"
        elif status.get("unconfirmed") and status.get("error"):
            error_message = status.get("error")
            failure_type = "status_query_error"

        is_error = bool(error_message)
        complete = (state_str in TERMINAL_SUCCESS_STATES) and not is_error

        # Extract changed files from activities if present
        files_changed: list[str] = []
        activities = result.get("activities", []) if isinstance(result, dict) else []
        if isinstance(activities, list):
            for act in activities:
                if isinstance(act, dict):
                    if "files_changed" in act and isinstance(act["files_changed"], list):
                        files_changed.extend(str(f) for f in act["files_changed"])
                    elif "file" in act and isinstance(act["file"], str):
                        files_changed.append(act["file"])
                    elif "artifacts" in act and isinstance(act["artifacts"], list):
                        for art in act["artifacts"]:
                            if isinstance(art, dict) and "path" in art:
                                files_changed.append(str(art["path"]))
        seen = set()
        files_changed = [f for f in files_changed if not (f in seen or seen.add(f))]
        # Preserve only artifacts actually returned by Jules; do not synthesize
        # patches, commits, or PRs from a successful status alone.
        artifact_data: list[Dict[str, Any]] = []
        pull_request_urls: list[str] = []
        commit_urls: list[str] = []
        patches: list[str] = []
        def collect_artifacts(value: Any) -> None:
            if isinstance(value, dict):
                url = value.get("url") or value.get("uri")
                if isinstance(url, str) and url.startswith("https://"):
                    if "github.com" in url and "/pull/" in url:
                        pull_request_urls.append(url)
                    elif "github.com" in url and "/commit/" in url:
                        commit_urls.append(url)
                    artifact_data.append(value)
                patch = value.get("patch") or value.get("diff")
                if isinstance(patch, str) and patch:
                    patches.append(patch)
                for child in value.values():
                    collect_artifacts(child)
            elif isinstance(value, list):
                for child in value:
                    collect_artifacts(child)
        collect_artifacts(result)

        summary_parts = [f"Jules session {session_id} ({state_str})"]
        if error_message:
            summary_parts.append(f"error: {error_message}")
        summary = " - ".join(summary_parts)

        parsed_data = {
            "session_id": session_id,
            "status": status,
            "result": result,
            "session": session,
            "summary": summary,
            "complete": complete,
            "files_changed": files_changed,
            "artifacts": artifact_data,
            "pull_request_urls": sorted(set(pull_request_urls)),
            "commit_urls": sorted(set(commit_urls)),
            "patches": patches,
        }
        if audit_error:
            parsed_data["audit_warning"] = audit_error

        raw_result_str = json.dumps(parsed_data)

        # Build schema object if a Pydantic schema was passed in options
        schema = options.get("schema")
        parsed_obj = None
        if schema is not None:
            try:
                parsed_obj = schema.model_validate(parsed_data)
            except Exception:
                parsed_obj = None

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        return SimpleNamespace(
            result=raw_result_str,
            parsed=parsed_obj or parsed_data,
            is_error=is_error,
            error_message=error_message,
            failure_type=failure_type,
            session_id=session_id,
            summary=summary,
            complete=complete,
            files_changed=files_changed,
            artifacts=artifact_data,
            pull_request_urls=sorted(set(pull_request_urls)),
            commit_urls=sorted(set(commit_urls)),
            patches=patches,
            status=status,
            activities=result,
            cost_usd=0.0,
            num_turns=1,
            duration_ms=elapsed_ms,
            messages=[{"role": "user", "content": prompt}],
            input_tokens=len(prompt.split()),
            output_tokens=len(raw_result_str.split()),
            cache_read_tokens=0,
            cache_creation_tokens=0,
            total_tokens=len(prompt.split()) + len(raw_result_str.split()),
            model="jules",
        )


def _jules_backend_handler(agent: HarnessAgent, req: HarnessRequest) -> Any:
    return JulesHarnessAgent().harness(req.prompt, **req.options)


def register_jules() -> None:
    register_backend("jules", _jules_backend_handler)
