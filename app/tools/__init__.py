from app.tools.find_customer import find_customer
from app.tools.get_order import get_order
from app.tools.get_order_history import get_order_history
from app.tools.calculate_balance import calculate_balance
from app.tools.apply_credit import apply_credit
from app.tools.process_refund import process_refund
from app.tools.cancel_order import cancel_order
from app.tools.update_order_status import update_order_status

READ_TOOLS = [
    find_customer,
    get_order,
    get_order_history,
    calculate_balance,
]

WRITE_TOOLS = [
    apply_credit,
    process_refund,
    cancel_order,
    update_order_status,
]

ALL_TOOLS = READ_TOOLS + WRITE_TOOLS

__all__ = [
    "find_customer",
    "get_order",
    "get_order_history",
    "calculate_balance",
    "apply_credit",
    "process_refund",
    "cancel_order",
    "update_order_status",
    "READ_TOOLS",
    "WRITE_TOOLS",
    "ALL_TOOLS",
]
