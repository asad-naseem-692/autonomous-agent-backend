# Feature: Find Customer Tool
**Owner:** Backend | **Module:** Business Tools (Read)

## Goal
Let the agent look up a customer by name or email — read-only, no
approval needed.

## Scope
- `app/tools/find_customer.py`: a typed function (Pydantic input/output)
  registered as an Agents SDK tool.
- Input: name or email (partial match allowed).
- Output: customer id, name, email — no sensitive data beyond this.
- Pure database read — no AI involved in the query itself, only in the
  agent's decision to call it.
