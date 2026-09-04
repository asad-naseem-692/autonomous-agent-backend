# Feature: Execution Trace (API)
**Owner:** Backend | **Module:** Execution Trace & History

## Goal
Let an operator see exactly what steps the agent took within one
conversation.

## Scope
- Endpoint: `GET /conversations/{id}/trace` — returns the ordered list
  of `execution_logs` entries for that conversation (tool name, input,
  output, status, timestamp).
