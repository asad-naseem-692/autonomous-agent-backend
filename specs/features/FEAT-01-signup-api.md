# Feature: Sign Up (API)
**Owner:** Backend | **Module:** Authentication

## Goal
Create a new operator account securely.

## Scope
- Endpoint: `POST /auth/signup`
- Input: name, email, password.
- Check email isn't already registered.
- Hash password with bcrypt before saving — never store plain text.
- Save to `users` table: id, name, email, hashed_password, role (default "operator"), created_at.
- Return created user (never the password hash).
