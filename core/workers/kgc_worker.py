
"""
KGC Worker - Knowledge Graph Completion
Worker responsável por ler documentos não estruturados e extrair fatos estruturados (Triplas).
Parte da Fase D: The Gardener Cycle.
"""

import logging
import json
from typing import List, Dict
from core.llm import LLMService
from core.rag_helper import RAGHelper

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KGCWorker")

class KGCompletionWorker:
    """
    Worker que realiza extração de conhecimento (SPO) de textos.
    """
    
    def __init__(self):
        self.llm = LLMService()
        self.rag = RAGHelper()
        logger.info("✅ KGC Worker Inicializado")

    def extract_triples(self, text: str) -> List[Dict[str, str]]:
        """
        Usa o LLM para extrair triplas (Subject, Predicate, Object) de um texto.
        """
        prompt = f"""
        TASK: Extract knowledge triples from the text below.
        FORMAT: Return a JSON list of objects with keys: "subject", "predicate", "object".
        LANGUAGE: Keep strict adherence to the text language (Portuguese or English).
        
        RULES:
        1. Ignore generic statements.
        2. Focus on factual relationships.
        3. Output MUST be valid JSON only. No markdown types.
        
        TEXT:
        {text[:2000]}
        
        JSON OUTPUT:
        """
        
        try:
            response = self.llm.completion(prompt, temperature=0.1, max_tokens=1024)
            # Limpar markdown se houver
            response = response.replace("```json", "").replace("```", "").strip()
            
            triples = json.loads(response)
            if isinstance(triples, list):
                return triples
            return []
            
        except Exception as e:
            logger.error(f"Erro na extração de triplas: {e}")
            return []

    def process_topic(self, topic: str, limit: int = 5) -> List[Dict]:
        """
        Busca documentos sobre um tópico e extrai novos fatos.
        """
        logger.info(f"🌿 Gardener trabalhando no tópico: {topic}")
        
        # 1. Recuperar documentos brutos (RAG)
        memories = self.rag.search_memories(query=topic, limit=limit)
        
        all_triples = []
        
        for mem in memories:
            text = mem.get('text', '')
            if not text:
                continue
                
            logger.info(f"🔎 Analisando fragmento id: {mem.get('id')}...")
            triples = self.extract_triples(text)
            
            if triples:
                logger.info(f"   -> Extraído {len(triples)} fatos.")
                all_triples.extend(triples)
                
        return all_triples

    def synthesize_to_memory(self, triples: List[Dict]):
        """
        (Futuro) Salvar triplas de volta no Qdrant como 'fatos sintéticos'.
        Por enquanto, apenas loga.
        """
        for t in triples:
            fact = f"{t.get('subject')} {t.get('predicate')} {t.get('object')}"
            logger.info(f"💾 Salvando Fato Sintético: {fact}")
            # TODO: self.rag.vector_store.add(...) com metadata={'type': 'synthetic_fact'}

if __name__ == "__main__":
    # Teste isolado
    worker = KGCompletionWorker()
    print("🧪 Testando KGC Worker com tópico: 'Ziva Architecture'")
    fatos = worker.process_topic("Ziva Architecture", limit=1)
    print(f"\n✅ Total de Fatos Extraídos: {len(fatos)}")
    print(json.dumps(fatos, indent=2, ensure_ascii=False))
