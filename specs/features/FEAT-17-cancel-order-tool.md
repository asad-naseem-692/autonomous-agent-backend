# Feature: Cancel Order Tool
**Owner:** Backend | **Module:** Business Tools (Write)

## Goal
Cancel an order — only after human approval.

## Scope
- `app/tools/cancel_order.py`: typed tool function.
- Input: order id, reason.
- Same approval-gated pattern as FEAT-15 — intercepts execution, writes to
  `approval_requests` and `execution_logs`, and returns structured JSON payload:
  `{"status": "pending_approval", "approval_id": "<uuid>", "action": "cancel_order", "parameters": {"order_id": string, "reason": string}, "message": "Action cancel_order has NOT been executed yet. It requires human approval. Approval request <uuid> created."}`.
- Never executes cancellation until explicitly approved via FEAT-20.
