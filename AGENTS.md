# AGENTS.md — Backend (FastAPI) — Autonomous Business Operations Agent

## Scope
This file applies to the `backend/` folder only. Deploys to Railway with
a Postgres database. A sibling `frontend/AGENTS.md` covers the frontend —
do not build any UI here.

## Tech stack (do not substitute)
Python, FastAPI, Pydantic v2, SQLAlchemy + Alembic, PostgreSQL,
python-jose (JWT), passlib[bcrypt] (password hashing), the real
**`openai-agents`** SDK (OpenAI Agents SDK) configured with a custom
`OpenAIChatCompletionsModel` pointing at Gemini's OpenAI-compatible
endpoint.

## Python project manager: use `uv`, not pip/requirements.txt
Same as our other projects: `uv init`, `uv add <package>` for
dependencies, commit `pyproject.toml` + `uv.lock` (no
`requirements.txt`). Run via `uv run uvicorn app.main:app --reload`.
Dockerfile installs `uv` and runs `uv sync --frozen`.

## Build order — full-stack, one feature at a time
Vertical slices pairing backend + frontend specs, one feature at a time,
stop for approval after each. Follow `specs/features/` in `FEAT-XX`
numeric order.

## Core architectural invariant
This backend is the single source of truth. All authorization, tool
execution, and approval-gating happen here — never trust the frontend.
**The agent never touches the database directly — it only ever acts
through typed tool functions.** Every user can only ever access their
own conversations and execution logs — checked on every request via the
verified JWT.

## AI & Agent usage — read this carefully
Only the agent's reasoning (`app/agent/runner.py`) calls Gemini, via the
**actual OpenAI Agents SDK** (`openai-agents` package) — not a
hand-rolled loop. Configure it like this:
```python
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

gemini_client = AsyncOpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

agent = Agent(
    name="Operations Agent",
    model=OpenAIChatCompletionsModel(
        model=settings.GEMINI_CHAT_MODEL,
        openai_client=gemini_client,
    ),
    tools=[...],  # all 8 business tools
)
```
**Before building any tools, verify this Agents-SDK-with-Gemini
combination actually works with a simple live test call** (e.g. one
trivial tool) — do not assume compatibility works exactly like plain
OpenAI, since this is a less common combination. Report what you find.

Never let the AI model decide authorization, approval-gating, or
database writes directly — those are deterministic code:
- **Read tools** (find_customer, get_order, get_order_history,
  calculate_balance) execute immediately when the agent calls them.
- **Write tools** (apply_credit, process_refund, cancel_order,
  update_order_status) are NEVER executed directly by the tool function
  when called by the agent — the reasoning loop intercepts the call,
  creates an `approval_requests` row, and only executes the real
  database write after a human explicitly approves it via the API.

## Hard rules
- Every tool call (read or write, executed or pending) is logged to
  `execution_logs` — no silent/unlogged actions.
- Write tools are always approval-gated — no exceptions, no "auto-approve"
  mode, even for testing (use a real approve API call in tests).
- An admin can never approve/reject another user's pending approvals
  unless explicitly acting as an approver on their behalf — approvals
  are scoped to the conversation's owning operator.
- `DATABASE_URL`, `CORS_ORIGINS`, `JWT_SECRET_KEY`, and `GEMINI_API_KEY`
  always come from environment variables via a central
  `app/core/config.py` — never hardcoded.
- Never combine `allow_origins=["*"]` with `allow_credentials=True`.
- Passwords always hashed with bcrypt — never logged or returned in
  plain text.

## Database
Same single-database strategy as our other projects: one Postgres
database on Railway, reached via a public connection string for local
development and an internal reference once deployed. I will provide the
real connection string directly for the local `.env` — never hardcode it
in any committed file.

## Data dictionary — return exactly these field names, always
`snake_case` fields, ISO 8601 UTC timestamps, UUID string ids, errors as
`{ "detail": "message" }`, list endpoints return plain arrays.

- **User**: `id, name, email, role ("operator"|"admin"), is_active, created_at`
- **Auth response**: `{ "access_token": string, "token_type": "bearer", "user": User }`
- **Customer**: `id, name, email`
- **Order**: `id, customer_id, status, amount, created_at`
- **Conversation**: `id, user_id, title, created_at`
- **Message**: `id, conversation_id, role ("user"|"assistant"), content, created_at`
- **ExecutionLog**: `id, conversation_id, tool_name, tool_input, tool_output, status ("executed"|"pending_approval"|"rejected"|"failed"), created_at`
- **ApprovalRequest**: `id, conversation_id, tool_name, tool_input, status ("pending"|"approved"|"rejected"), created_at, resolved_at, resolved_by`

If a feature needs a field not listed here, use the same conventions and
flag it in your summary — add it to both `backend/AGENTS.md` and
`frontend/AGENTS.md`. Never invent or rename a field silently on one side.

## Keep specs and code in sync (mandatory, every time)
The spec file for a feature is the source of truth for what that feature
is supposed to do — not just a one-time planning document. Whenever you
add, change, or remove behavior in a feature after it's already been
built:
1. **Update that feature's `.md` file in `specs/features/` in the same
   change** — add/edit/remove the relevant bullet points (endpoint path,
   request/response shape, validation rule, permission rule) so the spec
   still accurately describes the current behavior.
2. If the change affects what the frontend receives (new/renamed field,
   changed endpoint, changed status codes), note that clearly in the
   spec so it's visible to whoever is working on the frontend repo.
3. If a change doesn't fit any existing feature file, create a new
   `FEAT-XX-name.md` for it, following the same format as the others,
   rather than leaving the change undocumented.
4. Never let a spec describe behavior that no longer exists in the code,
   and never let the code do something its spec doesn't mention. Treat a
   stale or missing spec update as an incomplete task, not an optional
   cleanup step.

## Never let a change to one feature break a feature it depends on
Many features here build on each other (e.g. almost every tool depends
on the agent reasoning loop and the approval workflow). Before changing
a feature others rely on, check `specs/features/` for anything
referencing it. If a change is genuinely needed — including anything
affecting the API contract the frontend depends on — update that
feature's spec explicitly and confirm nothing else breaks. Never modify
a dependency's code, spec, or a fixed business rule (like "writes always
require approval") silently as a side effect of unrelated work.

## What you set up yourself
`.env.example` / local `.env` (`DATABASE_URL`, `CORS_ORIGINS`,
`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`GEMINI_API_KEY`, `GEMINI_CHAT_MODEL`, `ENVIRONMENT`), `.gitignore`
(must ignore `.env`, `.venv/`, `__pycache__/`, but NOT `uv.lock`),
`pyproject.toml` + `uv.lock`, `Dockerfile` (installs `uv`, runs
`uv sync --frozen`, listens on Railway's `$PORT`), central
`app/core/config.py`, a `/health` endpoint, an admin seed script.

## Deployment target
Railway (backend + Postgres). `CORS_ORIGINS` needs the deployed
frontend's Vercel URL once known.
