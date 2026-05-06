"""
Tests for chat and RAG endpoints.
"""
import pytest


def test_chat_no_docs(client):
    """Test chat when no documents are uploaded."""
    from tests.conftest import get_token
    token = get_token(client)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Use correct field name: 'query' not 'message'
    payload = {"query": "What is GST?", "session_id": None, "document_id": None}
    
    response = client.post("/api/v1/chat/query", json=payload, headers=headers)
    print(f"DEBUG: chat_no_docs status={response.status_code} body={response.text[:200]}")
    # Should return 200 even if no docs found
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_chat_unauthorized(client):
    """Test chat without auth token."""
    response = client.post("/api/v1/chat/query", json={"query": "test"})
    assert response.status_code in [401, 403]


def test_get_chat_history(client):
    """Test getting chat history."""
    from tests.conftest import get_token
    token = get_token(client)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a session using the correct endpoint
    session_resp = client.post("/api/v1/chat/sessions", headers=headers)
    print(f"DEBUG: create_session status={session_resp.status_code} body={session_resp.text[:200]}")
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]
    
    # Get history for this session
    response = client.get(f"/api/v1/chat/history/{session_id}", headers=headers)
    print(f"DEBUG: history status={response.status_code} body={response.text[:200]}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
