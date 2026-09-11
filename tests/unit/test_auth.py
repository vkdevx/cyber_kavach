import pytest
from fastapi.testclient import TestClient
from config.settings import settings
from backend.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from backend.api.main import app
from backend.api.deps import assert_no_active_response_action
from storage.db import init_db
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def setup_test_database():
    init_db()


client = TestClient(app)


def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_tokens():
    token_data = {"sub": "testanalyst", "role": "analyst", "uid": "usr_123"}
    access_token = create_access_token(token_data)
    decoded = decode_token(access_token)
    assert decoded["sub"] == "testanalyst"
    assert decoded["role"] == "analyst"
    assert decoded["type"] == "access"

    refresh_token = create_refresh_token(token_data)
    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh["sub"] == "testanalyst"
    assert decoded_refresh["type"] == "refresh"


def test_auth_registration_and_login_flow():
    import uuid
    uname = f"analyst_{uuid.uuid4().hex[:6]}"
    email = f"{uname}@sentinel.local"
    # 1. Register User
    reg_payload = {
        "username": uname,
        "email": email,
        "password": "SecurePassword123!",
        "role": "analyst"
    }
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == uname
    assert data["role"] == "analyst"

    # 2. Login User
    login_payload = {
        "username_or_email": uname,
        "password": "SecurePassword123!"
    }
    login_resp = client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data

    # 3. Invalid Password Failure
    invalid_login = {
        "username_or_email": uname,
        "password": "WrongPassword!"
    }
    failed_resp = client.post("/api/auth/login", json=invalid_login)
    assert failed_resp.status_code == 401

    # 4. Token Refresh
    refresh_resp = client.post("/api/auth/refresh", json={"refresh_token": token_data["refresh_token"]})
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


def test_active_response_prohibition():
    # Verify active response (IP blocking / firewall changes) is strictly rejected per diode rules
    with pytest.raises(HTTPException) as exc_info:
        assert_no_active_response_action("block_ip")
    assert exc_info.value.status_code == 400
    assert "ACTIVE_RESPONSE_PROHIBITED" in str(exc_info.value.detail)
