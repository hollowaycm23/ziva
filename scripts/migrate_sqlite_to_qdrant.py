"""
Migrate all interactions and sessions from SQLite (ziva.db) to Qdrant vector store for RAG.
"""
import sys, os, time, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from core.database import DatabaseManager
from core.vector_store import VectorStore
from core.llm import LLMService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MigrateSQLite2Qdrant")

BATCH_SIZE = 50

def get_all_data(db):
    conn = db._get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.session_id, i.role, i.content, i.timestamp, i.importance, i.tags
        FROM interactions i
        ORDER BY i.id ASC
    """)
    interactions = cursor.fetchall()
    cursor.execute("""
        SELECT s.id, s.start_time, s.end_time, s.summary, s.status
        FROM sessions s
        ORDER BY s.id ASC
    """)
    sessions = cursor.fetchall()
    conn.close()
    return interactions, sessions

def migrate():
    logger.info("=" * 60)
    logger.info("INICIANDO MIGRAÇÃO SQLite -> Qdrant")
    logger.info("=" * 60)

    db = DatabaseManager()
    vs = VectorStore()
    llm = LLMService()

    logger.info(f"Qdrant: {vs.client._grpc_options[0] if hasattr(vs, '_grpc_options') else 'localhost'}/{vs.collection_name}")
    logger.info(f"Embedding model: {llm.embedding_model}")
    logger.info(f"Vector size: {os.getenv('QDRANT_VECTOR_SIZE', '768')}")

    interactions, sessions = get_all_data(db)
    logger.info(f"Interactions encontradas: {len(interactions)}")
    logger.info(f"Sessions encontradas: {len(sessions)}")
    sessions_dict = {s[0]: s for s in sessions}

    total_added = 0
    total_skipped = 0
    total_errors = 0

    # Process sessions as summaries
    logger.info("\n--- SESSIONS (sumários) ---")
    for s in sessions:
        sid, start, end, summary, status = s
        if not summary or len(summary.strip()) < 10:
            continue
        text = f"[Session {sid}] Summary: {summary}"
        metadata = {
            "source": "session_summary",
            "session_id": sid,
            "type": "conversation_summary",
            "status": status or "unknown",
            "timestamp": start or time.time()
        }
        try:
            emb = llm.embedding(text)
            if emb and len(emb) > 0:
                result = vs.add_text(text, emb, metadata)
                if result:
                    total_added += 1
                else:
                    total_skipped += 1
        except Exception as e:
            total_errors += 1
            logger.error(f"Session {sid}: {e}")

        if (total_added + total_skipped + total_errors) % 20 == 0:
            logger.info(f"  Progresso: +{total_added} | skip {total_skipped} | err {total_errors}")

    # Process interactions
    logger.info("\n--- INTERACTIONS ---")
    batch_texts = []
    batch_embs = []
    batch_metas = []

    for i, row in enumerate(interactions):
        iid, sid, role, content, ts, importance, tags = row
        if not content or len(content.strip()) < 5:
            total_skipped += 1
            continue

        text = content.strip()
        metadata = {
            "source": "interaction",
            "role": role or "unknown",
            "session_id": sid,
            "interaction_id": iid,
            "type": "conversation",
            "timestamp": ts or time.time()
        }
        if importance:
            metadata["importance"] = importance
        if tags:
            metadata["tags"] = tags

        try:
            emb = llm.embedding(text)
            if not emb or len(emb) == 0:
                total_errors += 1
                continue

            batch_texts.append(text)
            batch_embs.append(emb)
            batch_metas.append(metadata)

            if len(batch_texts) >= BATCH_SIZE:
                ids = vs.add_texts(batch_texts, batch_embs, batch_metas)
                total_added += len([x for x in ids if x])
                batch_texts = []
                batch_embs = []
                batch_metas = []
                logger.info(f"  Lote inserido. Total: {total_added} | skip {total_skipped} | err {total_errors}")

        except Exception as e:
            total_errors += 1
            logger.error(f"Interaction {iid}: {e}")

    # Flush remaining batch
    if batch_texts:
        ids = vs.add_texts(batch_texts, batch_embs, batch_metas)
        total_added += len([x for x in ids if x])

    # Stats
    stats = vs.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("MIGRAÇÃO CONCLUÍDA")
    logger.info(f"  Adicionados: {total_added}")
    logger.info(f"  Ignorados (duplicados/vazios): {total_skipped}")
    logger.info(f"  Erros: {total_errors}")
    logger.info(f"  Total no Qdrant: {stats}")
    logger.info("=" * 60)

    return total_added > 0

if __name__ == "__main__":
    migrate()
