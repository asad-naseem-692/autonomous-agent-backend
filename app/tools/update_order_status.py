from agents import function_tool
from app.tools.approval_helper import create_pending_approval


@function_tool
def update_order_status(order_id: str, new_status: str) -> str:
    """Update the status of an existing order. This action requires human approval.

    Args:
        order_id: The unique identifier of the order (e.g. 'ord-103').
        new_status: The new status to apply (e.g. 'shipped', 'delivered', 'processing').
    """
    return create_pending_approval(
        tool_name="update_order_status",
        parameters={"order_id": order_id, "new_status": new_status},
    )
