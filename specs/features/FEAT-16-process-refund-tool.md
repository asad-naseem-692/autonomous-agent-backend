# Feature: Process Refund Tool
**Owner:** Backend | **Module:** Business Tools (Write)

## Goal
Refund an amount to a customer — only after human approval.

## Scope
- `app/tools/process_refund.py`: typed tool function.
- Input: order id, amount, reason.
- Same approval-gated pattern as FEAT-15 — intercepts execution, writes to
  `approval_requests` and `execution_logs`, and returns structured JSON payload:
  `{"status": "pending_approval", "approval_id": "<uuid>", "action": "process_refund", "parameters": {"order_id": string, "amount": float, "reason": string}, "message": "Action process_refund has NOT been executed yet. It requires human approval. Approval request <uuid> created."}`.
- Never executes the refund until explicitly approved via FEAT-20.
