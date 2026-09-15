from agents import function_tool
from app.tools.approval_helper import create_pending_approval


@function_tool
def cancel_order(order_id: str, reason: str) -> str:
    """Cancel an existing order. This action requires human approval.

    Args:
        order_id: The unique identifier of the order to cancel (e.g. 'ord-103').
        reason: The operational reason for cancelling the order.
    """
    return create_pending_approval(
        tool_name="cancel_order",
        parameters={"order_id": order_id, "reason": reason},
    )
