import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.approval_request import ApprovalRequest
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.execution_log import ExecutionLog
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.approval import ApprovalResponse

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/{id}", response_model=ApprovalResponse)
def get_approval(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details and current status of an approval request."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == id).first()
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval '{id}' not found")
    conv = db.query(Conversation).filter(Conversation.id == approval.conversation_id).first()
    if conv and conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return approval


@router.post("/{id}/approve", response_model=ApprovalResponse)
def approve_action(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve a pending sensitive action, executing the database mutation."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == id).first()
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval '{id}' not found")
    conv = db.query(Conversation).filter(Conversation.id == approval.conversation_id).first()
    if conv and conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied to approve this request")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Already {approval.status}")

    params = approval.tool_input or {}
    tool_name = approval.tool_name
    result_message = ""

    if tool_name == "apply_credit":
        cust_id = params.get("customer_id")
        amount = float(params.get("amount", 0.0))
        reason = params.get("reason", "Credit applied")
        customer = db.query(Customer).filter(Customer.id == cust_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer '{cust_id}' not found")
        customer.balance = round(customer.balance + amount, 2)
        result_message = (
            f"Successfully applied ${amount:.2f} credit to {customer.name} ({customer.id}). "
            f"New balance: ${customer.balance:.2f}. Reason: {reason}"
        )

    elif tool_name == "process_refund":
        order_id = params.get("order_id")
        amount = float(params.get("amount", 0.0))
        reason = params.get("reason", "Refund processed")
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
        order.status = "refunded"
        result_message = (
            f"Refund of ${amount:.2f} processed for order {order.id}. "
            f"Status set to refunded. Reason: {reason}"
        )

    elif tool_name == "cancel_order":
        order_id = params.get("order_id")
        reason = params.get("reason", "Cancelled")
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
        order.status = "cancelled"
        result_message = f"Order {order.id} cancelled. Reason: {reason}"

    elif tool_name == "update_order_status":
        order_id = params.get("order_id")
        new_status = params.get("new_status")
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
        order.status = new_status
        result_message = f"Order {order.id} status updated to '{new_status}'."

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {tool_name}")

    now_utc = datetime.now(timezone.utc)
    approval.status = "approved"
    approval.resolved_at = now_utc
    approval.resolved_by = current_user.id

    exec_logs = (
        db.query(ExecutionLog)
        .filter(
            ExecutionLog.conversation_id == approval.conversation_id,
            ExecutionLog.tool_name == approval.tool_name,
            ExecutionLog.status == "pending_approval",
        ).all()
    )
    for el in exec_logs:
        el.status = "executed"
        el.tool_output = {"status": "executed", "approval_id": approval.id, "result": result_message}

    db.add(Message(
        id=str(uuid.uuid4()),
        conversation_id=approval.conversation_id,
        role="assistant",
        content=f"Action Approved and Executed\n\n{result_message}",
        created_at=now_utc,
    ))
    db.commit()
    db.refresh(approval)
    resp = ApprovalResponse.model_validate(approval)
    resp.message = result_message
    return resp


@router.post("/{id}/reject", response_model=ApprovalResponse)
def reject_action(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reject a pending sensitive action. No database mutations are performed."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == id).first()
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval '{id}' not found")
    conv = db.query(Conversation).filter(Conversation.id == approval.conversation_id).first()
    if conv and conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied to reject this request")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Already {approval.status}")

    now_utc = datetime.now(timezone.utc)
    approval.status = "rejected"
    approval.resolved_at = now_utc
    approval.resolved_by = current_user.id

    exec_logs = (
        db.query(ExecutionLog)
        .filter(
            ExecutionLog.conversation_id == approval.conversation_id,
            ExecutionLog.tool_name == approval.tool_name,
            ExecutionLog.status == "pending_approval",
        ).all()
    )
    for el in exec_logs:
        el.status = "rejected"
        el.tool_output = {
            "status": "rejected",
            "approval_id": approval.id,
            "message": "Action rejected. Zero database modifications performed.",
        }

    db.add(Message(
        id=str(uuid.uuid4()),
        conversation_id=approval.conversation_id,
        role="assistant",
        content=f"Action Rejected\n\nThe proposed action '{approval.tool_name}' was rejected. No changes were made.",
        created_at=now_utc,
    ))
    db.commit()
    db.refresh(approval)
    resp = ApprovalResponse.model_validate(approval)
    resp.message = f"Action '{approval.tool_name}' rejected. No data was modified."
    return resp
