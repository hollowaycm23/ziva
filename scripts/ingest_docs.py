from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def ingest_docs():
    print("🚀 Starting Ingestion Process...")

    # Initialize services
    # Explicitly using nomic-embed-text/latest which we saw in 'ollama list'
    llm = LLMService(model="nomic-embed-text:latest")
    vs = VectorStore()

    # Define directories/files to index
    root_dir = Path(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..')))

    # Files to index (Manual selection for MVP)
    target_files = [
        root_dir / "walkthrough.md",
        root_dir / "README.md",
        # generic check, might not exist but code handles it? I'll check
        # existence or use glob
    ]

    # Or better, let's look for all .md files in artifacts if possible, but artifacts are in .gemini.
    # Let's index the source code docs or just the walkthrough we created in the repo (or artifacts if we copy them).
    # Wait, the artifact walkthrough.md is in .gemini. I should copy it to the repo root or read it from there.
    # The user rules say: "Artifacts are special documents... written to <appDataDir>/brain...".
    # I should read from the artifact paths I know.

    artifact_dir = Path(
        "/home/holloway/.gemini/antigravity/brain/82b3edf2-1089-4c79-ae5b-49091d73150f")
    target_files = list(artifact_dir.glob("*.md"))

    print(f"📂 Found {len(target_files)} relevant documents.")

    total_chunks = 0

    for file_path in target_files:
        if not file_path.exists():
            continue

        print(f"  📄 Processing: {file_path.name}")
        text = file_path.read_text(encoding="utf-8")

        # Simple chunking by paragraphs (heuristic)
        chunks = [c.strip() for c in text.split('\n\n') if len(c.strip()) > 50]

        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = llm.embedding(chunk)

            if embedding:
                # Add to Qdrant
                vs.add_text(
                    text=chunk,
                    embedding=embedding,
                    metadata={
                        "source": file_path.name,
                        "chunk_id": i
                    }
                )
                total_chunks += 1
                sys.stdout.write(".")
                sys.stdout.flush()
            else:
                print("x", end="")

        print(f" Done.")

    print(f"\n✅ Ingestion Complete! Added {total_chunks} chunks to Qdrant.")


if __name__ == "__main__":
    ingest_docs()
