import json
from agents import function_tool
from app.core.database import SessionLocal
from app.models.order import Order

@function_tool
def get_order_history(customer_id: str) -> str:
    """Get all orders for a specific customer, sorted newest first.

    Args:
        customer_id: The unique identifier of the customer (e.g. 'c001-alice-smith').
    """
    with SessionLocal() as db:
        orders = (
            db.query(Order)
            .filter(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .all()
        )

        if not orders:
            return json.dumps({
                "customer_id": customer_id,
                "message": f"No orders found for customer '{customer_id}'",
                "orders": [],
            })

        return json.dumps({
            "customer_id": customer_id,
            "orders": [
                {
                    "id": o.id,
                    "status": o.status,
                    "amount": o.amount,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in orders
            ],
        })
