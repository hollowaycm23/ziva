from core.llm import LLMService
import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.append("/home/holloway/ziva")


class TestLLMFallback(unittest.TestCase):

    def setUp(self):
        self.llm = LLMService()
        self.llm.model_path = "/models/old.gguf"
        self.llm.start_server = MagicMock()
        self.llm.stop_server = MagicMock()
        self.llm.is_running = MagicMock(return_value=True)  # Assume running

    @patch('core.hardware.HardwareValidator.get_system_specs')
    @patch('core.hardware.HardwareValidator.validate_model_fit')
    def test_update_model_hardware_fail(self, mock_validate, mock_specs):
        # Scenario: New model fails hardware check
        mock_specs.return_value = {}
        mock_validate.return_value = False  # Fail

        result = self.llm.update_model("/models/too_big.gguf")

        self.assertFalse(result)
        # Should satisfy "volta para a anterior"
        self.assertEqual(self.llm.model_path, "/models/old.gguf")
        self.llm.stop_server.assert_not_called()  # Should not even try to stop old

    @patch('core.hardware.HardwareValidator.validate_model_fit', return_value=True)
    @patch('core.llm.LLMService.health_check')
    def test_update_model_startup_fail(self, mock_health, mock_validate):
        # Scenario: Hardware OK, but new server fails to start (health check false)
        # Needs 10 False for retry loop + potentially more if start_server calls it?
        # start_server doesn't call health_check, only update_model does 10
        # times.
        mock_health.side_effect = [False] * 12  # Sufficient for 10 retries

        result = self.llm.update_model("/models/bad_binary.gguf")

        self.assertFalse(result)  # Update failed
        self.assertEqual(self.llm.model_path, "/models/old.gguf")  # Reverted

        # Expectation:
        # 1. Stop old
        # 2. Start new
        # 3. Fail check
        # 4. Stop new
        # 5. Start old
        self.assertEqual(self.llm.stop_server.call_count, 2)
        self.assertEqual(self.llm.start_server.call_count, 2)


if __name__ == '__main__':
    unittest.main()
