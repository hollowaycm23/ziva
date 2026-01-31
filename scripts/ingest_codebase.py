#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path
from typing import List

# Setup Path
sys.path.append(os.getcwd())

from core.rag_helper import get_rag_helper

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CodeIngest")

# Configuration
PROJECT_ROOT = Path(os.getcwd())
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'node_modules', '.gemini', 'tmp', 'data', 'logs', 'site-packages', 'cache'}
INCLUDE_EXTENSIONS = {'.py', '.sh', '.yml', '.yaml', '.md', '.json'}
CHUNK_SIZE = 1500  # Characters (roughly 300-400 tokens)
CHUNK_OVERLAP = 200

def get_files_to_ingest(root: Path) -> List[Path]:
    files = []
    for path in root.rglob('*'):
        # Check directories to ignore
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
            
        if path.is_file() and path.suffix in INCLUDE_EXTENSIONS:
            # Skip large files or specific files if needed
            if "package-lock.json" in path.name: 
                continue
            if path.stat().st_size > 100 * 1024: # Skip files > 100KB to avoid excessive token usage
                logger.warning(f"Skipping large file: {path}")
                continue
            files.append(path)
    return files

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

def ingest_codebase():
    logger.info(f"📂 Scanning codebase at: {PROJECT_ROOT}")
    files = get_files_to_ingest(PROJECT_ROOT)
    logger.info(f"Found {len(files)} files to ingest.")
    
    rag = get_rag_helper()
    
    total_chunks = 0
    processed_files = 0
    
    for i, file_path in enumerate(files):
        try:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            
            # Read content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                logger.warning(f"Skipping binary/non-utf8 file: {rel_path}")
                continue
                
            if not content.strip():
                continue

            # Format content header for better context
            file_header = f"File: {rel_path}\nLanguage: {file_path.suffix}\n---\n"
            
            # Chunking
            raw_chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
            
            for chunk_idx, chunk in enumerate(raw_chunks):
                # Prepare text for embedding (Header + Chunk)
                full_text = f"{file_header}{chunk}"
                
                emb = rag.get_embedding(full_text)
                if emb:
                    meta = {
                        "source": "codebase",
                        "file_path": str(rel_path),
                        "file_name": file_path.name,
                        "chunk_index": chunk_idx,
                        "type": "code_repository"
                    }
                    rag.vector_store.add_text(full_text, emb, meta)
                    total_chunks += 1
            
            processed_files += 1
            sys.stdout.write(f"\rProgress: {processed_files}/{len(files)} files ({total_chunks} chunks)")
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    print(f"\n\n✅ Ingestion Complete!")
    print(f"Total Files Processed: {processed_files}")
    print(f"Total Chunks Indexed: {total_chunks}")

if __name__ == "__main__":
    ingest_codebase()
