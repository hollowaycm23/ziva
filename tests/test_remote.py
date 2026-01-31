from extensions.remote_ops import remote_shell
from network.remote import RemoteExecutor
import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.append("/home/holloway/ziva")


class TestRemoteSSH(unittest.TestCase):

    @patch('network.remote.shutil.which')
    @patch('network.remote.subprocess.run')
    def test_run_command_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/ssh"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello Remote"
        mock_run.return_value = mock_result

        executor = RemoteExecutor("node08")
        res = executor.run_command("echo Hello")

        self.assertTrue(res['success'])
        self.assertEqual(res['stdout'], "Hello Remote")

        # Verify SSH args
        args = mock_run.call_args[0][0]
        self.assertIn("-o", args)
        self.assertIn("node08", args)

    @patch('extensions.remote_ops.RemoteExecutor')
    def test_tool_remote_shell(self, mock_cls):
        # Setup mock
        instance = mock_cls.return_value
        instance.check_connection.return_value = True
        instance.run_command.return_value = {
            "success": True,
            "stdout": "uptime result",
            "stderr": "",
            "exit_code": 0
        }

        output = remote_shell("node08", "uptime")
        self.assertIn("Sucesso", output)
        self.assertIn("uptime result", output)


if __name__ == '__main__':
    unittest.main()
