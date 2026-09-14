import json
from agents import function_tool
from app.core.database import SessionLocal
from app.models.order import Order

@function_tool
def get_order(order_id: str) -> str:
    """Get the details of a single order by its order ID.

    Args:
        order_id: The unique identifier of the order (e.g. 'ord-101').
    """
    with SessionLocal() as db:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return json.dumps({"error": f"Order '{order_id}' not found"})

        return json.dumps({
            "id": order.id,
            "customer_id": order.customer_id,
            "status": order.status,
            "amount": order.amount,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        })
