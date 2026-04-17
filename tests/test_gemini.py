import pytest
from gemini_agent import get_chat_response, analyze_crowd_data

def test_chat_response_logic(mocker):
    """Test the chatbot response wrapper logic with mocking."""
    # Mock the Client constructor
    mock_client_inst = mocker.Mock()
    mocker.patch('google.genai.Client', return_value=mock_client_inst)
    
    mock_resp = mocker.Mock()
    mock_resp.text = "Hello! I am VenueFlow AI."
    mock_client_inst.models.generate_content.return_value = mock_resp
    
    # Needs 3 args: message, role, context_data
    response = get_chat_response("Hi", "user", {"info": "test"})
    assert "VenueFlow AI" in response

def test_analyze_crowd_data_logic(mocker):
    """Test the crowd analysis logic."""
    mock_client_inst = mocker.Mock()
    mocker.patch('google.genai.Client', return_value=mock_client_inst)
    
    mock_resp = mocker.Mock()
    mock_resp.text = "Stadium load is 50%. Suggesting Gate 4. 🏟"
    mock_client_inst.models.generate_content.return_value = mock_resp
    
    insight = analyze_crowd_data({"gates": []})
    assert "Gate 4" in insight

def test_gemini_error_handling(mocker):
    """Test that the agent handles API errors gracefully."""
    mock_client_inst = mocker.Mock()
    mocker.patch('google.genai.Client', return_value=mock_client_inst)
    mock_client_inst.models.generate_content.side_effect = Exception("Quota Exceeded")
    
    response = get_chat_response("Hi", "admin", {})
    # Since my gemini_agent.py has try/except that prints and returns a string
    assert "trouble" in response or "Bot Error" in response or "handling" in response
