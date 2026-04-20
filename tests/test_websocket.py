import pytest
from unittest.mock import patch
from app import socketio

def test_websocket_connection_auth(client):
    """Test that WebSockets respect authentication states."""
    # SocketIO testing often requires a real server, but we can test the handler logic
    with client.session_transaction() as sess:
        sess['_user_id'] = 'admin@gmail.com'
    # handler for 'connect' should run without error
    from app import on_connect
    with patch('app.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.role = 'admin'
        mock_user.gate_id = 0
        on_connect()

def test_admin_action_security(client):
    """Test that non-admins cannot trigger admin WebSocket actions."""
    from app import handle_admin_action
    with patch('app.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.role = 'user'
        # This call should return early without executing D1 queries
        with patch('d1_client.execute') as mock_exec:
            handle_admin_action({'action': 'close', 'gate_id': 1})
            mock_exec.assert_not_called()

def test_broadcast_state_changes():
    """Test the WebSocket debouncing logic."""
    from app import broadcast_gate_status
    import app
    app.last_broadcast_state = ""
    
    with patch('d1_client.execute') as mock_exec:
        mock_exec.return_value = [{'id': 1, 'status': 'open'}]
        with patch('app.socketio.emit') as mock_emit:
            # First call - should emit
            broadcast_gate_status()
            assert mock_emit.call_count == 1
            # Second call with same data - should NOT emit
            broadcast_gate_status()
            assert mock_emit.call_count == 1
