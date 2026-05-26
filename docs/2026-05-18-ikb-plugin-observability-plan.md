# Implementation Plan: Observability Layer for IKB-v2 Plugin

## Context

You are implementing the observability layer for an internal knowledge base plugin distributed via Bitbucket. The plugin includes a local MCP server (`ikb-v2`) and a routing agent that intercepts MCP tool calls. There is no central backend — events are written to JSONL files locally and pushed to a separate Bitbucket events repo on a per-user branch.

Five phases below build a minimal viable observability layer. **Implement in order. Verify acceptance criteria before moving on.** Phases 4 and 5 depend on Phases 1-2; Phase 3 is independent and can be done in parallel after Phase 1.

## Assumptions — confirm with the human before starting

- Implementation language: Python
- Routing agent is Python code (a wrapper around MCP client calls), not a Claude markdown subagent
- A separate `observability-events` Bitbucket repo exists (or will be created) — one branch per user
- User identity derives from a stable property (work email or git config user.email); the chosen value is hashed before persistence
- Plugin install directory: `~/.claude/plugins/ikb/` (or substitute the actual path)
- A kill-switch env var `IKB_OBS_DISABLED=1` must short-circuit all observability behavior — the plugin works normally without it

If any of these are wrong, stop and ask before writing code.

## Phase 0 — Orientation

Before touching code:

1. Read the existing routing agent and `ikb-v2` MCP server to understand the call surface — where tool calls flow through, where routing decisions are made, what's already logged (if anything).
2. Confirm the events repo URL, branch naming convention, and your auth credentials work for clone + push.
3. Confirm Python version and dependency-management approach used by the plugin (uv / poetry / pip). Match it.

## Architecture

```
User → Claude Code → routing agent ──┬──> ikb-v2 MCP server
                                     ├──> [other MCP servers]
                                     │
                                     └──> ObservabilitySink
                                             │
                                             ▼
                                          PII Redactor (sync gate)
                                             │
                                             ▼
                                          Append JSONL →
                                          ~/.ikb-obs/events/<yyyy-mm-dd>/<session_id>.jsonl
                                             │
                                             ▼ (session end)
                                          Commit to cloned events repo
                                             │
                                             ▼ (idle / process exit)
                                          git push events/<user_hash>
```

Suggested module layout inside the plugin:

```
routing_agent/observability/
  sink.py        # Phase 1
  schema.py      # Phase 1
  git_io.py      # Phase 1
  redactor.py    # Phase 2
  tag.py         # Phase 3
  cost.py        # Phase 4
  schemas/v1.0.0.json
  rate_card.json
  tags.txt
tests/observability/
```

---

## Phase 1 — Event Schema + JSONL Append + Commit + Push

**Build**

1. **Schema** (`schema.py`)
   - `BaseEvent` dataclass with required fields:
     - `schema_version: str` (start at `"1.0.0"`, semver)
     - `plugin_version: str` (read from `pyproject.toml` once at import)
     - `event_type: str` — enum: `session_start`, `session_end`, `tool_call`, `route_decision`, `error`
     - `request_id: str` (uuid4)
     - `session_id: str` (uuid4, set once per session)
     - `user_id: str` (sha256 of work email + per-install salt; salt generated on first run and stored in `~/.ikb-obs/config/salt`)
     - `ts_utc_ms: int`
     - `workflow_tag: Optional[str]` (filled by Phase 3)
     - `workflow_tag_confidence: Optional[str]` — `explicit` | `inferred` | `default`
     - `client_app: str`
     - `is_synthetic: bool` (default false)
   - Subclasses stubbed: `SessionStartEvent`, `SessionEndEvent`, `ToolCallEvent` (Phase 4), `RouteDecisionEvent` (Phase 5), `ErrorEvent`.
   - Also write a JSON Schema file at `schemas/v1.0.0.json` for cross-language validation.

2. **Sink** (`sink.py`)
   - Singleton `ObservabilitySink` with `init(session_id, user_id, ...)`, `append(event)`, `close()`.
   - `append`:
     - Calls redactor (stub for Phase 1 — returns input unchanged; replaced in Phase 2)
     - Serializes to single-line JSON
     - Appends to `~/.ikb-obs/events/<yyyy-mm-dd>/<session_id>.jsonl`
     - `fsync` after each write
     - Each line must be a complete JSON object — write the full line atomically (write to buffer, then `os.write` the whole bytes)
   - `close`:
     - Emits `SessionEndEvent`
     - Calls `git_io.commit_session(session_id)`
   - Crash safety: a killed process must leave a parseable file (every completed line is valid JSON; incomplete lines tolerated by parsers that read line-by-line and skip junk).

3. **Git I/O** (`git_io.py`)
   - On first event ever: shallow clone the events repo to `~/.ikb-obs/repo/`. Checkout or create branch `events/<user_hash>`. If clone fails, store events locally and retry on next session — never block the user.
   - `commit_session(session_id)`:
     - Copy JSONL into the cloned repo at `observability/<user_hash>/<yyyy-mm>/<yyyy-mm-dd>/sessions/<session_id>.jsonl`
     - `git add` + `git commit` with message `events: session <session_id>`
   - `push_idle()`:
     - Background thread fires after 5 min of no new events OR at process exit
     - `git push origin events/<user_hash>` with exponential backoff (5 retries over 30 min max)
     - On persistent failure, keep local commits — they push on next attempt
   - Local retention: events unpushed for >30 days → log warning to `~/.ikb-obs/diagnostics.log`
   - Never force-push. Never rewrite history.

**Acceptance**

- A scripted 3-event session produces a JSONL file with exactly 3 valid JSON lines
- Killing the process mid-session leaves a parseable file
- After `close()`, a new commit exists on `events/<user_hash>`
- After idle or `push_idle()`, the commit appears on origin
- Repeat clone is idempotent
- `IKB_OBS_DISABLED=1` short-circuits all behavior — no files, no clones, no commits

---

## Phase 2 — PII Redactor (Synchronous Gate)

**Build**

1. **Redactor** (`redactor.py`)
   - Pure function `redact(event_dict: dict) -> dict`. No I/O. Deterministic.
   - Walks recursively, applies to all string values.
   - Two operations:
     - **Replace** with `[REDACTED:<tag>]` token (default for matched patterns)
     - **Drop** the field entirely (for sensitive field names regardless of value)
   - Built-in regex patterns: email, US phone, US SSN, credit card (Luhn-validated), IPv4/IPv6, common API key prefixes (`sk-`, `xoxb-`, `ghp_`, `AKIA`, `Bearer <token>`).
   - Drop-not-redact field list: `*.password`, `*.token`, `*.secret`, `*.api_key`, `args.raw_query` (if your tools use that name)
   - Config files:
     - `~/.ikb-obs/config/allowlist.txt` — org-specific terms that should never be redacted
     - `~/.ikb-obs/config/extra_patterns.json` — additional regex patterns

2. **Sink integration**
   - Replace the Phase 1 stub. Every event passes through the redactor before serialization.
   - **Fail-closed**: if the redactor raises, do NOT write the original event. Write a minimal `ErrorEvent` with `error_code: redactor_failure` (no payload — could contain the PII that crashed it).
   - The redacted form is what hits disk. The unredacted form must never touch disk or diagnostics logs.

3. **Adversarial test corpus** (`tests/observability/redactor_corpus/`)
   - ≥50 cases: emails inside queries, SSNs in retrieved doc text, API keys in error messages, Bearer tokens in headers, international phone formats, edge cases like SSN-looking strings in unrelated contexts (e.g., a part number).
   - Each case ships as a fixture file and a test that the redactor handles it correctly.

**Acceptance**

- All 50+ adversarial cases pass
- Redactor is pure — no I/O, no globals, deterministic across runs
- Redactor exceptions produce a minimal error event, not a crash, and the original event is dropped
- A property test that injects every PII pattern into every string field of every event type confirms no PII survives to disk

---

## Phase 3 — Workflow Tag

**Build**

1. **Tag resolver** (`tag.py`)
   - `resolve_tag(cwd, env) -> (tag, confidence)`
   - Resolution order:
     1. **Explicit** — value from routing agent's session-start prompt (set by step 3 below)
     2. **Inferred** — from `~/.ikb-obs/config/project_tags.json` mapping (git remote → tag, or path prefix → tag). Confidence `inferred`.
     3. **Default** — `"unspecified"`. Confidence `default`.
   - Allowed tag values loaded from `tags.txt` (one per line). Tags outside this list are rejected (intentional friction — prevents tag sprawl).

2. **Session-state file**
   - On session start, write `~/.ikb-obs/session/<session_id>.json` with `{tag, confidence}`.
   - Sink reads it on first event and caches for the session. Every event in the session carries identical values.
   - Remove the file on session end.

3. **Routing agent prompt**
   - At session start, the routing agent shows: `Working on <inferred_tag>? (Y / type alt / skip)`
   - `Y` or empty → record as `explicit` (the inference was confirmed)
   - Typed alternate → validate against `tags.txt`; if valid record as `explicit`; if invalid show the allowed list and re-prompt
   - `skip` or Ctrl-C → record as `inferred` (or `default`)
   - Skippable via `IKB_OBS_NO_PROMPT=1` — use inferred/default silently

**Acceptance**

- Three sessions in three different project dirs produce three different inferred tags
- Same project, separate sessions → same inferred tag (deterministic)
- `IKB_OBS_NO_PROMPT=1` skips the prompt without error
- Every event in a session carries the same tag + confidence
- An unknown tag at the prompt is rejected with the allowed list shown
- Adding a new tag requires editing `tags.txt` (verify by trying to use one that's not there)

---

## Phase 4 — Tool-Call + Cost Telemetry

**Build**

1. **`ToolCallEvent` fields** (extend `schema.py`)
   - `tool_name: str`
   - `tool_version_hash: str` — sha256 of the tool description JSON; computed once per tool registration and cached
   - `mcp_server: str`
   - `args_redacted: dict` (post-redactor)
   - `args_hash: str` — sha256 of the *redacted* args (so repeat queries can be clustered without raw text)
   - `status: str` — `success` | `error` | `timeout` | `policy_denied`
   - `error_code: Optional[str]`
   - `latency_ms: int`
   - `cost_usd_micros: int` (default 0; use int micros not floats for clean sums)
   - `token_count_in: Optional[int]`
   - `token_count_out: Optional[int]`

2. **Cost computation** (`cost.py`)
   - `compute_cost_micros(tool_or_model_name, token_in, token_out) -> int`
   - Rate card at `routing_agent/observability/rate_card.json`:
     ```
     { "<model_or_tool_name>": {
         "input_per_1m_tokens_usd": 3.0,
         "output_per_1m_tokens_usd": 15.0
       } }
     ```
   - Tool not in rate card → return 0 and emit an `ErrorEvent` with `error_code: cost_card_miss`. Do not break the tool call.

3. **Routing-agent wrapper**
   - Wrap every MCP tool invocation:
     - Generate `request_id`
     - Capture monotonic start time
     - Execute tool
     - Capture end time, status, token counts (parse from MCP response if exposed)
     - Compute cost
     - Build `ToolCallEvent`
     - `sink.append(event)`
   - Must not change tool semantics — only observe.
   - On tool exception: build event with `status=error`, `error_code=<exception class name>`, then **re-raise**. Callers must see the same exception they would have seen without observability.

**Acceptance**

- Every MCP tool call produces exactly one `ToolCallEvent`
- Cost matches expected math for rate-card-known tools (unit test with synthetic token counts)
- Rate-card miss → cost = 0 + warning event + tool still works
- Tool exception → event with `status=error` AND original exception re-raised
- Latency accurate to within ±5ms of wall-clock measurement
- A tool whose response contains PII in its args is fully redacted before persistence (integration test)

---

## Phase 5 — Route-Decision Events

**Build**

1. **`RouteDecisionEvent` fields** (extend `schema.py`)
   - `selected_tool: str`
   - `selected_mcp_server: str`
   - `candidates: list[{tool_name, mcp_server, score: float, reason: str}]`
   - `policy_version_hash: str` — sha256 of the routing-rules file content (or routing-function bytecode)
   - `route_reason_code: str` — `rule_match` | `fallback_default` | `user_override` | `single_candidate`
   - `selection_latency_ms: int` — routing logic time only, excluding tool execution
   - `was_user_override: bool`

2. **Emission**
   - At the point the routing agent selects a tool, emit a `RouteDecisionEvent` *before* invoking the tool.
   - If the user explicitly overrides the routing agent's selection mid-session, emit a second event with `was_user_override=true` and the user's selection.
   - `selection_latency_ms` measured around the routing logic alone, not the subsequent tool call.

**Acceptance**

- Every routing decision produces one `RouteDecisionEvent`
- A test that edits the routing rules file changes the `policy_version_hash` on the next event
- User override produces a second event with `was_user_override=true`
- Selection latency is recorded separately from any subsequent `ToolCallEvent.latency_ms`

---

## Cross-Cutting Requirements

**Schema evolution**

- Semver on `schema_version`. Adding optional fields = patch; adding required = minor; removing or retyping = major. Never delete a schema version definition — it must remain readable forever.

**Error handling philosophy**

- Observability errors must never break user work.
- **Fail-open** for: git push failure (queue locally), cost computation (default 0), tag resolution (default `unspecified`).
- **Fail-closed** for: PII redactor (write minimal error event, drop original), schema validation (drop malformed events, write to local error file).

**Diagnostic logging**

- The observability layer's own logs go to `~/.ikb-obs/diagnostics.log`, never the event stream.
- No PII in diagnostics either.
- Rotate at 10MB, keep 3 rotations.

**Concurrency**

- Single Claude session at a time per user — low concurrency.
- Sink writes only to the active session file; push thread reads only closed session files.
- Use a file lock on the active session file as a safety net.

**Kill switch**

- `IKB_OBS_DISABLED=1` env var short-circuits everything. The plugin must work normally with it set. Test this explicitly.

**Testing**

- Unit tests per module.
- Integration test: end-to-end session producing one of each event type, valid against the JSON Schema.
- Adversarial PII corpus (Phase 2).
- Git mock: simulate push failures, verify retry + local-queue behavior.
- No test writes to the real events repo — use a temp directory as the git remote.

---

## Out of Scope (Do Not Build)

- Aggregator / DuckDB / dashboards / analytics queries
- Retrieval-quality scoring (faithfulness, precision@k)
- Outcome joins to external systems (ServiceNow, CRM, HRIS)
- Real-time alerting
- Cross-user analytics
- Web UI / admin interface
- Schema migration tooling beyond version stamping

If you're tempted to build any of these, stop and ask.

---

## Final Acceptance (Whole Plan)

The plan is done when:

1. A user installs the plugin, runs a Claude session that hits ikb-v2 tools, ends the session, and within ~5 min a new commit appears on `events/<user_hash>` on the events repo.
2. The committed JSONL contains: 1 `session_start`, ≥1 `route_decision`, ≥1 `tool_call`, 1 `session_end`. Every event carries the same `workflow_tag` and `workflow_tag_confidence`.
3. A controlled PII test corpus produces zero PII in the committed events.
4. Network failures during push do not lose events — they appear on the next successful push.
5. With `IKB_OBS_DISABLED=1` the plugin behaves identically to a build without this layer.
