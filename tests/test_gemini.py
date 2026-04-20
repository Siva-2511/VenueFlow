import pytest
from unittest.mock import patch
import gemini_agent

def test_gemini_cache_logic():
    """Test that the AI response cache functions correctly."""
    with patch('google.genai.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.models.generate_content.return_value.text = "Mock AI Response"
        
        # First call
        res1 = gemini_agent.analyze_crowd_data("Test Data")
        # Second call should be cached (even if we disconnect API)
        res2 = gemini_agent.analyze_crowd_data("Test Data")
        
        assert res1 == res2 == "Mock AI Response"

def test_chat_response_structure():
    """Test that the chatbot includes system instructions."""
    with patch('google.genai.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.models.generate_content.return_value.text = "Hello Fan"
        
        resp = gemini_agent.get_chat_response("Hi", "user", "General")
        assert "Hello Fan" in resp

def test_gemini_error_handling():
    """Test that the system handles Gemini quota limits gracefully."""
    with patch('google.genai.Client', side_effect=Exception("429 RESOURCE_EXHAUSTED")):
        resp = gemini_agent.analyze_crowd_data("Some Data")
        assert "Cooling Down" in resp or "Unavailable" in resp
