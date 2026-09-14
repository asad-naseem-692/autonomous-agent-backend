from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.order import Order

def seed():
    with SessionLocal() as db:
        print("Seeding realistic customers and orders...")

        now = datetime.now(timezone.utc)

        # 1. Alice Smith
        alice = db.query(Customer).filter(Customer.id == "c001-alice-smith").first()
        if not alice:
            alice = Customer(
                id="c001-alice-smith",
                name="Alice Smith",
                email="alice@example.com",
                balance=150.0,
                created_at=now - timedelta(days=30),
            )
            db.add(alice)
            db.commit()
            print("Created customer: Alice Smith")

        # 2. Bob Jones
        bob = db.query(Customer).filter(Customer.id == "c002-bob-jones").first()
        if not bob:
            bob = Customer(
                id="c002-bob-jones",
                name="Bob Jones",
                email="bob@example.com",
                balance=0.0,
                created_at=now - timedelta(days=20),
            )
            db.add(bob)
            db.commit()
            print("Created customer: Bob Jones")

        # 3. Charlie Brown
        charlie = db.query(Customer).filter(Customer.id == "c003-charlie-brown").first()
        if not charlie:
            charlie = Customer(
                id="c003-charlie-brown",
                name="Charlie Brown",
                email="charlie@example.com",
                balance=45.5,
                created_at=now - timedelta(days=15),
            )
            db.add(charlie)
            db.commit()
            print("Created customer: Charlie Brown")

        # 4. Diana Prince
        diana = db.query(Customer).filter(Customer.id == "c004-diana-prince").first()
        if not diana:
            diana = Customer(
                id="c004-diana-prince",
                name="Diana Prince",
                email="diana@example.com",
                balance=250.0,
                created_at=now - timedelta(days=10),
            )
            db.add(diana)
            db.commit()
            print("Created customer: Diana Prince")

        # Orders
        orders_to_seed = [
            ("ord-101", "c001-alice-smith", "delivered", 75.0, now - timedelta(days=25)),
            ("ord-102", "c001-alice-smith", "shipped", 75.0, now - timedelta(days=10)),
            ("ord-103", "c002-bob-jones", "pending", 120.0, now - timedelta(days=5)),
            ("ord-104", "c003-charlie-brown", "processing", 45.5, now - timedelta(days=3)),
            ("ord-105", "c004-diana-prince", "delivered", 200.0, now - timedelta(days=8)),
            ("ord-106", "c004-diana-prince", "cancelled", 50.0, now - timedelta(days=2)),
        ]

        for ord_id, cust_id, status, amount, created_at in orders_to_seed:
            existing = db.query(Order).filter(Order.id == ord_id).first()
            if not existing:
                order = Order(
                    id=ord_id,
                    customer_id=cust_id,
                    status=status,
                    amount=amount,
                    created_at=created_at,
                )
                db.add(order)
                print(f"Created order: {ord_id}")

        db.commit()
        print("Seeding completed successfully!")

if __name__ == "__main__":
    seed()
