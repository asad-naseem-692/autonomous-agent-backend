# Feature: Send Message (API)
**Owner:** Backend | **Module:** Agent Conversation

## Goal
Accept a user's natural-language command and hand it to the agent.

## Scope
- Endpoint: `POST /conversations/{id}/messages` (or `POST /conversations`
  to start a new one).
- Input: message text.
- Saves the user message, then invokes the agent reasoning loop
  (FEAT-08), returning the agent's response (which may include a pending
  approval request instead of a final answer — see Module 5).
