import unittest
from core.agent.modes import get_mode_by_slug, MODES
from core.agent.prompts import get_system_prompt
from core.agent.nodes import set_mode


class TestModes(unittest.TestCase):
    def test_get_mode_by_slug(self):
        general = get_mode_by_slug("general")
        self.assertIsNotNone(general)
        self.assertEqual(general.slug, "general")

        architect = get_mode_by_slug("architect")
        self.assertIsNotNone(architect)
        self.assertEqual(architect.slug, "architect")

        invalid = get_mode_by_slug("invalid")
        self.assertIsNone(invalid)

    def test_get_system_prompt(self):
        # Test General Prompt
        prompt_gen = get_system_prompt("general")
        self.assertIn(
            "You are ZIVA, an Elite Autonomous AI Assistant",
            prompt_gen.template)

        # Test Architect Prompt
        prompt_arch = get_system_prompt("architect")
        self.assertIn("You are ZIVA (Architect Mode)", prompt_arch.template)
        self.assertIn("Focus on high-level design", prompt_arch.template)

        # Test Coder Prompt
        prompt_coder = get_system_prompt("coder")
        self.assertIn("You are ZIVA (Coder Mode)", prompt_coder.template)
        self.assertIn(
            "Focus on writing clean, efficient, and bug-free code",
            prompt_coder.template)

    def test_set_mode_node(self):
        # Test exact match
        state = {"question": "switch to architect mode", "mode": "general"}
        new_state = set_mode(state)
        self.assertEqual(new_state["mode"], "architect")

        # Test Portuguese alias
        state = {"question": "mude para o modo programador", "mode": "general"}
        new_state = set_mode(state)
        self.assertEqual(new_state["mode"], "coder")

        # Test no change
        state = {"question": "hello world", "mode": "architect"}
        new_state = set_mode(state)
        self.assertEqual(new_state["mode"], "architect")


if __name__ == '__main__':
    unittest.main()
