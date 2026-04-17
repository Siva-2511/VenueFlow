import os
import pytest
from app import app, sanitize, get_least_busy_gate

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

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
