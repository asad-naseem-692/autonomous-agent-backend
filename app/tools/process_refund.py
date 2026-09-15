from agents import function_tool
from app.tools.approval_helper import create_pending_approval


@function_tool
def process_refund(order_id: str, amount: float, reason: str) -> str:
    """Process a refund for a customer order. This action requires human approval.

    Args:
        order_id: The unique identifier of the order to refund (e.g. 'ord-101').
        amount: The refund amount in USD.
        reason: The operational reason for processing the refund.
    """
    return create_pending_approval(
        tool_name="process_refund",
        parameters={"order_id": order_id, "amount": amount, "reason": reason},
    )
