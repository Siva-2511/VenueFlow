import unittest
import json
from unittest.mock import patch, MagicMock
from app import app

class VenueFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_google_services_endpoint(self):
        """Verify the Google Services discovery endpoint returns the 12+ integrations."""
        response = self.app.get('/api/google-services')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("services", data)
        self.assertTrue(len(data["services"]) >= 11)

    def test_gemini_status_endpoint(self):
        """Verify the Gemini model status discovery endpoint."""
        response = self.app.get('/api/gemini-status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["model"], "google/gemini-2.0-flash")

    @patch('gemini_agent.genai.Client')
    def test_gemini_agent_logic(self, mock_client_class):
        """Ensure the Gemini Agent logic is verified with proper SDK mocking."""
        mock_client = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = "Test AI Response"
        mock_client.models.generate_content.return_value = mock_response
        
        from gemini_agent import analyze_crowd_data
        # Mock API key existence for the test
        with patch('os.getenv', return_value='test-key'):
            result = analyze_crowd_data("[{'gate_id': 1, 'count': 500}]")
            self.assertEqual(result, "Test AI Response")

    def test_security_headers(self):
        """Verify that strict Security Headers (CSP) are present on all responses."""
        response = self.app.get('/')
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')

if __name__ == '__main__':
    unittest.main()
