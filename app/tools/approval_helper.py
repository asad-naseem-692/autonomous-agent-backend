import json
import uuid
from typing import Dict, Any
from app.core.database import SessionLocal
from app.core.context import current_conversation_id_var
from app.models.approval_request import ApprovalRequest


def create_pending_approval(tool_name: str, parameters: Dict[str, Any]) -> str:
    approval_id = str(uuid.uuid4())
    conv_id = current_conversation_id_var.get()

    if conv_id:
        with SessionLocal() as db:
            approval = ApprovalRequest(
                id=approval_id,
                conversation_id=conv_id,
                tool_name=tool_name,
                tool_input=parameters,
                status="pending",
            )
            db.add(approval)
            db.commit()

    payload = {
        "status": "pending_approval",
        "approval_id": approval_id,
        "action": tool_name,
        "parameters": parameters,
        "message": (
            f"Action {tool_name} has NOT been executed yet. "
            f"It requires human approval. Approval request {approval_id} created."
        ),
    }
    return json.dumps(payload)
