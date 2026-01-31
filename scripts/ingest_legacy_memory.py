#!/usr/bin/env python3
import sys
import os
import json
import logging
from pathlib import Path

# Setup Path
sys.path.append(os.getcwd())

from core.rag_helper import get_rag_helper
from core.episodic_memory import EpisodicMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LegacyIngest")

TEMP_DIR = Path("tmp/memory_analysis")
CACHE_FILE = TEMP_DIR / "memory" / "web_search_cache.json"
EPISODES_FILE = TEMP_DIR / "data" / "episodic_memory" / "episodes.jsonl"

def ingest_web_cache():
    if not CACHE_FILE.exists():
        logger.warning(f"Cache file not found: {CACHE_FILE}")
        return

    logger.info(f"🔄 Ingesting Semantic Memory from {CACHE_FILE}...")
    rag = get_rag_helper()
    
    with open(CACHE_FILE, 'r') as f:
        data = json.load(f)
    
    count = 0
    total = len(data)
    
    for key, item in data.items():
        content = item.get("content")
        if not content:
            continue
            
        # Extract title or first line as pseudo-title/query for logging
        title = content.split('\n')[0][:50]
        
        # Ingest to RAG (Semantic Memory)
        # We manually use the vector store to add metadata
        emb = rag.get_embedding(content)
        if emb:
            meta = {
                "source": "legacy_web_cache",
                "original_id": key,
                "timestamp": item.get("timestamp"),
                "type": "web_content"
            }
            rag.vector_store.add_text(content, emb, meta)
            count += 1
            sys.stdout.write(f"\rProcessando Semântica: {count}/{total}")
            sys.stdout.flush()
            
    print(f"\n✅ Semântica: {count} itens importados.")

def ingest_episodes():
    if not EPISODES_FILE.exists():
        logger.warning(f"Episodes file not found: {EPISODES_FILE}")
        return

    logger.info(f"🔄 Ingesting Episodic Memory from {EPISODES_FILE}...")
    memory = EpisodicMemory()
    
    count = 0
    with open(EPISODES_FILE, 'r') as f:
        lines = f.readlines()
        
    total = len(lines)
    for line in lines:
        try:
            item = json.loads(line)
            
            # Map legacy structure to new Query/Answer format
            query = item.get("what", "Unknown Task")
            
            why = item.get("why", "")
            how = item.get("how", "")
            outcome = item.get("outcome", "")
            details = json.dumps(item.get("details", {}), ensure_ascii=False)
            
            answer = f"CONTEXTO: {why}\n\nSOLUÇÃO:\n{how}\n\nRESULTADO: {outcome}\nDETALHES: {details}"
            
            # Ingest
            memory.remember(query, answer, source="legacy_episode_import")
            count += 1
            sys.stdout.write(f"\rProcessando Episódios: {count}/{total}")
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            continue
            
    print(f"\n✅ Episódios: {count} itens importados.")

def main():
    print("🚀 Iniciando Ingestão de Memória Legada...")
    ingest_web_cache()
    ingest_episodes()
    print("🏁 Ingestão Concluída.")

if __name__ == "__main__":
    main()
