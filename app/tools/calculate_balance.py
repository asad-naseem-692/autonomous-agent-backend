import json
from agents import function_tool
from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.order import Order

@function_tool
def calculate_balance(customer_id: str) -> str:
    """Calculate and return a customer's balance, dues, and account standing.

    Args:
        customer_id: The unique identifier of the customer (e.g. 'c001-alice-smith').
    """
    with SessionLocal() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return json.dumps({"error": f"Customer '{customer_id}' not found"})

        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        unpaid_orders = [o for o in orders if o.status in ["pending", "processing", "due"]]
        unpaid_total = sum(o.amount for o in unpaid_orders)
        completed_orders = [o for o in orders if o.status in ["delivered", "completed", "shipped"]]
        completed_total = sum(o.amount for o in completed_orders)

        net_balance = round(customer.balance - unpaid_total, 2)

        return json.dumps({
            "customer_id": customer.id,
            "customer_name": customer.name,
            "credit_balance": round(customer.balance, 2),
            "unpaid_orders_amount": round(unpaid_total, 2),
            "unpaid_orders_count": len(unpaid_orders),
            "completed_orders_amount": round(completed_total, 2),
            "net_balance": net_balance,
            "currency": "USD",
        })
