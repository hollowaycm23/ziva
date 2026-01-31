import logging
import re

logger = logging.getLogger("ContentDetector")


class ContentDetector:
    """
    Detects potential AI-generated content to prevent contamination.
    """

    def __init__(self):
        self.suspicious_patterns = [
            r"as an ai language model",
            r"I cannot fulfill this request",
            r"my cutoff date",
            r"regenerate response",
            r"in summary, ",
            r"it is important to note that",
            r"consequently,",
            r"furthermore,"
        ]

    def detect_ai_content(self, text: str) -> bool:
        """
        Returns True if content seems to be AI-generated/contaminated.
        """
        if not text:
            return False

        text_lower = text.lower()

        # 1. Check for blatant flags
        for pattern in self.suspicious_patterns:
            if pattern in text_lower:
                logger.warning(f"AI Content Flag: found '{pattern}'")
                return True

        # 2. Heuristics (simplified)
        # Too many perfect transition words often indicate AI
        transitions = [
            "moreover",
            "however",
            "therefore",
            "consequently",
            "furthermore"]
        count = sum(1 for t in transitions if t in text_lower)
        if count > 3 and len(text.split()) < 200:
            logger.warning(
                f"AI Content Flag: High transition density ({count})")
            return True

        return False
