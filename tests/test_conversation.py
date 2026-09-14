import json
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine
from app.tools.find_customer import find_customer
from app.tools.get_order import get_order
from app.tools.get_order_history import get_order_history
from app.tools.calculate_balance import calculate_balance

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_tables():
    Base.metadata.create_all(bind=engine)
    yield

def test_read_tools_direct():
    # 1. find_customer
    res_raw = find_customer.__wrapped__(query="Alice")
    cust_data = json.loads(res_raw)
    assert isinstance(cust_data, list)
    assert any(c["name"] == "Alice Smith" for c in cust_data)

    # 2. get_order
    res_raw = get_order.__wrapped__(order_id="ord-101")
    ord_data = json.loads(res_raw)
    assert ord_data["id"] == "ord-101"
    assert ord_data["status"] == "delivered"
    assert ord_data["amount"] == 75.0

    # 3. get_order_history
    res_raw = get_order_history.__wrapped__(customer_id="c001-alice-smith")
    hist_data = json.loads(res_raw)
    assert hist_data["customer_id"] == "c001-alice-smith"
    assert len(hist_data["orders"]) >= 2

    # 4. calculate_balance
    res_raw = calculate_balance.__wrapped__(customer_id="c001-alice-smith")
    bal_data = json.loads(res_raw)
    assert bal_data["customer_id"] == "c001-alice-smith"
    assert bal_data["credit_balance"] == 150.0
    assert "net_balance" in bal_data

def test_conversation_unauthorized():
    response = client.post("/conversations", json={"message": "Hello agent"})
    assert response.status_code == 401

def test_conversation_create_and_agent_run():
    # 1. Sign up user
    email = f"agent_tester_{uuid.uuid4().hex[:8]}@example.com"
    signup_res = client.post("/auth/signup", json={
        "name": "Agent Tester",
        "email": email,
        "password": "Password123!"
    })
    assert signup_res.status_code == 201

    # 2. Login to get token
    login_res = client.post("/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create conversation and run agent
    conv_res = client.post("/conversations", headers=headers, json={
        "message": "Can you check details for customer Alice?"
    })
    assert conv_res.status_code == 201
    data = conv_res.json()
    assert "conversation_id" in data
    assert data["user_message"]["role"] == "user"
    assert data["agent_response"]["role"] == "assistant"
    assert len(data["agent_response"]["content"]) > 0
    assert len(data["tool_calls"]) > 0
    assert any(tc["tool_name"] == "find_customer" for tc in data["tool_calls"])

    conv_id = data["conversation_id"]

    # 4. Get conversation details
    detail_res = client.get(f"/conversations/{conv_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == conv_id
    assert len(detail["messages"]) == 2
    assert len(detail["execution_logs"]) >= 1

    # 5. List conversations
    list_res = client.get("/conversations", headers=headers)
    assert list_res.status_code == 200
    conv_list = list_res.json()
    assert any(c["id"] == conv_id for c in conv_list)
