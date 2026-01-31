from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
import tarfile
import json

import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def migrate_memory():
    print("📦 Starting Legacy Memory Migration...")

    backup_file = "/home/holloway/ziva/ziva_memory.tar.gz"

    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return

    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"  📂 Extracting to {temp_dir}...")
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=temp_dir)
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return

        # Initialize Services
        llm = LLMService(model="nomic-embed-text:latest")
        vs = VectorStore()
        total_ingested = 0

        # 1. Parse Episodic Memory (episodes.jsonl)
        episodes_path = Path(temp_dir) / "data/episodic_memory/episodes.jsonl"
        if episodes_path.exists():
            print("\n  🧠 Processing Episodic Memory...")
            try:
                with open(episodes_path, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        data = json.loads(line)

                        # Construct useful text representation
                        # Check what fields are available. Assuming 'content', 'summary', 'user_input' etc.
                        # Mapping unknown schema safely
                        text_parts = []
                        if "timestamp" in data:
                            text_parts.append(f"Date: {data['timestamp']}")
                        if "user_input" in data:
                            text_parts.append(f"User: {data['user_input']}")
                        if "model_response" in data:
                            text_parts.append(
                                f"Ziva: {data['model_response']}")
                        if "summary" in data:
                            text_parts.append(f"Summary: {data['summary']}")

                        full_text = "\n".join(text_parts)

                        if len(full_text) > 20:
                            emb = llm.embedding(full_text)
                            if emb:
                                vs.add_text(
                                    full_text, emb, {
                                        "source": "legacy_episodic", "original_id": data.get(
                                            "id", "unknown")})
                                total_ingested += 1
                                sys.stdout.write(".")
                                sys.stdout.flush()
            except Exception as e:
                print(f"    ⚠️ Error extracting episodes: {e}")
        else:
            print("    ⚠️ episodes.jsonl not found.")

        # 2. Parse Knowledge (JSON files)
        knowledge_dir = Path(temp_dir) / "data/knowledge"
        if knowledge_dir.exists():
            print("\n  📚 Processing Knowledge Base...")
            for json_file in knowledge_dir.rglob("*.json"):
                try:
                    data = json.loads(json_file.read_text())
                    # Assuming some structure or just dumping the JSON content
                    # as text
                    content = json.dumps(data, indent=2)

                    if len(content) > 20:
                        emb = llm.embedding(content)
                        if emb:
                            vs.add_text(
                                content, emb, {
                                    "source": f"legacy_knowledge_{
                                        json_file.name}", "path": str(json_file)})
                            total_ingested += 1
                            sys.stdout.write(".")
                            sys.stdout.flush()
                except Exception as e:
                    print(f"    ⚠️ Error processing {json_file.name}: {e}")

        # 3. Parse Sessions (sessions.json)
        sessions_path = Path(temp_dir) / "data/sessions/sessions.json"
        if sessions_path.exists():
            print("\n  🗂️ Processing Sessions...")
            try:
                data = json.loads(sessions_path.read_text())
                # If list or dict
                items = data if isinstance(
                    data, list) else [data]  # flatten if needed?
                # Actually sessions.json might be a dict of sessions.

                if isinstance(data, dict):
                    # If it's a dict, values might be the sessions
                    items = data.values()

                for item in items:
                    # Convert object to string representation
                    text = json.dumps(item)
                    if len(text) > 50:
                        emb = llm.embedding(text)
                        if emb:
                            vs.add_text(
                                text, emb, {
                                    "source": "legacy_sessions"})
                            total_ingested += 1
                            sys.stdout.write(".")
                            sys.stdout.flush()
            except Exception as e:
                print(f"    ⚠️ Error processing sessions: {e}")

    print(
        f"\n\n✅ Migration Complete! Ingested {total_ingested} legacy items into Qdrant.")


if __name__ == "__main__":
    migrate_memory()
