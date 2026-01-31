from network.transfer import TransferManager
from network.daemon import MessageDaemon
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Adiciona root ao path para imports
sys.path.append("/home/holloway/ziva")


class TestP2P(unittest.TestCase):

    @patch('network.transfer.subprocess.run')
    def test_start_transfer_check_connection(self, mock_run):
        # Setup mock for success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        tm = TransferManager(remote_host="gabrielle")
        self.assertTrue(tm.check_connection())

    @patch('network.transfer.subprocess.run')
    def test_send_file_success(self, mock_run):
        # Mock SCP success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Create dummy file
        dummy_file = "test_msg.txt"
        with open(dummy_file, "w") as f:
            f.write("test")

        tm = TransferManager(remote_host="gabrielle")
        result = tm.send_file(dummy_file, "/tmp/remote_test.txt")

        # Cleanup
        os.remove(dummy_file)

        self.assertTrue(result)
        # Verify SCP command structure
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "scp")
        self.assertIn("gabrielle:/tmp/remote_test.txt", args[-1])

    @patch('network.daemon.os.listdir')
    @patch('network.daemon.os.remove')
    @patch('network.daemon.TransferManager.send_file')
    def test_daemon_process_outbox(self, mock_send, mock_remove, mock_listdir):
        # Setup
        mock_listdir.return_value = ["msg1.json"]
        mock_send.return_value = True

        daemon = MessageDaemon()
        daemon.process_outbox()

        mock_send.assert_called_once()
        mock_remove.assert_called_once()


if __name__ == '__main__':
    unittest.main()
