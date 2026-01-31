import logging
import json
import os
from typing import List, Dict

from core.llm import LLMService
from core.rag_helper import get_rag_helper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Learner")


class Learner:
    """
    Autodidact Agent.
    Identifies knowledge gaps, performs web research, and fills them.
    """

    def __init__(self):
        self.llm = LLMService(model="ziva-base:latest")
        self.rag = get_rag_helper()
        self.gaps_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "knowledge_gaps.json")

    def study_session(self):
        """
        Main cycle: Load Gaps -> Research -> Memorize -> Clear Gaps.
        """
        logger.info("🎓 Beginning Study Session...")
        gaps = self._load_gaps()
        if not gaps:
            logger.info("🎓 No knowledge gaps detected. Skipping study.")
            return
        logger.info(f"🎓 Found {len(gaps)} gaps via ThoughtPolice logs.")
        for gap in gaps:
            topic = gap.get("topic")
            if not topic:
                continue
            logger.info(f"🔎 Researching topic: '{topic}'")
            raw_info = self._research_web(topic)
            if not raw_info:
                logger.warning(f"Could not find info for {topic}.")
                continue
            
            # Semantic Validation Step
            if not self._validate_relevance(topic, raw_info):
                logger.warning(f"🗑️ Rejected irrelevant content for topic: {topic}")
                continue
                
            fact = self._synthesize(topic, raw_info)
            self._memorize(topic, fact)
        self._clear_gaps()
        logger.info("🎓 Study Session Complete.")

    def _load_gaps(self) -> List[Dict]:
        """Loads gaps from JSON."""
        if not os.path.exists(self.gaps_file):
            return []
        try:
            with open(self.gaps_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading gaps: {e}")
            return []

    def _clear_gaps(self):
        """Clears the gaps file."""
        try:
            with open(self.gaps_file, 'w') as f:
                json.dump([], f)
        except Exception:
            pass

    def _research_web(self, topic: str) -> str:
        """
        Executes web search using SearXNG (standard tool).
        """
        try:
            from core.tools.searxng import SearXNGClient
            client = SearXNGClient()
            results = client.search(topic, num_results=3)
            
            if results:
                formatted = []
                for r in results:
                    title = r.get('title', 'No Title')
                    snippet = r.get('snippet', 'No content')
                    formatted.append(f"Source: {title} - {snippet}")
                return "\n".join(formatted)
            else:
                logger.warning(f"SearXNG: No results found for {topic}")
                return ""

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return ""

    def _synthesize(self, topic: str, raw_text: str) -> str:
        """
        Compresses raw web results into a concise fact.
        """
        prompt = f"""
        Topic: {topic}
        Raw Search Data:
        {raw_text[:2000]}

        TASK: Synthesize the search data into a single, comprehensive knowledge block.
        - Focus on facts.
        - Ignore noise.

        OUTPUT: The synthesized fact.
        """
        res = self.llm.completion(prompt)
        return f"LEARNED FACT ({topic}): {res.strip()}"

    def _validate_relevance(self, topic: str, content: str) -> bool:
        """
        Asks LLM to validate if content is actually relevant to the topic.
        Returns True if relevant.
        """
        prompt = f"""
        [VALIDATION TASK]
        Topic: {topic}
        Content Found:
        {content[:1500]}
        
        Is this content TECHNICALLY relevant to the topic?
        - If the content discusses grammar, dictionaries, or unrelated definitions -> NO.
        - If the content discusses the specific technical subject -> YES.
        
        Reply with a JSON: {{"relevant": true/false, "reason": "why"}}
        """
        try:
            res = self.llm.completion(prompt, temperature=0.1)
            # Simple parsing fallback
            if '"relevant": true' in res.lower():
                return True
            if '"relevant": false' in res.lower():
                logger.info(f"Validation Reject Reason: {res}")
                return False
            
            # If JSON parsing fails but LLM is chatty, default to strict (False) unless sure
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def _memorize(self, topic: str, fact: str):
        """
        Injects into Qdrant.
        """
        logger.info(f"🧠 Memorizing new fact about {topic}...")
        emb = self.rag.get_embedding(fact)
        if emb:
            self.rag.vector_store.add_text(
                text=fact,
                embedding=emb,
                metadata={
                    "type": "autodidact_fact",
                    "source": "web_research"}
            )


if __name__ == "__main__":
    learner = Learner()
    if not os.path.exists(learner.gaps_file):
        os.makedirs(os.path.dirname(learner.gaps_file), exist_ok=True)
        with open(learner.gaps_file, 'w') as f:
            json.dump([{"topic": "quantum computing basics"}], f)
    learner.study_session()