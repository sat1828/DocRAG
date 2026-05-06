"""
Tests for authentication endpoints.
"""
import pytest


def test_register_user(client):
    """Test user registration."""
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Test@123"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()


def test_login_user(client):
    """Test user login."""
    # Register first
    client.post("/api/v1/auth/register", json={
        "email": "test2@example.com",
        "password": "Test@123"
    })
    
    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "test2@example.com",
        "password": "Test@123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_current_user(client):
    """Test getting current user info."""
    # Register and get token
    client.post("/api/v1/auth/register", json={
        "email": "test3@example.com",
        "password": "Test@123"
    })
    
    login_response = client.post("/api/v1/auth/login", data={
        "username": "test3@example.com",
        "password": "Test@123"
    })
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test3@example.com"


def test_unauthorized_access(client):
    """Test unauthorized access."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]  # 401 if no creds, 403 if invalid schema
