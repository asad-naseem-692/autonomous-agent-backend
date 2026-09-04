# Feature: Approve Action (API)
**Owner:** Backend | **Module:** Human Approval Workflow

## Goal
Let the user confirm a pending sensitive action, triggering its execution.

## Scope
- Endpoint: `POST /approvals/{id}/approve`
- Only the operator who owns the conversation (or an admin) can approve.
- Marks the request "approved", then actually executes the underlying
  tool function, feeds the result back into the agent loop, and returns
  the agent's continued response.
