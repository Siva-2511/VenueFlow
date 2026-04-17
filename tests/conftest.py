import pytest
import os
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['DEBUG'] = False
    
    # Use a mock or temporary D1 client if needed
    os.environ['GEMINI_API_KEY'] = 'test-key-12345'
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def mock_gemini(mocker):
    """Fixture to mock Gemini API calls."""
    mock_client = mocker.patch('gemini_agent.client')
    mock_response = mocker.Mock()
    mock_response.text = "Mocked AI Response: Everything is running smoothly at the stadium! 🏏"
    mock_client.models.generate_content.return_value = mock_response
    return mock_client
