import sys, os, json, logging, time, uuid
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from core.llm import LLMService
from core.vector_store import VectorStore
from qdrant_client.models import PointStruct

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger("ImportLegacyKnowledge")

CONTENT_FIELDS = {"conteudo", "content", "text", "body"}
META_FIELDS = {"id", "conceito", "categoria", "nivel", "linguagem", "dificuldade", "tipo"}
SKIP_KEYS = {"pontuacao_total", "licoes_completadas", "resultados", "nota_media", "acertos", "total_testes", "historico"}

def is_lesson_file(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    if any(k in data for k in SKIP_KEYS):
        return False
    return bool(CONTENT_FIELDS & data.keys())

def extract_text(data: dict) -> str:
    parts = []
    if data.get("conceito"):
        parts.append(f"# {data['conceito']}")
    if data.get("categoria"):
        parts.append(f"Categoria: {data['categoria']}")
    if data.get("nivel"):
        parts.append(f"Nivel: {data['nivel']}")
    if data.get("linguagem"):
        parts.append(f"Linguagem: {data['linguagem']}")
    for field in CONTENT_FIELDS:
        if data.get(field):
            parts.append(data[field])
            break
    return "\n\n".join(parts)

def build_metadata(data: dict) -> dict:
    meta = {"source": "legacy_knowledge"}
    for key in META_FIELDS:
        if key in data:
            meta[key] = data[key]
    return meta

def main():
    knowledge_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ.get("ZIVA_KNOWLEDGE_DIR", r"C:\Users\hollo\AppData\Local\Temp\ziva_knowledge_import\data\knowledge"))
    if not knowledge_dir.exists():
        log.error(f"Directory not found: {knowledge_dir}")
        sys.exit(1)

    llm = LLMService()
    vs = VectorStore()

    points = []
    skipped = 0

    for json_path in sorted(knowledge_dir.rglob("*.json")):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Failed to parse {json_path.name}: {e}")
            skipped += 1
            continue

        if not is_lesson_file(data):
            skipped += 1
            continue

        text = extract_text(data)
        if len(text) < 20:
            skipped += 1
            continue

        emb = llm.embedding(text)
        if not emb:
            log.warning(f"Embedding failed for {json_path.name}")
            skipped += 1
            continue

        point_id = str(uuid.uuid4())
        payload = {"text": text, "timestamp": time.time()}
        payload.update(build_metadata(data))

        points.append(PointStruct(id=point_id, vector=emb, payload=payload))
        log.info(f"  {json_path.name} -> {data.get('conceito', '?')[:50]}")

    if points:
        vs.client.upsert(collection_name=vs.collection_name, points=points)
        log.info(f"\nImported {len(points)} knowledge items into '{vs.collection_name}' ({skipped} skipped)")
    else:
        log.info(f"No knowledge items found to import ({skipped} skipped)")

if __name__ == "__main__":
    main()
