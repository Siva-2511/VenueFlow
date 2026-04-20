import pytest
from unittest.mock import patch

def test_login_page_renders(client):
    """Test that the login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"VENUEFLOW" in response.data

def test_google_auth_redirect(client):
    """Test the Google OAuth redirection logic."""
    response = client.get('/auth/google')
    assert response.status_code == 302
    assert "accounts.google.com" in response.headers['Location']

@patch('d1_client.execute')
def test_user_registration_logic(mock_execute, client):
    """Test the registration payload handling."""
    mock_execute.return_value = [] # No existing user
    payload = {
        "email": "test@venueflow.ai",
        "name": "Test User",
        "password": "password123",
        "passwordConfirm": "password123",
        "match_teams": "CSK vs MI"
    }
    response = client.post('/register', json=payload)
    assert response.status_code == 200
    assert response.json['status'] == 'success'
