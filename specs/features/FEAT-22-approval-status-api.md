# Feature: Approval Status (API)
**Owner:** Backend | **Module:** Human Approval Workflow

## Goal
Let the frontend know when an approval is pending or resolved.

## Scope
- Endpoint: `GET /approvals/{id}` — returns current status and details.
- Used by the frontend to render the approval card and update it once
  resolved.
