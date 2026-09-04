# Feature: Get Order History Tool
**Owner:** Backend | **Module:** Business Tools (Read)

## Goal
Let the agent see all orders for a given customer.

## Scope
- `app/tools/get_order_history.py`: typed tool function.
- Input: customer id.
- Output: list of orders (id, status, amount, created_at), newest first.
- Read-only, no approval required.
