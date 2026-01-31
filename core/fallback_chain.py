#!/usr/bin/env python3
"""
Fallback Chain - Cascading tool execution for reliable responses.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from core.response_validator import ResponseValidator
from core.query_classifier import QueryClassifier, QueryType
from core.query_reformulator import QueryReformulator
from core.context_expander import ContextExpander


logger = logging.getLogger("FallbackChain")


@dataclass
class FallbackResult:
    """
    Result of fallback chain execution.
    """
    response: str
    tools_used: List[str]
    successful_tool: Optional[str]
    attempts: int
    validation: Any
    duration_ms: int


class FallbackChain:
    """
    Executes tools in fallback chain until valid response is obtained.
    """

    def __init__(
        self,
        rag=None,
        web_search=None,
        kiwix=None,
        weather=None,
        datetime_tool=None,
        llm=None,
        validator: Optional[ResponseValidator] = None,
        classifier: Optional[QueryClassifier] = None,
        reformulator: Optional[QueryReformulator] = None,
        context_expander: Optional[ContextExpander] = None
    ):
        """
        Initialize fallback chain.
        """
        self.rag = rag
        self.web_search = web_search
        self.kiwix = kiwix
        self.weather = weather
        self.datetime_tool = datetime_tool
        self.llm = llm
        self.validator = validator or ResponseValidator()
        self.classifier = classifier or QueryClassifier()
        self.reformulator = reformulator or QueryReformulator()
        self.context_expander = context_expander or ContextExpander()
        logger.info("FallbackChain initialized")

    def execute(
        self,
        query: str,
        context: Optional[Dict] = None,
        max_reformulations: int = 3
    ) -> FallbackResult:
        """
        Execute fallback chain for a query.
        """
        start_time = datetime.now()
        context = context or {}
        expanded_query = self.context_expander.expand_query(query)
        if expanded_query != query:
            logger.info(f"Query expanded: '{query}' → '{expanded_query}'")
            query = expanded_query
        result = self._try_query(query, context)
        if result.validation.is_valid:
            return result
        failed_queries = [query]
        for attempt in range(max_reformulations):
            logger.info(
                f"Reformulation attempt {attempt + 1}/{max_reformulations}")
            variations = self.reformulator.reformulate(query, failed_queries)
            if not variations:
                break
            for variation in variations:
                logger.info(f"Trying variation: '{variation}'")
                result = self._try_query(variation, context)
                if result.validation.is_valid:
                    logger.info(f"✅ Variation succeeded: '{variation}'")
                    return result
                failed_queries.append(variation)
        logger.warning("All attempts failed, using ultimate LLM fallback")
        final_response = self._ultimate_llm_fallback(query, failed_queries)
        duration_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000)
        return FallbackResult(
            response=final_response,
            tools_used=["ultimate_llm_fallback"],
            successful_tool="ultimate_llm_fallback",
            attempts=len(failed_queries) + 1,
            validation=self.validator.validate_response(
                final_response, query),
            duration_ms=duration_ms
        )

    def _try_query(
        self,
        query: str,
        context: Dict
    ) -> FallbackResult:
        start_time = datetime.now()
        context = context or {}
        classification = self.classifier.classify(query)
        query_type = classification.query_type
        logger.info(
            f"Executing fallback chain for {query_type.value} query")
        tool_order = self._get_tool_order(query_type)
        tools_used = []
        attempts = 0
        successful_tool = None
        final_response = None
        validation = None
        for tool_name in tool_order:
            attempts += 1
            tools_used.append(tool_name)
            logger.info(f"Attempt {attempts}: Trying {tool_name}")
            try:
                response = self._execute_tool(tool_name, query, context)
                if not response:
                    logger.warning(f"{tool_name} returned empty response")
                    continue
                validation = self.validator.validate_response(
                    response, query, tools_used=[tool_name]
                )
                if validation.is_valid:
                    logger.info(f"✅ {tool_name} provided valid response")
                    final_response = response
                    successful_tool = tool_name
                    break
                else:
                    logger.warning(
                        f"❌ {tool_name} response invalid: {validation.reason}")
            except Exception as e:
                logger.error(f"Error executing {tool_name}: {e}")
                continue
        if not final_response:
            logger.warning("All tools failed, using LLM reasoning")
            final_response = self._llm_fallback(query, tools_used)
            successful_tool = "llm_reasoning"
            attempts += 1
            validation = self.validator.validate_response(
                final_response, query, tools_used=["llm_reasoning"]
            )
        duration_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000)
        return FallbackResult(
            response=final_response,
            tools_used=tools_used,
            successful_tool=successful_tool,
            attempts=attempts,
            validation=validation,
            duration_ms=duration_ms
        )

    def _get_tool_order(self, query_type: QueryType) -> List[str]:
        if query_type == QueryType.WEATHER:
            return ["weather", "web_search"]
        elif query_type == QueryType.DATETIME:
            return ["datetime"]
        elif query_type == QueryType.FACTUAL:
            return ["rag", "kiwix", "web_search"]
        elif query_type == QueryType.TECHNICAL:
            return ["rag", "web_search", "kiwix"]
        elif query_type == QueryType.CONVERSATIONAL:
            return []
        else:
            return ["rag", "web_search"]

    def _execute_tool(
        self,
        tool_name: str,
        query: str,
        context: Dict
    ) -> Optional[str]:
        try:
            if tool_name == "rag" and self.rag:
                return self._try_rag(query)
            elif tool_name == "kiwix" and self.kiwix:
                return self._try_kiwix(query)
            elif tool_name == "web_search" and self.web_search:
                return self._try_web_search(query)
            elif tool_name == "weather" and self.weather:
                return self._try_weather(query)
            elif tool_name == "datetime" and self.datetime_tool:
                return self._try_datetime(query)
            else:
                logger.warning(f"Tool {tool_name} not available")
                return None
        except Exception as e:
            logger.error(f"Error in {tool_name}: {e}")
            return None

    def _try_rag(self, query: str) -> Optional[str]:
        if not self.rag:
            return None
        try:
            results = self.rag.search(query, limit=3)
            if results:
                combined = "\n\n".join([r.get("content", "")
                                       for r in results[:2]])
                return combined if len(combined) > 50 else None
        except Exception as e:
            logger.error(f"RAG error: {e}")
        return None

    def _try_kiwix(self, query: str) -> Optional[str]:
        if not self.kiwix:
            return None
        try:
            result = self.kiwix(query)
            return result if result and len(result) > 50 else None
        except Exception as e:
            logger.error(f"Kiwix error: {e}")
        return None

    def _try_web_search(self, query: str) -> Optional[str]:
        if not self.web_search:
            return None
        try:
            results = self.web_search(query, limit=3)
            if results:
                formatted = []
                for r in results[:2]:
                    title = r.get("title", "")
                    content = r.get("content", "")
                    if content:
                        formatted.append(f"{title}: {content}")
                return "\n\n".join(formatted) if formatted else None
        except Exception as e:
            logger.error(f"Web search error: {e}")
        return None

    def _try_weather(self, query: str) -> Optional[str]:
        if not self.weather:
            return None
        try:
            import re
            location_match = re.search(
                r'em\s+([a-záàâãéèêíïóôõöúçñ\s]+)', query.lower())
            location = location_match.group(
                1).strip() if location_match else None
            result = self.weather(location=location)
            return result if result else None
        except Exception as e:
            logger.error(f"Weather error: {e}")
        return None

    def _try_datetime(self, query: str) -> Optional[str]:
        if not self.datetime_tool:
            return None
        try:
            result = self.datetime_tool()
            return result if result else None
        except Exception as e:
            logger.error(f"Datetime error: {e}")
        return None

    def _ultimate_llm_fallback(self, query: str,
                               failed_attempts: List[str]) -> str:
        """
        Ultimate LLM fallback that NEVER says "não sei".
        """
        if self.llm:
            prompt = f"""Você é Ziva, uma IA que NUNCA diz "não sei".

Query: {query}
Tentativas falharam: {', '.join(failed_attempts[:3])}

Sua resposta DEVE:
1. Se tiver informação relacionada, forneça-a
2. Se não, forneça contexto geral útil sobre o tópico
3. Sugira como reformular a pergunta

NUNCA use frases como "não sei" ou "não tenho informação".

Resposta:"""
            try:
                import requests
                response = requests.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={
                        "model": "qwen2.5:7b",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("response", "")
                    if llm_response and len(llm_response) > 50:
                        return llm_response
            except Exception as e:
                logger.error(f"LLM fallback error: {e}")
        return f"""Sobre '{query}':

Não encontrei informações específicas, mas posso ajudar:

1. **Reformule a pergunta**: Tente ser mais específico.
2. **Contexto adicional**: Forneça mais detalhes.
3. **Tópicos relacionados**: Posso buscar temas relacionados.
"""