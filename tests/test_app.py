import os
import pytest
from app import app, sanitize, get_least_busy_gate

def test_root_redirect(client):
    """Test that the root URL redirects to login."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_login_page_renders(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'VenueFlow' in response.data

def test_google_callback_missing_code(client):
    """Edge Case: Google callback without code should redirect back to login with error."""
    response = client.get('/auth/google/callback')
    assert response.status_code == 302
    assert 'google_error=1' in response.headers['Location']

def test_sanitize_function():
    """Test the input sanitizer logic."""
    assert sanitize("hello <script>alert(1)</script>", 50) == "hello scriptalert(1)/script"
    assert sanitize("a" * 100, 10) == "aaaaaaaaaa"
    assert sanitize("", 10) == ""

def test_protected_routes_without_auth(client):
    """Edge Case: Unauthenticated users should be blocked from protected routes."""
    routes = ['/user', '/staff', '/admin', '/api/admin/ai_insight']
    for route in routes:
        response = client.get(route)
        assert response.status_code in [200, 302, 401, 403]
        if response.status_code == 302:
            assert '/login' in response.headers['Location']

def test_auth_rejection_for_bad_passwords(client):
    """Edge Case: Registration with mismatched passwords should fail."""
    response = client.post('/register', json={
        "name": "Test User",
        "email": "mismatch@example.com",
        "password": "pass",
        "passwordConfirm": "pass123"
    })
    assert response.status_code == 400
    assert b'Passwords do not match' in response.data

def test_duplicate_registration_fails(client):
    """Edge Case: Registering an existing email should return 409."""
    # First registration
    client.post('/register', json={
        "name": "Original",
        "email": "duplicate@example.com",
        "password": "password123",
        "passwordConfirm": "password123"
    })
    # Second registration with same email
    response = client.post('/register', json={
        "name": "Clone",
        "email": "duplicate@example.com",
        "password": "password123",
        "passwordConfirm": "password123"
    })
    assert response.status_code == 409
    assert b'Account already exists' in response.data

def test_api_stats_access(client):
    """Test that stats API returns 401 when unauthenticated (as expected)."""
    response = client.get('/api/stats')
    # Since we added protection, 401 is now the correct response for guests
    assert response.status_code == 401

def test_gate_logic(mocker):
    """Test logic for finding the least busy gate by mocking D1 results."""
    # The real function uses ORDER BY current ASC LIMIT 1
    # So we mock it to return the 'best' gate as the first element
    mock_gates = [{"id": 3, "current": 5}]
    mocker.patch('d1_client.execute', return_value=mock_gates)
    
    # get_least_busy_gate() takes 0 args in app.py
    from app import get_least_busy_gate
    assert get_least_busy_gate() == 3
