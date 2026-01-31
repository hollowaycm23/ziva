#!/usr/bin/env python3
"""
Project History Ingestor for Ziva
Ingests memory artifacts (brain/) and source code (ziva/) into the RAG system.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm import LLMService
from core.vector_store import VectorStore

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HistoryIngest")

class HistoryIngestor:
    def __init__(self):
        self.llm = LLMService(model="nomic-embed-text:latest")
        self.vs = VectorStore()
        logger.info("🚀 History Ingestor initialized.")

    def scan_directory(self, root_path: Path, patterns: List[str]) -> List[Path]:
        """
        Recursively scans a directory for files matching patterns.
        """
        matches = []
        if not root_path.exists():
            logger.warning(f"⚠️ Path not found: {root_path}")
            return matches

        for pattern in patterns:
            # Recursive glob
            found = list(root_path.rglob(pattern))
            matches.extend(found)
        
        logger.info(f"📂 Scanned {root_path}: found {len(matches)} files matching {patterns}")
        return matches

    def read_file(self, file_path: Path) -> Dict:
        """
        Reads a file and returns its content and metadata.
        """
        try:
            # Skip binary or very large files
            if file_path.stat().st_size > 100_000: # 100KB limit for now
                logger.warning(f"⚠️ Skipping large file: {file_path.name}")
                return None
            
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            if not content.strip():
                return None

            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "text": content,
                "type": "artifact" if "brain" in str(file_path) else "code"
            }
        except Exception as e:
            logger.error(f"❌ Error reading {file_path}: {e}")
            return None

    def ingest_files(self, files: List[Path], source_tag: str):
        """
        Ingests a list of files into the VectorStore.
        """
        total_chunks = 0
        for file_path in files:
            data = self.read_file(file_path)
            if not data:
                continue

            logger.info(f"💾 Ingesting: {data['file_name']}...")
            
            content = data['text']
            # Chunking strategy
            # For code: larger chunks to keep context? Or smaller?
            # Let's use 1000 chars for now, consistent with other scripts.
            stride = 800
            size = 1000
            chunks = [content[i:i+size] for i in range(0, len(content), stride)]
            
            for idx, chunk in enumerate(chunks):
                metadata = {
                    "source": source_tag,
                    "file_path": data['file_path'],
                    "file_name": data['file_name'],
                    "type": data['type'],
                    "ingested_at": time.time(),
                    "chunk_id": idx
                }
                
                # Embed and add with retry
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        embedding = self.llm.embedding(chunk)
                        if embedding:
                            pid = self.vs.add_text(
                                text=chunk,
                                embedding=embedding,
                                metadata=metadata
                            )
                            if pid:
                                logger.info(f"   ✅ Chunk {idx} added (ID: {pid})")
                                total_chunks += 1
                            else:
                                logger.info(f"   ⚠️ Chunk {idx} duplicate - skipped")
                        else:
                            logger.warning(f"⚠️ Failed to embed chunk {idx} of {data['file_name']}")
                        break # Success
                    except Exception as e:
                        logger.warning(f"⚠️ Error adding chunk {idx} (Attempt {attempt+1}/{max_retries}): {e}")
                        time.sleep(2) # Wait before retry
                else:
                    logger.error(f"❌ Failed to add chunk {idx} after {max_retries} attempts.")
            
            # Rate limiting - increase to avoid Qdrant overload/connection resets
            time.sleep(0.5)
            
        logger.info(f"🏁 Batch complete ({source_tag}). Total chunks added: {total_chunks}")

def run_history_ingestion():
    ingestor = HistoryIngestor()
    
    # 1. Ingest Brain Artifacts (Memory)
    brain_path = Path("/home/holloway/.gemini/antigravity/brain")
    brain_files = ingestor.scan_directory(brain_path, ["*.md"])
    ingestor.ingest_files(brain_files, source_tag="project_history_memory")
    
    # 2. Ingest Source Code (Ziva)
    project_path = Path("/home/holloway/ziva")
    # Define core directories to avoid ingesting venv, node_modules, etc.
    code_dirs = ["core", "scripts", "agent", "api", "network"]
    
    all_code_files = []
    for d in code_dirs:
        p = project_path / d
        if p.exists():
            # Python, Shell, Markdown
            all_code_files.extend(ingestor.scan_directory(p, ["*.py", "*.sh", "*.md"]))
    
    ingestor.ingest_files(all_code_files, source_tag="project_history_code")

if __name__ == "__main__":
    run_history_ingestion()
