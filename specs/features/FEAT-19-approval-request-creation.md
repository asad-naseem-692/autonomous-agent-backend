# Feature: Approval Request Creation
**Owner:** Backend | **Module:** Human Approval Workflow

## Goal
Pause a sensitive action and record that it needs human sign-off.

## Scope
- `approval_requests` table: id, conversation_id, tool_name, tool_input
  (json), status ("pending"|"approved"|"rejected"), created_at,
  resolved_at, resolved_by.
- Created automatically whenever a write tool (FEAT-15–18) is invoked by the
  agent: the tool wrapper creates the `approval_requests` record with `status="pending"`,
  logs to `execution_logs` with `status="pending_approval"`, and returns the
  structured JSON payload (`{"status": "pending_approval", "approval_id": "<uuid>", "action": "...", "parameters": {...}, "message": "..."}`)
  so the agent loop produces its final summary message with the approval request attached.
