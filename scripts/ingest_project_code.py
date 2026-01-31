#!/usr/bin/env python3
import sys
import os
import glob
import logging

# Ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vector_store import VectorStore
from core.llm import LLMService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CodeIngest")

DIRECTORIES = [
    "core",
    "extensions",
    "agent",
    "scripts"
]

EXTENSIONS = [".py", ".go", ".md"]

def get_files():
    files = []
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    for d in DIRECTORIES:
        path = os.path.join(root_dir, d)
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in EXTENSIONS):
                    if "pycache" in root or ".git" in root:
                        continue
                    files.append(os.path.join(root, filename))
    return files

def ingest_code():
    store = VectorStore(collection_name="main_knowledge")
    llm = LLMService()
    
    files = get_files()
    logger.info(f"📂 Found {len(files)} files to ingest.")
    
    texts = []
    embeddings = []
    metadatas = []
    
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Skip empty files
            if not content.strip():
                continue
                
            rel_path = os.path.relpath(fpath, os.path.join(os.path.dirname(__file__), '..'))
            
            # Formatting for embedding
            # Provide context about what this text is
            formatted_text = f"Project File: {rel_path}\nLanguage: {rel_path.split('.')[-1]}\n\n{content}"
            
            # Naive size check - if too big, we might want to skip or chunk.
            # LLM embedding usually has limit (8192 tokens for nomic).
            # 1 char ~ 1 byte. 8192 tokens ~ 32KB text.
            if len(content) > 30000:
                logger.warning(f"⚠️ File {rel_path} too large ({len(content)} chars). Truncating for embedding (Keeping start).")
                embed_text = formatted_text[:30000]
            else:
                embed_text = formatted_text

            embedding = llm.embedding(embed_text)
            if not embedding:
                logger.warning(f"❌ Failed to embed {rel_path}")
                continue
                
            texts.append(formatted_text) # Store full text or embedded text? 
            # We store the formatted text so RAG retrieves "Project File: ..."
            embeddings.append(embedding)
            metadatas.append({
                "type": "code",
                "source": "project_code",
                "file_path": rel_path,
                "language": rel_path.split('.')[-1]
            })
            
            logger.info(f"✅ Prepared: {rel_path}")
            
        except Exception as e:
            logger.error(f"Error processing {fpath}: {e}")

    if texts:
        logger.info(f"💾 Ingesting {len(texts)} code modules into Qdrant...")
        # Batch insert
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            store.add_texts(
                texts[i:i+batch_size], 
                embeddings[i:i+batch_size], 
                metadatas[i:i+batch_size]
            )
            logger.info(f"   Batch {i}-{i+batch_size} done.")
            
    logger.info("🎉 Code Ingestion Complete.")

if __name__ == "__main__":
    ingest_code()
