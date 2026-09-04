# Feature: Update Order Status Tool
**Owner:** Backend | **Module:** Business Tools (Write)

## Goal
Change an order's status — only after human approval.

## Scope
- `app/tools/update_order_status.py`: typed tool function.
- Input: order id, new status.
- Same approval-gated pattern as FEAT-15 — intercepts execution, writes to
  `approval_requests` and `execution_logs`, and returns structured JSON payload:
  `{"status": "pending_approval", "approval_id": "<uuid>", "action": "update_order_status", "parameters": {"order_id": string, "new_status": string}, "message": "Action update_order_status has NOT been executed yet. It requires human approval. Approval request <uuid> created."}`.
- Never executes status update until explicitly approved via FEAT-20.
