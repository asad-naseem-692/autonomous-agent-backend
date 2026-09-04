# Feature: Dynamic Tool Selection
**Owner:** Backend | **Module:** Agent Conversation

## Goal
Let the agent choose the right tool(s) for a given request from the
full registry, without hardcoded if/else logic on our side.

## Scope
- This is handled by the OpenAI Agents SDK itself (function-calling)
  once tools are registered with clear names, descriptions, and typed
  parameters (Pydantic schemas).
- Our job is only to define good tool descriptions/schemas — not to
  write our own selection logic.
