import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.grpc_server import BrainServicer
import scripts.grpc_server as grpc_server
import ziva_brain_pb2

class TestBrainServicer(unittest.TestCase):

    def setUp(self):
        # We define a helper to init service with mocks
        pass

    def _create_servicer(self):
        # Ensure 'openai' exists on the module before we patch it, or use create=True on the patch itself
        # But since we are calling it inside the context, let's use a simpler approach.
        with patch('scripts.grpc_server.LLM'), patch('scripts.grpc_server.openai', create=True):
             servicer = BrainServicer()
             servicer.llm = Mock()
             return servicer

    @patch('scripts.grpc_server.LLM', autospec=True)
    @patch('scripts.grpc_server.openai', create=True)
    def test_init_success(self, mock_openai, mock_llm):
        mock_llm.return_value = Mock()
        servicer = BrainServicer()
        self.assertFalse(servicer.use_fallback)
        self.assertIsNotNone(servicer.llm)

    @patch('scripts.grpc_server.LLM', side_effect=Exception("CUDA Error"))
    @patch('scripts.grpc_server.openai', create=True)
    def test_init_fallback(self, mock_openai, mock_llm):
        servicer = BrainServicer()
        self.assertTrue(servicer.use_fallback)
        self.assertIsNotNone(servicer.client)

    def test_validate_request_valid(self):
        servicer = self._create_servicer()
        request = Mock(prompt="Hello world", temperature=1.0, max_tokens=100)
        servicer._validate_request(request)

    def test_validate_request_empty_prompt(self):
        servicer = self._create_servicer()
        request = Mock(prompt="", temperature=1.0, max_tokens=100)
        with self.assertRaises(ValueError) as cm:
            servicer._validate_request(request)
        self.assertIn("empty", str(cm.exception))

    def test_validate_request_invalid_temperature(self):
        servicer = self._create_servicer()
        request = Mock(prompt="Hello", temperature=3.0, max_tokens=100)
        with self.assertRaises(ValueError) as cm:
            servicer._validate_request(request)
        self.assertIn("Temperature", str(cm.exception))

    def test_validate_request_invalid_max_tokens(self):
        servicer = self._create_servicer()
        request = Mock(prompt="Hello", temperature=1.0, max_tokens=0)
        with self.assertRaises(ValueError) as cm:
            servicer._validate_request(request)
        self.assertIn("Max tokens", str(cm.exception))

    @patch('scripts.grpc_server.logger')
    def test_generate_native_llm(self, mock_logger):
        servicer = self._create_servicer()
        request = Mock(prompt="Hello", temperature=1.0, max_tokens=50, stop_sequences=[])
        context = Mock()
        mock_output = Mock()
        mock_output.outputs = [Mock()]
        mock_output.outputs[0].text = "Generated text"
        mock_output.outputs[0].token_ids = [1, 2, 3]
        servicer.llm.generate.return_value = [mock_output]

        response = servicer.Generate(request, context)

        self.assertIsNotNone(response, "Response should not be None")
        self.assertEqual(response.text, "Generated text")
        self.assertEqual(response.token_usage, 3)
        self.assertTrue(response.finished)
        servicer.llm.generate.assert_called_once()

    @patch('scripts.grpc_server.logger')
    def test_generate_fallback(self, mock_logger):
        servicer = self._create_servicer()
        servicer.use_fallback = True
        servicer.client = Mock()
        request = Mock(prompt="Hello", temperature=1.0, max_tokens=50, stop_sequences=[])
        context = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Fallback text"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 10
        servicer.client.chat.completions.create.return_value = mock_response

        response = servicer.Generate(request, context)

        self.assertEqual(response.text, "Fallback text")
        self.assertEqual(response.token_usage, 10)
        self.assertTrue(response.finished)

if __name__ == '__main__':
    unittest.main()