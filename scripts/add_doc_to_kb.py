#!/usr/bin/env python3
"""
Adiciona documento ao knowledge base da Ziva (SQLite).
Usa schema existente da tabela.
"""

from pathlib import Path
from core.database import DatabaseManager
import sys
import time
sys.path.insert(0, '/home/holloway/ziva')


def add_to_knowledge_base(doc_path: str):
    """Adiciona documento ao knowledge base"""
    path = Path(doc_path)

    if not path.exists():
        print(f"❌ Arquivo não encontrado: {doc_path}")
        return

    # Ler conteúdo
    content = path.read_text(encoding='utf-8')

    # Dividir em chunks
    chunk_size = 500
    chunks = [content[i:i + chunk_size]
              for i in range(0, len(content), chunk_size)]

    print(f"📄 Documento: {path.name}")
    print(f"📊 Total de chunks: {len(chunks)}")

    # Adicionar ao banco
    db = DatabaseManager()
    conn = db._get_conn()
    cursor = conn.cursor()

    added = 0
    for idx, chunk in enumerate(chunks):
        try:
            # Usar schema existente (content, topic, priority, created_at)
            cursor.execute(
                "INSERT OR IGNORE INTO knowledge_base (content, topic, priority, created_at) VALUES (?, ?, ?, ?)",
                (chunk, "smart_web_scraping_ai_agents_llm", "high", time.time())
            )
            if cursor.rowcount > 0:
                added += 1
                print(f"✅ Chunk {idx + 1}/{len(chunks)}")
        except Exception as e:
            print(f"⚠️  Erro no chunk {idx + 1}: {e}")

    conn.commit()
    conn.close()

    print(f"\n📊 Resumo:")
    print(f"  - Total de chunks: {len(chunks)}")
    print(f"  - Adicionados: {added}")
    print(f"  - Já existiam: {len(chunks) - added}")
    print(f"\n✅ Documento adicionado ao knowledge base!")
    print(f"   A Ziva agora pode consultar este conhecimento!")


if __name__ == "__main__":
    add_to_knowledge_base(
        "/home/holloway/ziva/docs/SMART_WEB_SCRAPING_AI_AGENTS.md")
