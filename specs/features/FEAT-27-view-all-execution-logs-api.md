# Feature: View All Execution Logs (API)
**Owner:** Backend | **Module:** Admin Panel

## Goal
Let an admin audit what actions have been taken across the whole system.

## Scope
- Endpoint: `GET /admin/execution-logs` (admin role only, 403 otherwise).
- Returns execution log entries across all users, with filters (by user,
  by tool name, by status, by date range).
