# Feature: Get Order Tool
**Owner:** Backend | **Module:** Business Tools (Read)

## Goal
Let the agent fetch a single order's details.

## Scope
- `app/tools/get_order.py`: typed tool function.
- Input: order id.
- Output: order id, customer id, status, amount, created_at.
- Read-only, no approval required.
