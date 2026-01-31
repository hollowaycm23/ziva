
import os
import requests
from pydantic import BaseModel, Field

class Tools:
    class Valves(BaseModel):
        SEARXNG_URL: str = Field(
            default="http://172.17.0.1:8080",
            description="URL base do SearXNG (Use http://172.17.0.1:8080 para Docker no Linux)"
        )

    def __init__(self):
        self.valves = self.Valves()

    def fast_rag_search(self, query: str) -> str:
        """
        Realiza uma busca rápida na web usando SearXNG (Ziva Fast RAG).
        Use esta ferramenta quando precisar de informações atuais, notícias ou fatos que não estão em seu treinamento.
        
        :param query: O termo de busca ou pergunta.
        :return: Resumo formatado dos resultados da busca.
        """
        print(f"\n[OpenWebUI] Buscando por: '{query}' em {self.valves.SEARXNG_URL}...")
        
        params = {
            'q': query,
            'format': 'json',
            'language': 'pt-BR',
            'safesearch': '0'
        }
        
        try:
            # Tenta conectar ao SearXNG
            response = requests.get(f"{self.valves.SEARXNG_URL}/search", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('results'):
                return "Nenhum resultado encontrado na web."

            # Formata os resultados para o LLM com instrução anti-alucinação forte
            context_text = f"--- DADOS REAIS DA WEB (Fonte: SearXNG) ---\n"
            context_text += f"QUERY: '{query}'\n"
            context_text += "INSTRUÇÃO CRÍTICA: Responda APENAS com base nestes dados. Se a resposta não estiver aqui, diga que não sabe. NÃO INVENTE.\n\n"
            
            # Pega top 3 resultados (Otimizado para evitar Context Overflow)
            for i, result in enumerate(data['results'][:3]):
                title = result.get('title', 'Sem título')
                # Remove espaços extras e quebras
                content = result.get('content', 'Sem resumo').replace("\n", " ")
                
                # Truncate content strict limit
                if len(content) > 600:
                    content = content[:600] + "..."
                
                url = result.get('url', 'N/A')
                
                context_text += f"{i+1}. {title}: {content} ({url})\n"
                
            return context_text

        except Exception as e:
            return f"Erro ao conectar no SearXNG ({self.valves.SEARXNG_URL}): {e}"
