from network.transfer import TransferManager
import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.append("/home/holloway/ziva")


class TestConnectivityFailover(unittest.TestCase):

    @patch('network.transfer.subprocess.run')
    def test_failover_to_physical_ip(self, mock_run):
        # Scenario: Primary (Hostname) fails, Fallback (IP) succeeds

        # Mock results
        # 1. Primary -> Fail (returncode 255)
        res_fail = MagicMock()
        res_fail.returncode = 255

        # 2. Fallback -> Success (returncode 0)
        res_ok = MagicMock()
        res_ok.returncode = 0

        mock_run.side_effect = [res_fail, res_ok]

        tm = TransferManager(
            remote_host="gabrielle",
            fallback_ip="192.168.1.50")

        success = tm.check_connection()

        self.assertTrue(success)
        self.assertEqual(tm.active_host, "192.168.1.50")

        # Verify calls
        # 1. gabrielle
        args1 = mock_run.call_args_list[0][0][0]
        self.assertIn(
            "gabrielle",
            args1[0] if isinstance(
                args1,
                str) else str(args1))

        # 2. 192.168.1.50
        args2 = mock_run.call_args_list[1][0][0]
        self.assertIn(
            "192.168.1.50",
            args2[0] if isinstance(
                args2,
                str) else str(args2))


if __name__ == '__main__':
    unittest.main()
