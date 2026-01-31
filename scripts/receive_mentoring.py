
import sys
import os
import json
import shutil
import time
from pathlib import Path

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vector_store import VectorStore
from core.llm import LLMService

def process_mentoring_inbox():
    print("🎓 Verificando inbox de mentoria (Antigravity -> Ziva)...")
    
    inbox_dir = Path("mentoring/inbox")
    archive_dir = Path("mentoring/archive")
    
    # Initialize Core Systems
    try:
        store = VectorStore(collection_name="main_knowledge")
        llm = LLMService()
    except Exception as e:
        print(f"❌ Erro ao inicializar subsistemas: {e}")
        return

    files = list(inbox_dir.glob("*.json"))
    
    if not files:
        print("📭 Inbox vazia.")
        return

    print(f"📦 Encontradas {len(files)} lições para absorver.")

    for file_path in files:
        print(f"\n📄 Processando {file_path.name}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate Structure
            lesson_id = data.get("id")
            topic = data.get("topic")
            content = data.get("content")
            
            if not content:
                print(f"⚠️ Lição inválida (sem conteúdo): {file_path}")
                continue

            # Ingest content
            print(f"🧠 Absorvendo conhecimento sobre: {topic}")
            # Simplified text for better embedding quality
            full_text = f"{topic}\n{content}"
            
            # Embed using LLM with correct model
            embedding = llm.embedding(full_text, model="nomic-embed-text")
            
            if embedding:
                meta = {
                    "source": "antigravity_tutor",
                    "type": "lesson",
                    "lesson_id": lesson_id,
                    "topic": topic,
                    "confidence": 1.0,  # Absolute Authority
                    "timestamp": time.time()
                }
                
                pid = store.add_text(full_text, embedding, meta)
                if pid:
                    print(f"✅ Lição absorvida com sucesso! ID de memória: {pid}")
                    # Archive file
                    shutil.move(str(file_path), str(archive_dir / file_path.name))
                else:
                    print("⚠️ Falha ao salvar no Qdrant (possível duplicata).")
            else:
                print("❌ Falha na vetorização.")

        except json.JSONDecodeError:
            print(f"❌ Arquivo JSON inválido: {file_path}")
        except Exception as e:
            print(f"❌ Erro ao processar lição: {e}")

if __name__ == "__main__":
    process_mentoring_inbox()
