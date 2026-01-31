import sys
from unittest.mock import MagicMock

# MOCKING DEPENDENCIES FOR CONSTRAINED ENV - MUST BE BEFORE IMPORTS
sys.modules['qdrant_client'] = MagicMock()
sys.modules['qdrant_client.models'] = MagicMock()
sys.path.append("/home/holloway/ziva")

from agent.ziva import ZivaAgent
import unittest
from unittest.mock import patch
import json
import os


class TestKnowledgeSync(unittest.TestCase):

    @patch('agent.ziva.ZivaAgent.__init__', return_value=None)
    def test_broadcast_knowledge(self, mock_init):
        agent = ZivaAgent()
        # Clean initialization for test
        mock_db = MagicMock()
        agent.db = mock_db
        agent.dispatcher = MagicMock()
        agent.dispatcher.registry.list_workers.return_value = [
            {'id': 'node08', 'status': 'active'},
            {'id': 'node09', 'status': 'active'}
        ]

        # Output directory mock
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            insights = [{
                "content": "Water is wet",
                "origin_node": "node07",
                "origin_job": 123,
                "timestamp": 1000
            }]

            agent.broadcast_knowledge(insights)

            # Check if file was written to outbox
            mock_file.assert_called()

            # Check if write was called at all
            handle = mock_file()
            handle.write.assert_called()

            # Instead of trying to reconstruct full JSON from potentially multiple write calls,
            # we verify that the payload content is present in the written data.
            # json.dump might call write multiple times.

            writes = [args[0][0] for args in handle.write.call_args_list]
            full_content = "".join(writes)

            self.assertIn("knowledge_sync", full_content)
            self.assertIn("Water is wet", full_content)

    @patch('agent.ziva.ZivaAgent.__init__', return_value=None)
    def test_process_incoming_knowledge(self, mock_init):
        # Setup Agent
        agent = ZivaAgent()
        agent.knowledge = MagicMock()
        agent.llm = MagicMock()
        agent.db = MagicMock()
        
        agent.llm.embedding.return_value = [0.1, 0.2]  # Mock embedding
        agent.llm.embedding.return_value = [0.1, 0.2]  # Mock embedding

        # Setup DB Mock Data
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        agent.db._get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock message row: id, filename, direction, source, target, content,
        # timestamp, status
        packet = json.dumps({
            "type": "knowledge_sync",
            "payload": {
                "content": "Fire is hot",
                "origin_node": "node08"
            }
        })

        mock_cursor.fetchall.return_value = [
            (1, "msg1.json", "incoming", "node08", "node07", packet, 1234, "new")]

        # Execute
        agent.process_incoming_messages()

        # Verify
        agent.llm.embedding.assert_called_with("Fire is hot")
        agent.knowledge.add_text.assert_called()  # Should call add_text

        # Verify DB update
        mock_cursor.execute.assert_called_with(
            "UPDATE messages SET status='processed' WHERE id=?", (1,))


if __name__ == '__main__':
    unittest.main()
