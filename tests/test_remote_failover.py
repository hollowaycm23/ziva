from network.remote import RemoteExecutor
import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.append("/home/holloway/ziva")


class TestRemoteExecutorFailover(unittest.TestCase):

    @patch('network.remote.shutil.which')
    @patch('network.remote.subprocess.run')
    def test_executor_failover(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/ssh"

        # Scenario: Primary fails, Fallback succeeds

        # 1. Ping Primary -> Fail
        res_fail = MagicMock()
        res_fail.returncode = 255

        # 2. Ping Fallback -> Success ("ping\n")
        res_ok = MagicMock()
        res_ok.returncode = 0
        res_ok.stdout = "ping\n"

        mock_run.side_effect = [res_fail, res_ok]

        executor = RemoteExecutor("primary_host", fallback_ip="10.0.0.1")

        # Check connection triggers failover
        success = executor.check_connection()

        self.assertTrue(success)
        self.assertEqual(executor.active_host, "10.0.0.1")

        # Verify call args
        # Call 1: primary_host
        args1 = mock_run.call_args_list[0][0][0]
        self.assertIn("primary_host", args1)

        # Call 2: 10.0.0.1
        args2 = mock_run.call_args_list[1][0][0]
        self.assertIn("10.0.0.1", args2)


if __name__ == '__main__':
    unittest.main()
