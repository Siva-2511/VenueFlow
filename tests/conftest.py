import pytest
from app import app as flask_app
from flask_login import login_user, UserMixin

class MockUser(UserMixin):
    def __init__(self, email, role, gate_id=1):
        self.id = email
        self.email = email
        self.role = role
        self.gate_id = gate_id

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-key",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """A client with a simulated logged-in user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = 'user@example.com'
        sess['_fresh'] = True
    return client
