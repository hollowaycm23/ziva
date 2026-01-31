#!/usr/bin/env python3
import sys
import os
import logging

# Setup Path
sys.path.append(os.getcwd())

from core.rag_helper import get_rag_helper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyRAG")

def main():
    print("🧪 Verificando persistência no RAG...")
    
    try:
        rag = get_rag_helper()
        text = "Ziva Verification System Check: RAG Persistence is Active."
        
        print("1. Gerando embedding...")
        emb = rag.get_embedding(text)
        if not emb:
            print("❌ Falha ao gerar embedding.")
            sys.exit(1)
            
        print(f"✅ Embedding gerado. Dimensão: {len(emb)}")
        
        print("2. Inserindo no Qdrant...")
        rag.vector_store.add_text(text, emb, {
            "source": "verification_script",
            "type": "system_check"
        })
        print("✅ Dados enviados para inserção (Upsert).")
        
        print("3. Buscando para verificar persistência...")
        # Force a small delay or just search
        import time
        time.sleep(1)
        
        results = rag.search_memories(query="Ziva Verification System Check", limit=1)
        
        found = False
        for res in results:
            if "Ziva Verification System Check" in res['text']:
                print(f"✅ SUCESSO! Memória recuperada: {res['text']}")
                print(f"   Score: {res['score']}")
                found = True
                break
        
        if not found:
            print("❌ Falha: Memória não encontrada após inserção.")
            print(f"   Resultados brutos: {results}")

    except Exception as e:
        print(f"❌ Exceção Crítica: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
