# Feature: Conversation History (API)
**Owner:** Backend | **Module:** Execution Trace & History

## Goal
Let an operator revisit their past conversations with the agent.

## Scope
- `conversations` and `messages` tables, both scoped to
  `user_id = current_user.id`.
- Endpoint: `GET /conversations` — list of past conversations.
- Endpoint: `GET /conversations/{id}` — full message history for one.
