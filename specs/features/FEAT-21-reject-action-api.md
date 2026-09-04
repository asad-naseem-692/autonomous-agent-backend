# Feature: Reject Action (API)
**Owner:** Backend | **Module:** Human Approval Workflow

## Goal
Let the user decline a pending sensitive action.

## Scope
- Endpoint: `POST /approvals/{id}/reject`
- Marks the request "rejected" — the underlying tool is never executed.
- Feeds this rejection back into the agent loop so it can acknowledge it
  and adjust its final summary accordingly.
