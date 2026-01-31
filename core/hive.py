import logging
from core.llm import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HiveMind")


class HiveMind:
    """
    Orchestrates distributed intelligence and consensus.
    """

    def __init__(self):
        self.llm = LLMService(model="ziva-base:latest")

    def consult_swarm(self, query: str) -> str:
        """
        Asks the swarm and returns the consensus answer.
        """
        logger.info("🐝 Hive Mind Activated. Consulting peers...")
        logger.info("🤖 Node A (Ziva) thinking...")
        answer_a = self.llm.completion(f"Answer this query concisely: {query}")
        answer_b = self._ask_peer("Gabrielle", query)

        if answer_a.strip() == answer_b.strip():
            logger.info("✅ Full Consensus reached immediately.")
            return answer_a

        logger.info("⚠️ Divergence detected. Arbitrating...")
        final_answer = self._arbitrate(query, answer_a, answer_b)
        return final_answer

    def _ask_peer(self, peer_name: str, query: str) -> str:
        """
        Queries a peer node.
        """
        logger.info(f"📡 Sending query to Node {peer_name}...")
        try:
            from core.p2p_learning import GabrielleConnector
            connector = GabrielleConnector()
            if connector.is_connected:
                response = connector.ask_remote_llm(query)
                if response:
                    logger.info("✅ Received answer from Remote Node via RPC!")
                    return response
        except Exception as e:
            logger.warning(f"RPC Connection failed: {e}")

        logger.info("⚠️ Remote Node unreachable. Switching to Local Simulation.")
        prompt = f"""
        Persona: You are {peer_name}, a skeptical AI assistant.
        Query: {query}
        Task: Provide an answer independently.
        """
        return self.llm.completion(prompt).strip()

    def _arbitrate(self, query: str, ans_a: str, ans_b: str) -> str:
        """
        Uses LLM to judge the best answer.
        """
        prompt = f"""
        I have two conflicting answers.
        Query: "{query}"
        Answer A (Ziva): "{ans_a}"
        Answer B (Gabrielle): "{ans_b}"
        TASK:
        1. Compare the facts.
        2. Identify who is likely correct.
        3. Synthesize the FINAL, correct answer.
        OUTPUT: Only the final answer.
        """
        return self.llm.completion(prompt).strip()


if __name__ == "__main__":
    hive = HiveMind()
    q = "What is the capital of Australia?"
    print(f"\n🐝 Consensus Answer: {hive.consult_swarm(q)}")