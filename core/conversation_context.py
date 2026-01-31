import logging
import time
from typing import List, Dict
from collections import deque
from core.llm import LLMService

logger = logging.getLogger("ConversationContext")


class ConversationContext:
    """
    Mantém e gerencia o contexto de uma conversa.
    """

    def __init__(self, session_id: int, max_history: int = 10):
        """
        Inicializa contexto conversacional.
        """
        self.session_id = session_id
        self.max_history = max_history

        self.message_history = deque(maxlen=max_history)

        self.current_topic = None
        self.current_intent = None
        self.entities_mentioned = {}
        self.last_tool_used = None
        self.last_result = None

        self.llm = LLMService()

    def add_message(self, role: str, content: str):
        """
        Adiciona mensagem ao histórico.
        """
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

    def detect_intent(self, user_input: str) -> str:
        """
        Detecta a intenção do usuário.
        """
        prompt = f"""Analise esta mensagem e identifique a intenção:

Mensagem: "{user_input}"

Intenções possíveis: question, command, clarification, feedback.
Responda APENAS com uma palavra."""

        response = self.llm.completion(prompt, temperature=0.1, max_tokens=10)
        intent = response.strip().lower()

        if intent in ['question', 'command', 'clarification', 'feedback']:
            self.current_intent = intent
            return intent

        return 'question'

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extrai entidades nomeadas do texto.
        """
        prompt = f"""Extraia entidades nomeadas deste texto:

Texto: "{text}"

Liste APENAS as entidades encontradas no formato:
PESSOAS: nome1, nome2
LUGARES: lugar1, lugar2
CONCEITOS: conceito1, conceito2
FERRAMENTAS: ferramenta1, ferramenta2
"""

        response = self.llm.completion(prompt, temperature=0.2, max_tokens=150)
        entities = {
            "pessoas": [], "lugares": [], "conceitos": [], "ferramentas": []
        }
        for line in response.split('\n'):
            if ':' in line:
                category, items = line.split(':', 1)
                category = category.strip().lower()
                items_list = [i.strip() for i in items.split(',') if i.strip()]

                if 'pessoa' in category:
                    entities['pessoas'] = items_list
                elif 'lugar' in category:
                    entities['lugares'] = items_list
                elif 'conceito' in category:
                    entities['conceitos'] = items_list
                elif 'ferramenta' in category:
                    entities['ferramentas'] = items_list

        for category, items in entities.items():
            if items:
                if category not in self.entities_mentioned:
                    self.entities_mentioned[category] = []
                self.entities_mentioned[category].extend(items)
                self.entities_mentioned[category] = self.entities_mentioned[category][-10:]

        return entities

    def resolve_anaphora(self, user_input: str) -> str:
        """
        Resolve referências anafóricas (isso, aquilo, ele, etc).
        """
        anaphora_words = [
            'isso', 'aquilo', 'ele', 'ela', 'isto', 'este', 'esse', 'aquele']
        has_anaphora = any(word in user_input.lower()
                           for word in anaphora_words)

        if not has_anaphora or not self.message_history:
            return user_input

        recent_context = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}"
            for msg in list(self.message_history)[-3:]
        ])
        last_tool = self.last_tool_used or 'nenhuma'
        last_res = str(self.last_result)[:100] if self.last_result else 'nenhum'

        prompt = f"""Resolva as referências anafóricas nesta mensagem:

CONTEXTO RECENTE:
{recent_context}

ÚLTIMA FERRAMENTA USADA: {last_tool}
ÚLTIMO RESULTADO: {last_res}

MENSAGEM COM REFERÊNCIAS:
"{user_input}"

Reescreva a mensagem substituindo as referências.
Responda APENAS com a mensagem reescrita:"""

        resolved = self.llm.completion(prompt, temperature=0.2, max_tokens=200)
        return resolved.strip() if resolved else user_input

    def get_context_summary(self) -> str:
        """
        Gera resumo do contexto atual.
        """
        summary = []
        if self.current_topic:
            summary.append(f"Tópico atual: {self.current_topic}")
        if self.current_intent:
            summary.append(f"Intenção: {self.current_intent}")
        if self.entities_mentioned:
            for category, items in self.entities_mentioned.items():
                if items:
                    summary.append(
                        f"{category.capitalize()}: {', '.join(items[-3:])}")
        if self.last_tool_used:
            summary.append(f"Última ferramenta: {self.last_tool_used}")
        if self.message_history:
            summary.append(f"Histórico: {len(self.message_history)} mensagens")
        return "\n".join(summary) if summary else "Sem contexto prévio"

    def update_tool_context(self, tool_name: str, result: any):
        """
        Atualiza contexto após execução de ferramenta.
        """
        self.last_tool_used = tool_name
        self.last_result = result