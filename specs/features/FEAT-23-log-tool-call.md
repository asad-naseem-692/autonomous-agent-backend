# Feature: Log Every Tool Call
**Owner:** Backend | **Module:** Execution Trace & History

## Goal
Keep a permanent, tamper-evident record of every tool the agent ran (or
attempted to run).

## Scope
- `execution_logs` table: id, conversation_id, tool_name, tool_input
  (json), tool_output (json), status ("executed"|"pending_approval"|
  "rejected"|"failed"), created_at.
- A row is written every time the agent selects a tool — including read
  tools (executed immediately) and write tools (logged as
  "pending_approval" until resolved, then updated).
