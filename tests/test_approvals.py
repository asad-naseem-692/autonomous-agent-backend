import json
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.customer import Customer
from app.models.order import Order
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.execution_log import ExecutionLog
from app.models.approval_request import ApprovalRequest
from app.tools.apply_credit import apply_credit
from app.tools.process_refund import process_refund
from app.tools.cancel_order import cancel_order
from app.tools.update_order_status import update_order_status

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_tables():
    Base.metadata.create_all(bind=engine)
    yield


def test_write_tools_return_pending_and_zero_db_mutation():
    with SessionLocal() as db:
        cust = db.query(Customer).filter(Customer.id == "c001-alice-smith").first()
        if not cust:
            cust = Customer(id="c001-alice-smith", name="Alice Smith", email="alice@example.com", balance=150.0)
            db.add(cust)
        ord1 = db.query(Order).filter(Order.id == "ord-101").first()
        if not ord1:
            ord1 = Order(id="ord-101", customer_id="c001-alice-smith", status="delivered", amount=75.0)
            db.add(ord1)
        db.commit()

    with SessionLocal() as db:
        initial_balance = db.query(Customer).filter(Customer.id == "c001-alice-smith").first().balance
        initial_status = db.query(Order).filter(Order.id == "ord-101").first().status

    r1 = json.loads(apply_credit.__wrapped__(customer_id="c001-alice-smith", amount=50.0, reason="Loyalty"))
    assert r1["status"] == "pending_approval" and r1["action"] == "apply_credit"

    r2 = json.loads(process_refund.__wrapped__(order_id="ord-101", amount=75.0, reason="Defect"))
    assert r2["status"] == "pending_approval" and r2["action"] == "process_refund"

    r3 = json.loads(cancel_order.__wrapped__(order_id="ord-101", reason="Duplicate"))
    assert r3["status"] == "pending_approval" and r3["action"] == "cancel_order"

    r4 = json.loads(update_order_status.__wrapped__(order_id="ord-101", new_status="processing"))
    assert r4["status"] == "pending_approval" and r4["action"] == "update_order_status"

    # CRITICAL: direct DB check -- no mutations
    with SessionLocal() as db:
        assert db.query(Customer).filter(Customer.id == "c001-alice-smith").first().balance == initial_balance, \
            "FAIL: balance changed without approval!"
        assert db.query(Order).filter(Order.id == "ord-101").first().status == initial_status, \
            "FAIL: order status changed without approval!"


def test_approve_applies_credit_and_transitions_log():
    email = f"op_{uuid.uuid4().hex[:8]}@test.com"
    client.post("/auth/signup", json={"name": "Op", "email": email, "password": "Password123!"})
    login = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    token = login.json()["access_token"]
    user_id = login.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    conv_id, approval_id, exec_log_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())

    with SessionLocal() as db:
        start_balance = db.query(Customer).filter(Customer.id == "c001-alice-smith").first().balance
        db.add(Conversation(id=conv_id, user_id=user_id, title="Approve Test"))
        db.add(ApprovalRequest(
            id=approval_id, conversation_id=conv_id,
            tool_name="apply_credit",
            tool_input={"customer_id": "c001-alice-smith", "amount": 20.0, "reason": "Bonus"},
            status="pending",
        ))
        db.add(ExecutionLog(
            id=exec_log_id, conversation_id=conv_id,
            tool_name="apply_credit",
            tool_input={"customer_id": "c001-alice-smith", "amount": 20.0, "reason": "Bonus"},
            tool_output={"status": "pending_approval"},
            status="pending_approval",
        ))
        db.commit()

    get_r = client.get(f"/approvals/{approval_id}", headers=headers)
    assert get_r.status_code == 200 and get_r.json()["status"] == "pending"

    apr_r = client.post(f"/approvals/{approval_id}/approve", headers=headers)
    assert apr_r.status_code == 200 and apr_r.json()["status"] == "approved"

    with SessionLocal() as db:
        assert db.query(Customer).filter(Customer.id == "c001-alice-smith").first().balance == round(start_balance + 20.0, 2)
        appr = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
        assert appr.status == "approved" and appr.resolved_by == user_id and appr.resolved_at is not None
        elog = db.query(ExecutionLog).filter(ExecutionLog.id == exec_log_id).first()
        assert elog.status == "executed" and elog.tool_output["status"] == "executed"
        msgs = db.query(Message).filter(Message.conversation_id == conv_id).all()
        assert any("Approved" in m.content for m in msgs)


def test_reject_zero_mutation_and_log_transition():
    email = f"rej_{uuid.uuid4().hex[:8]}@test.com"
    client.post("/auth/signup", json={"name": "Rej", "email": email, "password": "Password123!"})
    login = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    token = login.json()["access_token"]
    user_id = login.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    conv_id, approval_id, exec_log_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())

    with SessionLocal() as db:
        status_before = db.query(Order).filter(Order.id == "ord-101").first().status
        db.add(Conversation(id=conv_id, user_id=user_id, title="Reject Test"))
        db.add(ApprovalRequest(
            id=approval_id, conversation_id=conv_id,
            tool_name="cancel_order",
            tool_input={"order_id": "ord-101", "reason": "Accidental"},
            status="pending",
        ))
        db.add(ExecutionLog(
            id=exec_log_id, conversation_id=conv_id,
            tool_name="cancel_order",
            tool_input={"order_id": "ord-101", "reason": "Accidental"},
            tool_output={"status": "pending_approval"},
            status="pending_approval",
        ))
        db.commit()

    rej_r = client.post(f"/approvals/{approval_id}/reject", headers=headers)
    assert rej_r.status_code == 200 and rej_r.json()["status"] == "rejected"

    with SessionLocal() as db:
        assert db.query(Order).filter(Order.id == "ord-101").first().status == status_before, \
            "FAIL: order mutated on rejection!"
        appr = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
        assert appr.status == "rejected" and appr.resolved_by == user_id
        elog = db.query(ExecutionLog).filter(ExecutionLog.id == exec_log_id).first()
        assert elog.status == "rejected"
        msgs = db.query(Message).filter(Message.conversation_id == conv_id).all()
        assert any("Rejected" in m.content or "rejected" in m.content for m in msgs)


def test_unauthorized_and_double_action():
    email1 = f"ua1_{uuid.uuid4().hex[:8]}@test.com"
    client.post("/auth/signup", json={"name": "UA1", "email": email1, "password": "Password123!"})
    r1 = client.post("/auth/login", json={"email": email1, "password": "Password123!"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    user1_id = r1.json()["user"]["id"]

    email2 = f"ua2_{uuid.uuid4().hex[:8]}@test.com"
    client.post("/auth/signup", json={"name": "UA2", "email": email2, "password": "Password123!"})
    r2 = client.post("/auth/login", json={"email": email2, "password": "Password123!"})
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    conv_id, approval_id = str(uuid.uuid4()), str(uuid.uuid4())
    with SessionLocal() as db:
        db.add(Conversation(id=conv_id, user_id=user1_id, title="Unauth Test"))
        db.add(ApprovalRequest(
            id=approval_id, conversation_id=conv_id,
            tool_name="cancel_order",
            tool_input={"order_id": "ord-101", "reason": "Test"},
            status="pending",
        ))
        db.commit()

    assert client.post(f"/approvals/{approval_id}/approve", headers=h2).status_code == 403
    assert client.post(f"/approvals/{approval_id}/approve", headers=h1).status_code == 200
    assert client.post(f"/approvals/{approval_id}/approve", headers=h1).status_code == 400
    assert client.post(f"/approvals/{approval_id}/reject", headers=h1).status_code == 400
