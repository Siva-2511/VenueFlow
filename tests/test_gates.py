import pytest
from unittest.mock import patch

@patch('d1_client.execute')
def test_gate_load_balancing(mock_execute, client):
    """Test the 'least busy gate' logic."""
    from app import get_least_busy_gate
    mock_execute.return_value = [{'id': 4}]
    gate_id = get_least_busy_gate()
    assert gate_id == 4

@patch('d1_client.execute')
def test_gate_status_broadcast(mock_execute):
    """Test that gate status broadcasts correctly hash state."""
    from app import broadcast_gate_status
    mock_execute.return_value = [{'id': 1, 'name': 'Gate 1', 'current': 10, 'capacity': 200, 'status': 'open'}]
    # This should not raise any errors
    broadcast_gate_status()

@patch('d1_client.execute')
def test_api_stats_endpoint(mock_execute, auth_client):
    """Test the occupancy statistics API."""
    mock_execute.return_value = [{'total': 500, 'cap': 1000}]
    response = auth_client.get('/api/stats')
    assert response.status_code == 200
    assert response.json['percent'] == 50.0
