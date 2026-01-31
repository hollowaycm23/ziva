import os
import sys
import argparse
import logging

# Adicionar diretório pai ao path para importar core
sys.path.append(os.getcwd())

from core.vector_stores.factory import get_vector_store
from core.rag_helper import RAGHelper

logger = logging.getLogger("Migrator")

def migrate(source_backend: str, target_backend: str, source_coll: str, target_coll: str, retention: int = None):
    print(f"\n🚀 Iniciando migração de '{source_backend}:{source_coll}' para '{target_backend}:{target_coll}'...")
    
    # Salvar backend atual para restaurar depois
    original_backend = os.getenv("ZIVA_VECTOR_STORE_BACKEND", "qdrant")
    
    try:
        # Configurar origem
        os.environ["ZIVA_VECTOR_STORE_BACKEND"] = source_backend
        source_store = get_vector_store(collection_name=source_coll)
        
        # Obter stats da origem
        source_stats = source_store.get_stats()
        total_to_migrate = source_stats.get("total_points", 0)
        print(f"📦 Origem: {source_backend} ({total_to_migrate} documentos)")
        
        # Configurar destino
        # IMPORTANTE: Se o destino for o mesmo backend, precisamos de nomes de coleção diferentes
        os.environ["ZIVA_VECTOR_STORE_BACKEND"] = target_backend
        target_store = get_vector_store(collection_name=target_coll)
        print(f"🎯 Destino: {target_backend}")
        
        count = 0
        offset = None
        while True:
            # Precisamos alternar o backend no env se forem diferentes, mas get_vector_store já instanciou
            docs, next_offset = source_store.scroll(limit=100, offset=offset)
            
            if not docs:
                break
                
            texts = [doc["text"] for doc in docs]
            vectors = [doc["vector"] for doc in docs if doc["vector"] is not None]
            metadatas = [doc["metadata"] for doc in docs]
            
            # Se nem todos os docs tiverem vetores (raro), precisamos filtrar ou regenerar
            if len(vectors) < len(texts):
                print("⚠️ Alguns documentos estão sem vetores. Ignorando no momento.")
                # Simplificação: apenas migra o que tem vetor
                valid_docs = [doc for doc in docs if doc["vector"] is not None]
                texts = [doc["text"] for doc in valid_docs]
                vectors = [doc["vector"] for doc in valid_docs]
                metadatas = [doc["metadata"] for doc in valid_docs]

            if texts:
                target_store.add_texts(texts, vectors, metadatas)
                count += len(texts)
                print(f"🛰️  Migrados: {count}/{total_to_migrate}")
            
            if next_offset is None:
                break
            offset = next_offset
            
        print(f"\n✅ Migração concluída com sucesso! {count} documentos transferidos.")
        
        # Aplica política de retenção se especificado
        if retention:
            print(f"🧹 Aplicando política de retenção de {retention} dias no destino...")
            deleted = target_store.delete_old_points(retention)
            if deleted >= 0:
                print(f"🗑️  Removidos {deleted} pontos antigos.")
            else:
                print("⚠️ Falha ao processar limpeza automática.")
        
    except Exception as e:
        logger.error(f"❌ Falha na migração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restaurar backend original
        os.environ["ZIVA_VECTOR_STORE_BACKEND"] = original_backend

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description="Ziva Vector Store Migrator")
    parser.add_argument("--from", dest="source", required=True, help="Backend de origem")
    parser.add_argument("--to", dest="target", required=True, help="Backend de destino")
    parser.add_argument("--source-coll", default="main_knowledge", help="Coleção de origem")
    parser.add_argument("--target-coll", default="main_knowledge", help="Coleção de destino")
    parser.add_argument("--retention", type=int, help="Dias para retenção de dados no destino")
    
    args = parser.parse_args()
    
    migrate(args.source, args.target, args.source_coll, args.target_coll, args.retention)
