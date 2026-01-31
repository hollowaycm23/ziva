import logging
import json
from typing import List, Dict, Optional

from core.database import DatabaseManager
from core.llm import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThoughtPolice")


class ThoughtPolice:
    """
    Subsystem responsible for Metacognition and Self-Correction.
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.llm = LLMService(model="ziva-base:latest")
        self.failure_keywords = [
            "error", "erro", "failed", "falhou", "wrong", "errado",
            "bug", "exception", "traceback", "não funciona", "not working"
        ]

    def scan_for_failures(self, limit: int = 10) -> List[Dict]:
        """
        Scans recent interactions for potential failures.
        """
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, session_id, content, timestamp FROM interactions "
            "WHERE role = 'user' ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        failures = []
        for row in rows:
            msg_id, session_id, content, timestamp = row
            if any(kw in content.lower() for kw in self.failure_keywords):
                logger.info(
                    f"🚩 Potential failure detected in msg {msg_id}: "
                    f"'{content[:30]}...'"
                )
                cursor.execute("""
                    SELECT id, content FROM interactions
                    WHERE session_id = ? AND timestamp < ? AND role = 'assistant'
                    ORDER BY timestamp DESC LIMIT 1
                """, (session_id, timestamp))
                assistant_row = cursor.fetchone()
                if not assistant_row:
                    continue
                aid, a_content = assistant_row
                cursor.execute("""
                    SELECT id, content FROM interactions
                    WHERE session_id = ? AND id < ? AND role = 'user'
                    ORDER BY timestamp DESC LIMIT 1
                """, (session_id, aid))
                original_user_row = cursor.fetchone()
                if not original_user_row:
                    continue
                uid, u_content = original_user_row
                failures.append({
                    "session_id": session_id,
                    "original_prompt": u_content,
                    "bad_response": a_content,
                    "user_complaint": content
                })
                if len(failures) >= limit:
                    break
        conn.close()
        return failures

    def contemplate(self, failure_context: Dict) -> Optional[Dict]:
        """
        Uses LLM to analyze the failure and generate a correction.
        """
        logger.info(
            f"🤔 Contemplating failure in session {failure_context['session_id']}...")
        prompt = f"""
        I need you to perform a Root Cause Analysis on a conversation failure.

        Original User Request: "{failure_context['original_prompt']}"
        My Response: "{failure_context['bad_response']}"
        User Feedback/Error: "{failure_context['user_complaint']}"

        Task:
        1. Identify what went wrong.
        2. Generate a 'Learned Lesson' (abstract rule to avoid this in future).
        3. Generate the Correct Response that should have been given.

        Format your response as a JSON object with keys: "analysis", "lesson",
        "corrected_response".
        """
        try:
            response = self.llm.completion(prompt)
            clean_response = response.replace(
                "```json", "").replace("```", "").strip()
            start = clean_response.find("{")
            end = clean_response.rfind("}")
            if start != -1 and end != -1:
                json_str = clean_response[start:end + 1]
                sanitized_str = ""
                in_quote = False
                escape = False
                for char in json_str:
                    if char == '"' and not escape:
                        in_quote = not in_quote
                    if char == '\\':
                        escape = not escape
                    else:
                        escape = False
                    if in_quote and char == '\n':
                        sanitized_str += '\\n'
                    elif in_quote and char == '\r':
                        sanitized_str += '\\r'
                    elif in_quote and char == '\t':
                        sanitized_str += '\\t'
                    else:
                        sanitized_str += char
                data = json.loads(sanitized_str)
                return data
            else:
                logger.warning("Failed to parse JSON from contemplation.")
                return None
        except Exception as e:
            logger.error(f"Contemplation failed: {e}")
            if 'json_str' in locals():
                logger.error(f"Raw String was: {json_str!r}")
            return None

    def internalize_lesson(self, lesson_data: Dict):
        """
        Saves the lesson to the Vector Database.
        """
        try:
            from core.rag_helper import get_rag_helper
            rag = get_rag_helper()
            lesson_text = (
                f"LESSON: {lesson_data['lesson']}\\n"
                f"EXAMPLE CONTEXT: {lesson_data['analysis']}"
            )
            embedding = rag.get_embedding(lesson_text)
            if embedding:
                rag.vector_store.add_text(
                    text=lesson_text,
                    embedding=embedding,
                    metadata={"type": "learned_lesson", "source": "thought_police"}
                )
                logger.info("✅ Lesson internalized successfully.")
            else:
                logger.error("Failed to generate embedding for lesson.")
        except Exception as e:
            logger.error(f"Internalization error: {e}")

    def run_cycle(self):
        """Runs one full cycle of detection -> contemplation -> learning."""
        failures = self.scan_for_failures()
        if not failures:
            logger.info("No failures detected. Good job, Ziva!")
            return
        for fail in failures:
            insight = self.contemplate(fail)
            if insight:
                self.internalize_lesson(insight)


if __name__ == "__main__":
    police = ThoughtPolice()
    police.run_cycle()