# Feature: Agent Reasoning Loop
**Owner:** Backend | **Module:** Agent Conversation

## Goal
Run the actual OpenAI Agents SDK loop that decides what to do, calls
tools, and produces a final answer.

## Scope
- `app/agent/runner.py`: uses the real `openai-agents` SDK, configured
  with a custom `OpenAIChatCompletionsModel` pointing at Gemini's
  OpenAI-compatible `base_url`, using `GEMINI_API_KEY`.
- The agent is given the full tool registry (Module 3 + Module 4 tools)
  with their descriptions/schemas.
- When the agent selects a "write" tool (FEAT-15 through FEAT-18), the
  loop pauses and creates a pending approval request (FEAT-19) instead
  of executing it — execution only happens after approval (FEAT-20).
- When the agent selects a "read" tool (FEAT-11 through FEAT-14), it
  executes immediately and the result is fed back into the loop.
- Every tool call and its result is logged (FEAT-23) regardless of
  outcome.
