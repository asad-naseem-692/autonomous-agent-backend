import json
from agents import function_tool
from app.core.database import SessionLocal
from app.models.customer import Customer

@function_tool
def find_customer(query: str) -> str:
    """Find a customer by name or email address (case-insensitive partial match allowed).

    Args:
        query: Customer name or email to search for (e.g. 'Alice' or 'bob@example.com').
    """
    with SessionLocal() as db:
        customers = db.query(Customer).filter(
            (Customer.name.ilike(f"%{query}%")) | (Customer.email.ilike(f"%{query}%"))
        ).all()

        if not customers:
            return json.dumps({"error": f"No customer found matching '{query}'"})

        return json.dumps([
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "balance": c.balance,
            }
            for c in customers
        ])
