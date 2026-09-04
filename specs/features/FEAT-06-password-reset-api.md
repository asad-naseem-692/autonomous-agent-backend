# Feature: Password Reset (API)
**Owner:** Backend | **Module:** Authentication

## Goal
Let a user securely reset a forgotten password.

## Scope
- `POST /auth/request-reset` — generate a short-lived, single-use reset
  token (email it in production; for dev, return/log it).
- `POST /auth/confirm-reset` — verify token, hash new password with
  bcrypt, update user record, invalidate the token.
