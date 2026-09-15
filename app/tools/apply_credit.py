from agents import function_tool
from app.tools.approval_helper import create_pending_approval


@function_tool
def apply_credit(customer_id: str, amount: float, reason: str) -> str:
    """Apply a credit amount to a customer's account. This action requires human approval.

    Args:
        customer_id: The unique identifier of the customer (e.g. 'c001-alice-smith').
        amount: The credit amount in USD to add to the customer's balance.
        reason: The operational reason for applying the credit.
    """
    return create_pending_approval(
        tool_name="apply_credit",
        parameters={"customer_id": customer_id, "amount": amount, "reason": reason},
    )
