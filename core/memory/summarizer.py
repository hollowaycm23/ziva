import logging
from core.llm import LLMService

logger = logging.getLogger("Summarizer")

class MemorySummarizer:
    """
    Condenses conversation history into a long-term summary.
    """

    def __init__(self):
        self.llm = LLMService()

    def summarize_conversation(self, existing_summary: str, recent_messages: list) -> str:
        """
        Creates a new summary by combining the old one with recent events.
        """
        if not recent_messages:
            return existing_summary

        history_str = ""
        for msg in recent_messages:
            # Handle both dicts and LangChain message objects
            if hasattr(msg, "type"):
                role = msg.type
                content = msg.content
            elif isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
            else:
                role = "unknown"
                content = str(msg)

            # Filter out tool outputs to keep summary clean
            if role == "tool" or role == "ToolMessage":
                continue
            history_str += f"{role.upper()}: {content[:200]}...\n"

        prompt = f"""
        Você é um arquivista de memória. Abaixo está um resumo do que aconteceu até agora e as novas mensagens.
        Crie um NOVO resumo consolidado que mantenha os pontos cruciais, nomes, fatos e decisões técnicas.
        Seja conciso, mas preciso. Use Português do Brasil.

        RESUMO ANTERIOR:
        {existing_summary}

        NOVAS MENSAGENS:
        {history_str}

        NOVO RESUMO CONSOLIDADO:
        """
        
        try:
            new_summary = self.llm.completion(prompt, max_tokens=1024)
            return new_summary.strip()
        except Exception as e:
            logger.error(f"Failed to summarize: {e}")
            return existing_summary

