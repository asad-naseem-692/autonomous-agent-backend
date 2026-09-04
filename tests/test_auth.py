import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_tables():
    Base.metadata.create_all(bind=engine)
    yield

def test_signup_success():
    random_email = f"operator_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/auth/signup", json={
        "name": "Test Operator",
        "email": random_email,
        "password": "secretpassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Operator"
    assert data["email"] == random_email
    assert data["role"] == "operator"
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data

def test_signup_duplicate_email():
    random_email = f"operator_{uuid.uuid4().hex[:8]}@example.com"
    # First signup
    client.post("/auth/signup", json={
        "name": "Test Operator",
        "email": random_email,
        "password": "secretpassword123"
    })
    # Second signup with same email
    response = client.post("/auth/signup", json={
        "name": "Another Operator",
        "email": random_email,
        "password": "secretpassword123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"

def test_login_success():
    random_email = f"operator_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={
        "name": "Login Operator",
        "email": random_email,
        "password": "mypassword123"
    })
    
    response = client.post("/auth/login", json={
        "email": random_email,
        "password": "mypassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == random_email
    assert data["user"]["role"] == "operator"

def test_login_invalid_credentials():
    response = client.post("/auth/login", json={
        "email": "nonexistent_user@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_get_me_authenticated():
    random_email = f"operator_{uuid.uuid4().hex[:8]}@example.com"
    signup_res = client.post("/auth/signup", json={
        "name": "Me Operator",
        "email": random_email,
        "password": "mypassword123"
    })
    login_res = client.post("/auth/login", json={
        "email": random_email,
        "password": "mypassword123"
    })
    token = login_res.json()["access_token"]
    
    # Call /auth/me with Bearer token
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == random_email
    assert me_data["name"] == "Me Operator"

def test_get_me_unauthorized():
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_logout_success():
    response = client.post("/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Successfully logged out"

def test_password_reset_flow():
    random_email = f"reset_user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={
        "name": "Reset Operator",
        "email": random_email,
        "password": "initialpassword123"
    })

    # 1. Request reset for existing user
    req_res = client.post("/auth/request-reset", json={"email": random_email})
    assert req_res.status_code == 200
    req_data = req_res.json()
    assert "password reset instructions" in req_data["message"].lower()
    token = req_data["reset_token"]
    assert token is not None

    # 2. Confirm reset with new password
    new_pwd = "brandnewpassword456"
    confirm_res = client.post("/auth/confirm-reset", json={
        "token": token,
        "new_password": new_pwd
    })
    assert confirm_res.status_code == 200
    assert "successfully reset" in confirm_res.json()["message"].lower()

    # 3. Old password should fail
    old_login = client.post("/auth/login", json={
        "email": random_email,
        "password": "initialpassword123"
    })
    assert old_login.status_code == 401

    # 4. New password should succeed
    new_login = client.post("/auth/login", json={
        "email": random_email,
        "password": new_pwd
    })
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

    # 5. Reusing the token should fail
    reuse_res = client.post("/auth/confirm-reset", json={
        "token": token,
        "new_password": "anotherpassword789"
    })
    assert reuse_res.status_code == 400

def test_request_reset_nonexistent_user():
    response = client.post("/auth/request-reset", json={"email": "nobody_exists@example.com"})
    assert response.status_code == 200
    data = response.json()
    # Generic message returned, no token
    assert "password reset instructions" in data["message"].lower()
    assert data["reset_token"] is None
