# Feature: Role Assignment & Storage
**Owner:** Backend | **Module:** Authentication

## Goal
Store and enforce each user's role (operator / admin).

## Scope
- `role` column on `users` table, default "operator" at signup.
- Role only ever comes from the verified JWT server-side.
- Admin accounts created via a seed script, not public signup.
