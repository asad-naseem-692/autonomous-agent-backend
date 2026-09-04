# Feature: Calculate Balance Tool
**Owner:** Backend | **Module:** Business Tools (Read)

## Goal
Let the agent compute a customer's current balance (dues/credits).

## Scope
- `app/tools/calculate_balance.py`: typed tool function.
- Input: customer id.
- Output: current balance computed as `sum(credits) - sum(unpaid/due orders)` (deterministic code over `credits` and `orders` tables, not AI-estimated).
- Read-only, no approval required.
