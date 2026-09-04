# Feature: Delete/Suspend User (API)
**Owner:** Backend | **Module:** Admin Panel

## Goal
Let an admin remove or suspend a problematic operator account.

## Scope
- Endpoint: `PATCH /admin/users/{id}/suspend` (toggles `is_active`) and
  `DELETE /admin/users/{id}` (admin role only, 403 otherwise).
- Deleting a user cascades to their conversations, messages, and
  execution logs — no orphaned data.
- Prevent an admin from suspending/deleting their own account.
