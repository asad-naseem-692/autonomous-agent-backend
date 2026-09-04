# Feature: Apply Credit Tool
**Owner:** Backend | **Module:** Business Tools (Write)

## Goal
Add a credit amount to a customer's account — but only after human approval.

## Scope
- `app/tools/apply_credit.py`: typed tool function.
- Input: customer id, amount, reason.
- **Never executes immediately.** When the agent selects this tool, the
  reasoning loop (FEAT-08) intercepts it, creates a pending approval
  request (FEAT-19) in `approval_requests`, logs to `execution_logs` with status
  "pending_approval", and returns a structured JSON payload:
  `{"status": "pending_approval", "approval_id": "<uuid>", "action": "apply_credit", "parameters": {"customer_id": string, "amount": float, "reason": string}, "message": "Action apply_credit has NOT been executed yet. It requires human approval. Approval request <uuid> created."}`.
- The actual database write only happens once a human approves it (FEAT-20).
- Once approved, applies the credit and returns confirmation.
