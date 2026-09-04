# Feature: View All Operators (API)
**Owner:** Backend | **Module:** Admin Panel

## Goal
Let an admin see who is using the system.

## Scope
- Endpoint: `GET /admin/users` (admin role only, 403 otherwise).
- Returns id, name, email, role, created_at for every user.
- Does NOT return other users' conversation content — only who exists.
